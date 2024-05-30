import subprocess
from tqdm import tqdm

config = {"key_person": "O_Bondarenko_2",
          "results_dir": "./data/apify/appliances/"}
# 'blenders':"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289914&dc&fs=true&ds=v1%3AoNMXerEibQbAt6zMkxy1RLEyZLGjPbb52QsB9z86ITk&qid=1714059312&rnid=2619525011&ref=sr_nr_n_3",
category2link = {
 "Indoor Grills & Griddles" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289919&dc&fs=true&ds=v1%3Av764CqJhAZAQP7uRxqITAd7Qn2FDSrXmbBe6tj37ObE&qid=1714059312&rnid=2619525011&ref=sr_nr_n_17",
 "Juicers" : "https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289926&dc&fs=true&ds=v1%3ATulfLPO8g0XiIDoxg6IoMSm85GMqNvGlpthvE6zrcdU&qid=1714059312&rnid=2619525011&ref=sr_nr_n_18",
 "Kegerators" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A2686378011&dc&fs=true&ds=v1%3AbWdAtOp56oqrCeYu43hVovN3q0hzUQsFCmDF1lllj%2Fk&qid=1714059312&rnid=2619525011&ref=sr_nr_n_19",
 "Microwave Ovens" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289935&dc&fs=true&ds=v1%3ArVylE7z81B2vJ0SXbLN5TPddsKHyM2zDhvBaO8JULAE&qid=1714059312&rnid=2619525011&ref=sr_nr_n_20",
 "Household Mixers" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289929&dc&fs=true&ds=v1%3AgdqmOzit8UrHIGEty4wOPX5Bck6JnDCZk2CSNv6ffWw&qid=1714059312&rnid=2619525011&ref=sr_nr_n_21",
 "Ovens & Toasters" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289933&dc&fs=true&ds=v1%3A9ivL%2FrHM623SDKf4z3JYokXbDNMTq2CZ%2FYziBAWyTz4&qid=1714059312&rnid=2619525011&ref=sr_nr_n_22",
 "Rice Cookers": "https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A678540011&dc&fs=true&ds=v1%3AWfxHzPSkf4gzJN2fItq2ULFfgwpgoKLejvmaFYnrlFQ&qid=1714059312&rnid=2619525011&ref=sr_nr_n_23",
 "Slow Cookers" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289940&dc&fs=true&ds=v1%3Ao1bu5gh6krcWEYp4KoTf%2BpKGV%2FiPjLPGzWI7%2BAhOlIc&qid=1714059312&rnid=2619525011&ref=sr_nr_n_24",
 "Soda Makers" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A7956268011&dc&fs=true&ds=v1%3ArWw7tVXtgBq0LRxUE2bLaLFl0cN1gltPGayoKXFOLOk&qid=1714059312&rnid=2619525011&ref=sr_nr_n_25",
 "Specialty Kitchen Appliances" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289941&dc&fs=true&ds=v1%3A8UCFlO4jXLGvh33v9N8wuEhkiKOS%2FyeXdjmn23%2Bom4c&qid=1714059312&rnid=2619525011&ref=sr_nr_n_26",
 "Food Steamers" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A678541011&dc&fs=true&ds=v1%3A%2BiWREYi0lqZ815SPCdjUSQJtHZS7fpgHajlSw1WQCdU&qid=1714059312&rnid=2619525011&ref=sr_nr_n_27",
 "Waffle Irons" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A289942&dc&fs=true&ds=v1%3A%2BUMyQvlYiy4w1wDVMKZ27U05PkatL%2FLlEUW%2BgyHfWxQ&qid=1714059312&rnid=2619525011&ref=sr_nr_n_28",
 "Wine Cellars" :"https://www.amazon.com/s?i=kitchen&rh=n%3A1055398%2Cn%3A284507%2Cn%3A2619525011%2Cn%3A289913%2Cn%3A3741521&dc&fs=true&ds=v1%3AmgKheESdF85DRfo%2FWshVkUv4qmRk7Fjal62WMGRv4RU&qid=1714059312&rnid=2619525011&ref=sr_nr_n_29",
 }



initial_command_list = ["poetry", "run", "python", "scrape_apify.py"]

for key, value in config.items():
    initial_command_list.append("--" + key)
    initial_command_list.append(value)

for category,link in tqdm(category2link.items()):
    subprocess.run(initial_command_list
                + ["--large_category_name", "appliances"]
                + ["--category_name", category]
                + ["--category_url", link]
                + ["--max_items", '200'])

