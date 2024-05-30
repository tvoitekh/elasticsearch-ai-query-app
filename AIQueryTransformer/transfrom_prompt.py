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


class OpenAIDSL:

    CACHE_DIR = os.path.join(os.path.dirname(__file__), '../cache')
    BASE_PROMPT = """
    Given the mapping delimited by triple backticks ```%s``` translate the text delimited by triple quotes in a valid Elasticsearch DSL query \"\"\"%s\"\"\". 
    Give me only the json code part of the answer. Compress the json output removing spaces.
    
    Example:
    
    User request:
    
    I want to buy an electric stove or a kettle with price less than 2000
    
    Your response:
    
    "query": {
    "bool": {
        "must": [
        {
            "range": {
            "actual_price": {
                "lt": 2000
            }
            }
        },
        {
            "bool": {
            "should": [
                {
                "match": {
                    "name": "electric stove"
                }
                },
                {
                "match": {
                    "name": "electric kettle"
                }
                }
            ]
            }
        }
        ]
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
        prompt = f"You are a helpful assistant, and your main job is to suggest customers a list of products or categories based on their needs. You need to be concise and professional in your response. The user request is as follows: \"{request}\"."

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                temperature=0.0,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            items = response['choices'][0]['message']['content']
            items = [item.strip() for item in items.split(',')]
            return items

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
    prompt = 'provide me 4 most common items for kitchen'
    
    # Extract relevant items
    items = openai_dsl.extract_items_from_request(prompt)
    print(f"Extracted items: {items}")
    
    # Construct a detailed prompt using the extracted items
    detailed_prompt = f"I want to buy {', '.join(items)}"
    
    # Generate Elasticsearch DSL query
    query = openai_dsl.chat_gpt(detailed_prompt, mapping)
    print(query)
    
    # Perform the search
    search_res = openai_dsl.search('amazon-products-index', detailed_prompt)
    print(search_res)
