import feedparser
from datetime import datetime
import string as string_module

# from geotext import GeoText
from bs4 import BeautifulSoup
import requests
import json
from tqdm import tqdm

# import pandas as pd
from geonamescache import GeonamesCache
import logging

logging.basicConfig(level=logging.INFO)


def fetch_bbc_news_rss(url, date, limit=None):
    # Parse the RSS feed
    feed = feedparser.parse(url)

    # Extract information from the feed
    entries = []
    for entry in tqdm(feed.entries[:limit]):
        # print(entry.published)
        entry_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
        if entry_date.date() == date:
            entry_info = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "summary": entry.summary,
            }
            entries.append(entry_info)

    return entries


def extract_article_text(url):
    # Fetch the HTML content of the article
    response = requests.get(url)
    response.encoding = "utf-8"
    html_content = response.text

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the element with the ID "main-content"
    main_content = soup.find(id="main-content")

    # Extract the text content from divs labeled as data-component="text-block" inside the main-content
    text_blocks = main_content.find_all(
        "div",
        {"data-component": "text-block"},
    )
    article_sentences = list()
    for text_block in text_blocks:

        text = text_block.get_text()
        article_sentences.append(text)

    return article_sentences


def get_geonames_cache():

    # Initialize the GeoNamesCache
    gc = GeonamesCache()

    cities = gc.get_cities()
    countries = gc.get_countries_by_names()

    cities_set = set({key: value["name"] for key, value in cities.items()}.values())
    countries_set = set(
        {key: value["name"] for key, value in countries.items()}.values()
    )

    return cities_set, countries_set


def get_named_geographies(text_sentences: list, cities_ref_set, countries_ref_set):
    """Requires sentences so we can decide what to do with the first word of a sentence being capitalised in English"""
    named_cities = list()
    named_countries = list()

    # Define the translation table to remove punctuation

    for sentence in tqdm(text_sentences):
        # Remove punctuation using translate method
        translator = str.maketrans("", "", string_module.punctuation)
        clean_sentence = sentence.translate(translator)
        words = clean_sentence.split(" ")
        # print(words)
        for word in words[1:]:
            # Skip first word of sentence
            if word.istitle():
                # Check if the word is capitalised
                logging.info(f"checking word:{word}")
                if word in countries_ref_set:
                    named_countries.append(word)
                    logging.info(f"Country found: {word}")

                elif word in cities_ref_set:
                    named_cities.append(word)
                    logging.info(f"City found: {word}")

    return named_cities, named_countries


def save_to_json(entries, filename):
    with open(filename, "w") as f:
        json.dump(entries, f, indent=4)


def main():

    cities_ref_set, countries_ref_set = get_geonames_cache()
    # URL of the BBC News RSS feed you want to fetch
    bbc_world_news_rss_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    desired_date = datetime.now().date()

    logging.info("Fetching RSS feed content")

    bbc_world_news_entries = fetch_bbc_news_rss(
        bbc_world_news_rss_url, desired_date, limit=10
    )

    for entry in tqdm(bbc_world_news_entries):

        logging.info(f"Title:, {entry['title']}")
        logging.info(f"Link:, {entry['link']}")

        article_sentences = extract_article_text(entry["link"])
        # print(article_sentences)

        named_cities, named_countries = get_named_geographies(
            article_sentences, cities_ref_set, countries_ref_set
        )

        entry["named_cities"] = sorted(list(set(named_cities)))
        entry["named_countries"] = sorted(list(set(named_countries)))

        logging.info(f"Named Cities: {named_cities}")
        logging.info(f"Named Countries: {named_countries}")

        save_to_json(
            bbc_world_news_entries,
            f"./news_stories/{desired_date.strftime('%Y-%m-%d')}_news_entries.json",
        )


if __name__ == "__main__":
    main()
