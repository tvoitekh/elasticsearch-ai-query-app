import subprocess
# example directory - "./data/apify/decor/",
# example number of items - 100 (for different sub-smallest categories may vary - 100-200-300)
# the config for the key person looks like this
# {
#  "PERSON_NAME":" "SCRAPER_KEY"   
# }

config = {"key_person": "INSERT_YOUR_KEY",
          "results_dir": "./data/apify/decor/",
          "max_items": '100'}

initial_command_list = ["poetry", "run", "python", "scrape_apify.py"]

for key, value in config.items():
    initial_command_list.append("--" + key)
    initial_command_list.append(value)
category_configs = [
{
    "large_category_name": "lighting",
    "category_name": "Lamps, Bases & Shades",
    "category_url": "https://www.amazon.com/s?k=Lamps%2C+Bases+%26+Shades&i=tools&rh=n%3A3736561&page=1&c=ts&qid=1714147332&ts_id=3736561&ref=sr_pg_2"
},
{
    "large_category_name": "lighting",
    "category_name": "Novelty Lighting",
    "category_url": "https://www.amazon.com/s?k=Novelty+Lighting&i=tools&rh=n%3A3736531&page=1&c=ts&qid=1714147745&ts_id=3736531&ref=sr_pg_2"
},
{
    "large_category_name": "lighting",
    "category_name": "Wall Light Fixtures",
    "category_url": "https://www.amazon.com/s?k=Wall+Light+Fixtures&i=tools&rh=n%3A5486429011&page=1&c=ts&qid=1714147831&ts_id=5486429011&ref=sr_pg_2"
},
]

for category_config in category_configs:
    subprocess.run(initial_command_list
                + ["--large_category_name", category_config["large_category_name"]]
                + ["--category_name", category_config["category_name"]]
                + ["--category_url", category_config["category_url"]])