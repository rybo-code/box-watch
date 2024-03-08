# box-watch

1. Download the day's news articles from BBC world news
2. Extract the mentioned geographical locations in each article
3. Geocode the locations to a coordinate
4. [INCOMPLETE] Extract the latest satellite image of the locations from Senitnel Satellite imagery

### Usage
Run from Github action:


Run locally:
'docker build -t box-watch .'
'docker run box-watch python ./src/check_news_stories.py -o ./data.json'
'docker run box-watch python ./src/geolocate_names.py -i ./data.json -o ./data_geocoded.json 

### Description


Because sentinel-hub has a free acess limit of 30 days, we directly use the AWS S3 bucket containing open source sentinel imagery.

### Links

