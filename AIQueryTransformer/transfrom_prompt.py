from constants import (
    BASE_COMPLETION_MODEL,
    CHATGPT_16K_MODEL,
    CHATGPT_MODEL,
    COMPLETION_MODEL,
    EMBEDDINGS_MODEL,
    DEFAULT_MODEL,
    TOKENS_DELTA,
    MAX_TOKENS
)

from elasticsearch import Elasticsearch, exceptions as es_exceptions, ElasticsearchException
import openai
import os
import hashlib
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from dotenv import load_dotenv

load_dotenv()

prompt_file_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'base_prompt.txt')

# Read the prompt file content
with open(prompt_file_path, 'r') as file:
    base_prompt = file.read()
    

class OpenAIDSL:

    CACHE_DIR = os.path.join(os.path.dirname(__file__), '../cache')
    BASE_PROMPT = """
    Given the mapping delimited by triple backticks ```%s``` translate the text delimited by triple quotes in a valid Elasticsearch DSL query \"\"\"%s\"\"\". 
    Give me only the json code part of the answer. Compress the json output removing spaces.
    
    Example:
    
    Example Request 1:
    I am looking for contemporary stainless steel handles for compact coolers that will give my fridge a finished look.

    Desired Elasticsearch DSL Response 1:

    {{
    "query": {{
        "bool": {{
        "must": [
            {{
            "match": {{
                "title": "stainless steel handles"
            }}
            }},
            {{
            "bool": {{
                "should": [
                {{
                    "match": {{
                    "description": "contemporary"
                    }}
                }},
                {{
                    "match": {{
                    "description": "compact coolers"
                    }}
                }},
                {{
                    "match": {{
                    "description": "finished look"
                    }}
                }}
                ]
            }}
            }}
        ]
        }}
    }}
    }}
    
    Example Request 2:
    
    I want to buy an electric stove or a kettle with price less than 2000
    
    Desired Elasticsearch DSL Response 2:
    
    {
  "query": {
    "bool": {
      "must": [
        {
          "bool": {
            "should": [
              { "match": { "name": "electric stove" } },
              { "match": { "name": "kettle" } }
            ]
          }
        },
        {
          "range": {
            "actual_price": {
              "lt": 2000
            }
          }
        }
      ]
    }
  }
}
    
    Example Request 3:
    I want to buy refrigerator, dishwasher, microwave, blender
    
    Desired Elasticsearch DSL Response 3:
    {
  "query": {
    "bool": {
      "must": [
        {
          "bool": {
            "should": [
              { "match": { "name": "refrigerator" } },
              { "match": { "name": "dishwasher" } },
              { "match": { "name": "microwave" } },
              { "match": { "name": "blender" } }
            ]
          }
        }
      ]
    }
  }
}
"""

    def __init__(
        self,
        completion_model=COMPLETION_MODEL,
        embeddings_model=EMBEDDINGS_MODEL,
        model=CHATGPT_16K_MODEL,
        tokens_delta=TOKENS_DELTA,
        es_client=Elasticsearch([{'host': 'localhost', 'port': 9200}]),
    ):
        self.model = model
        self.completion_model = completion_model
        self.embeddings_model = embeddings_model
        self.tokens_delta = tokens_delta
        self.max_tokens = MAX_TOKENS[self.model]
        self.es_client = es_client
        self.cache_dir = self.CACHE_DIR
        self.base_prompt = self.BASE_PROMPT

    def get_mapping(self, index):
        try:
            result = self.es_client.indices.get_mapping(index)
            mapping = str(result)
            self.set_cache_mapping(index, mapping)
            return mapping
        except es_exceptions.ElasticsearchException as e:
            raise e

    def extract_items_from_request(self, request):
        prompt = f"""
        You are a helpful assistant, and your main job is to suggest customers a list of products or categories based on their needs.
        Please output only the list of products (and prices only if desired prices are specified by the user).
        Do not include any additional information, explanations, or polite phrases.
        Format your response as a comma-separated list of product:price pairs if prices are specified.
        Example: electric kettle:30, stove:100, kitchen knife:15

        The user request is as follows: "{request}"
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                temperature=0.0,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            items = response['choices'][0]['message']['content']
            items = [item.strip() for item in items.split(',')]
            
            products_and_prices = []
            for item in items:
                if ':' in item:
                    product, price = item.split(':')
                    products_and_prices.append({'product': product.strip(), 'price': price.strip()})
                else:
                    products_and_prices.append({'product': item.strip(), 'price': None})

            return products_and_prices

        except openai.OpenAIError as e:
            raise e

    def assess_clarity_of_request(self, request):
        prompt = f"""
        You are an assistant that determines whether a user's request for product suggestions is clear or ambiguous. 
        If the request mentions particular products and/or prices without any ambiguous phrases, such as "most common kitchen appliances", respond with "clear". If the request is ambiguous or unclear, respond with "unclear".
        
        Example 1:
        
        I want to buy refrigerator, dishwasher, microwave, blender
        
        Expected response:
        
        "clear"
        
        Example 2:
        
        give me 4 most common kitchen applicances
        
        Expected response:
        
        "unclear"
        
        
        

        The user request is as follows: "{request}"
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                temperature=0.0,
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}],
            )

            clarity = response['choices'][0]['message']['content'].strip().lower()
            return clarity

        except openai.OpenAIError as e:
            raise e

    def search(self, index, prompt, cache=True):
        query = None
        if cache:
            query = self.get_cache_prompt(prompt)
        if query is None:
            mapping = self.get_cache_mapping(index) if cache else None
            if mapping is None:
                mapping = self.get_mapping(index)
            query = self.chat_gpt(prompt, mapping)
        self.last_query = query
        return self.es_client.search(index=index, body=query)

    def get_products_from_query(self, index_name, dsl_query):
        try:
            search_results = self.es_client.search(
                index=index_name, body=dsl_query)

            products = []
            hits = search_results["hits"]["hits"]
            for hit in hits:
                products.append(hit["_source"])

            return products

        except es_exceptions.ElasticsearchException as e:
            raise e

    def chat_gpt(self, prompt, mapping):
        prompt = self.base_prompt % (mapping.strip(), prompt.strip())
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                temperature=0.0,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            answer = response.choices[0]['message']['content']
            if answer:
                self.set_cache_prompt(prompt, answer)
                return answer
            else:
                raise ValueError(
                    "OpenAI GPT did not produce a valid Elasticsearch DSL query.")
        except openai.OpenAIError as e:
            raise e

    def get_cache_mapping(self, index):
        filename = os.path.join(self.cache_dir, f"{index}.json")
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                return file.read()
        return None

    def set_cache_mapping(self, index, mapping):
        filename = os.path.join(self.cache_dir, f"{index}.json")
        with open(filename, 'w') as file:
            file.write(mapping)

    def get_cache_prompt(self, prompt):
        filename = os.path.join(
            self.cache_dir, f"{hashlib.md5(prompt.encode()).hexdigest()}.json")
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                return file.read()
        return None

    def set_cache_prompt(self, prompt, query):
        filename = os.path.join(
            self.cache_dir, f"{hashlib.md5(prompt.encode()).hexdigest()}.json")
        with open(filename, 'w') as file:
            file.write(query)

    def delete_cache_prompt(self, prompt):
        filename = os.path.join(
            self.cache_dir, f"{hashlib.md5(prompt.encode()).hexdigest()}.json")
        if os.path.exists(filename):
            os.remove(filename)


if __name__ == "__main__":
    openai_dsl = OpenAIDSL(
        completion_model=COMPLETION_MODEL,
        embeddings_model=EMBEDDINGS_MODEL,
        model=CHATGPT_16K_MODEL,
        tokens_delta=TOKENS_DELTA,
    )

    mapping = openai_dsl.get_mapping('amazon-products-index')
    print(mapping)
    prompt = 'I want to buy an oven with a price less than 2000'
    
    # Assess clarity of the initial request
    clarity = openai_dsl.assess_clarity_of_request(prompt)
    
    if clarity == "unclear":
        # Extract relevant items
        extracted_items = openai_dsl.extract_items_from_request(prompt)
        prediction_items = []
        for item in extracted_items:
            if item['price']:
                prediction_items.append(f"product name: {item['product']}, price: {item['price']}")
            else:
                prediction_items.append(f"product name: {item['product']}")
        
        items = ', '.join(prediction_items)
        print(items)
        
        # Construct a detailed prompt using the extracted items
        detailed_prompt = f"I want to buy {items}"
        
        print(detailed_prompt)
        
        # Generate Elasticsearch DSL query
        query = openai_dsl.chat_gpt(detailed_prompt, mapping)
    else:
        # Generate Elasticsearch DSL query directly from the original prompt
        query = openai_dsl.chat_gpt(prompt, mapping)
    
    print(query)
    
    # Perform the search
    search_res = openai_dsl.search('amazon-products-index', prompt)
    print(search_res)
