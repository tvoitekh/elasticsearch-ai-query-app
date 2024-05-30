# example
poetry run python scrape_apify.py\
    --key_person INSERT_YOUR_KEY_PERSON_NAME \
    --category_url "https://www.amazon.com/s?k=Kitchen+%26+Dining+Room+Chairs&i=garden&rh=n%3A3733821&c=ts&qid=1714124170&ts_id=3733821&ref=sr_pg_1"\
    --results_dir ./data/apify/\
    --large_category_name kitchen\
    --category_name "Dining Room Sets"