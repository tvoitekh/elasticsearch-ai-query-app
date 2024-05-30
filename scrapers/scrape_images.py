import requests
from PIL import Image
import io
import os
import pandas as pd
from tqdm import tqdm
from glob import glob
import concurrent.futures
import logging
from pathlib import Path
from functional import seq

logging.basicConfig(level=logging.INFO,
                    filename='logs/log.txt',
                    filemode='a+',
                    format='%(asctime)s - %(levelname)s - %(message)s')
MAX_WORKERS = 20

# Download an image from a URL and save it to a file

def download_image(url, path):
    try:
        response = requests.get(url)
        img = Image.open(io.BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(path)
        return "success"
    except Exception as e:
        logging.info("Error downloading image: {}".format(e))
        return None

def download_image_from_amz_record(row, pathdir):
    # row = id_row_tuple[1]
    url = row["image_url"]
    asin_id = row["asin"]
    flattened_index = row["flattened_index"]
    log_id = f"{asin_id}_{flattened_index}"
    # path = f"./data/thumbnails/{asin_id}/{flattened_index}.jpg"
    filepath = os.path.join(pathdir, asin_id, f"{flattened_index}.jpg")
    Path(filepath).parent.mkdir(exist_ok=True, parents=True)
    status = download_image(url, filepath)
    if status != "success":
        logging.info("Failed to download image for {}".format(log_id))
        return [log_id, "failure"]
    return [log_id, filepath]


if __name__=="__main__":
    df = pd.DataFrame()
    for filepath in tqdm(glob("./data/apify/*/*/*/*.parquet")):
        df = pd.concat([df, pd.read_parquet(filepath)])
    # preprocessing
    # dropping duplicates by id
    df.drop_duplicates(subset=["asin"], inplace=True)
    pathdir = "./data/thumbnails"
    # pathdir = "./data/images"
    images_column_name = "galleryThumbnails"
    # images_column_name = "highResolutionImages"
    
    # filter out already scraped ids
    already_scraped_ids = seq([*Path(pathdir).glob("*")])\
        .map(lambda x: x.name).to_list()
    df = df[~df["asin"].isin(already_scraped_ids)]
    # preprocessing to get the image urls in a flattened format
    df_images_flattened = df[["asin", images_column_name]]\
        .explode(images_column_name)\
        .reset_index()\
        .drop(columns=["index"])
    # as an analogical way of row_number() in SQL
    df_images_flattened["flattened_index"] = df_images_flattened\
        .groupby("asin")\
        .cumcount()
    df_images_flattened.rename(
        columns={images_column_name: "image_url"},
        inplace=True)
    df_images_flattened.dropna()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(
            executor.map(lambda _id_row_tuple:
                         download_image_from_amz_record(_id_row_tuple[1],
                                                        pathdir),
                         df_images_flattened.iterrows()),
                         total=len(df_images_flattened)))
    
