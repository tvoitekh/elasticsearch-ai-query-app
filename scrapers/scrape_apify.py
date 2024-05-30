import os
import json
import argparse
from pathlib import Path
import pandas as pd
from apify_client import ApifyClient
import logging
# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    Path("logs", "scrape_apify.log"),
    mode="a",
)
formatter = logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
# Constants
MAX_ITEMS = 100


def save_actor_call(actor_call, filename):
    jsonified = pd.Series(actor_call).to_json()
    with open(filename, 'w') as f:
        f.write(jsonified)


def get_dataframe_from_call(apify_client, actor_call=None, dataset_id=None):
    items = []
    if actor_call is None and dataset_id is None:
        raise ValueError("Either actor_call or dataset_id should be provided")
    if dataset_id is None:
        dataset_id = actor_call["defaultDatasetId"]
    for item in apify_client.dataset(dataset_id).iterate_items():
        items.append(item)
    return pd.DataFrame(items)


def get_category_df(apify_client,
                    category_url,
                    results_dir,
                    large_category_name,
                    category_name,
                    max_items=MAX_ITEMS):
    # Prepare the Actor input
    run_input = {
        "categoryUrls": [{ "url": category_url}],
        "maxItemsPerStartUrl": max_items,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }
    actor_call = apify_client.actor("junglee/amazon-crawler")\
        .call(run_input=run_input)
    if actor_call["status"] == "FAILED":
        raise Exception(actor_call["statusMessage"])
    actor_call_filepath = os.path.join(results_dir,
                                       "actor_calls",
                                       large_category_name,
                                       category_name+".json")
    Path(actor_call_filepath).parent.mkdir(parents=True, exist_ok=True)
    save_actor_call(actor_call, actor_call_filepath)
    df = get_dataframe_from_call(apify_client, actor_call)
    df_filepath = os.path.join(results_dir,
                               "dataframes",
                               large_category_name,
                               category_name+".parquet")
    Path(df_filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(df_filepath)


def main(args):
    with open("./apify_keys.json", "r") as f:
        apify_keys = json.load(f)
    apify_client = ApifyClient(apify_keys[args.key_person])
    get_category_df(apify_client,
                    args.category_url,
                    results_dir=args.results_dir,
                    large_category_name=args.large_category_name,
                    category_name=args.category_name,
                    max_items=args.max_items)
    # example:
    # get_category_df(apify_client,
    #             "https://www.amazon.com/s?k=Kitchen+%26+Dining+Room+Chairs&i=garden&rh=n%3A3733821&c=ts&qid=1714124170&ts_id=3733821&ref=sr_pg_1",
    #             results_dir="./data/apify/",
    #             large_category_name="kitchen",
    #             category_name="Dining Room Sets")
    

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Scraping apify')
    parser.add_argument('--key_person', type=str)
    parser.add_argument('--category_url', type=str)
    parser.add_argument('--results_dir', type=str)
    parser.add_argument('--large_category_name', type=str)
    parser.add_argument('--category_name', type=str)
    parser.add_argument('--max_items', type=int, default=MAX_ITEMS)
    args = parser.parse_args()
    print(args)
    main(args)