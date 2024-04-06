# elasticsearch-filter-query-ai-app
Install the required packages:

pip install -r requirements.txt


Setup and Run Elasticsearch locally in Docker:

docker pull docker pull docker.elastic.co/elasticsearch/elasticsearch:7.10.2

docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.10.2

Use elasticsearch:7.10.2 for compatibility with ARM based Macs (otherwise, there are dedicated versions with -arm64 suffix, e.g. docker.elastic.co/elasticsearch/elasticsearch:8.12.2-arm64) 

