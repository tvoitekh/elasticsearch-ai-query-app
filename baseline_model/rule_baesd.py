import re
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.translate.bleu_score import corpus_bleu

def extract_product_info(sentence):
    # Enhanced regex to capture product names more accurately
    name_match = re.search(r'(?:Do you have|Is there any|I\'m interested in buying|I would like to get|Can you find me|I wish to buy|I\'m looking to buy)\s+(a |an )?(.+?)(?: that is| which is| with|,| for| -|$)', sentence)
    product_name = name_match.group(2) if name_match else "Not found"
    
    # Enhanced regex for price extraction
    price_match = re.search(r'(\$\d+(?:\.\d+)?|Rs\s*\d+(?:\.\d+)?)', sentence)
    price = price_match.group(0) if price_match else "Price not mentioned"

    # Formatting the output as a string with product name and price
    return f"product name: {product_name}, price: {price}"

data = pd.read_csv('test_data.csv')

# Apply the function to extract information
data['formatted_info'] = data['input'].apply(lambda x: extract_product_info(x))

# Preprocess text data for BLEU score computation
references = [word_tokenize(str(x).lower()) for x in data['output']]
candidates = [word_tokenize(str(x).lower()) for x in data['formatted_info']]

# Calculate BLEU score
bleu_score = corpus_bleu([[ref] for ref in references], candidates)
print(f"BLEU Score: {bleu_score}")
