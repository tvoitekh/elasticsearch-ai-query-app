import openai

from dotenv import load_dotenv

load_dotenv()

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


prompt = f"Extract potential generalized item names from the user request: \"I want to by a kettle for my kitchen\". Items are separated by commas. Items:"

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    temperature=0.0,
    max_tokens=4000,
    messages=[{"role": "user", "content": prompt}],
)

print(response.choices[0])