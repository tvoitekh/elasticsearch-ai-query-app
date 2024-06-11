# elasticsearch-filter-query-ai-app

## Install the required packages
```bash
pip install -r requirements.txt
```

## Downgrade the openai version
```bash
pip install 'openai<1.0.0'
```

## Setup and run Elasticsearch locally in Docker
```bash
docker pull docker pull docker.elastic.co/elasticsearch/elasticsearch:7.10.2
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.10.2
```

## Initialize an index and store the example data in a cluster
Navigate to ```/notebooks``` and run the ```ProdIndexPlayground.ipynb``` notebook

Use ```elasticsearch:7.10.2``` for compatibility with ARM based Macs (otherwise, there are dedicated versions with -arm64 suffix, e.g. ```docker.elastic.co/elasticsearch/elasticsearch:8.12.2-arm64```)

## Navigate to the script directory
```bash
cd AIQueryTransformer
```

## Execute the script to obtain the response
```bash
python transform_prompt.py
```
## Evaluate the solution on test data
```bash
python test_data.py
```

