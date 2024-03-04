import feedparser
from datetime import datetime
import string as string_module
import spacy

# from geotext import GeoText
from bs4 import BeautifulSoup
import requests
import json
from tqdm import tqdm
import re
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


import string as string_module


def clean_sentences(text_sentences: list):
    """
    Splits sentences into words, removes punctuation, scans for multi-word nouns
    We are defining nouns as capitalised words other than the first word in a sentence.
    This is a simplification but applicable for professional publications such as news articles.
    """
    translator = str.maketrans("", "", string_module.punctuation)
    clean_sentences = [s.translate(translator).strip() for s in text_sentences]
    bag_of_words = list()

    # Search for multi-word nouns
    multi_word_noun_pattern = r"\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)+\b"

    for s in clean_sentences:
        multi_word_nouns = re.findall(multi_word_noun_pattern, s)
        # Remove the multi word nouns from our sentence
        left_over_words = re.sub(multi_word_noun_pattern, "", s).strip()
        # Find any other capitalised words ie. nouns
        other_nouns = re.findall(r"\b[A-Z][a-z]*\b", left_over_words)

        words = multi_word_nouns + other_nouns
        bag_of_words += words

    return bag_of_words


def get_named_geographies(text_sentences: list, cities_ref_set, countries_ref_set):
    """Requires sentences so we can decide what to do with the first word of a sentence being capitalised in English"""
    named_cities = list()
    named_countries = list()
    words = clean_sentences(text_sentences)

    for word in words:
        if word.istitle():
            # Double check if the word is capitalised
            logging.info(f"checking word:{word}")
            if word in countries_ref_set:
                named_countries.append(word)
                logging.info(f"Country found: {word}")

            elif word in cities_ref_set:
                named_cities.append(word)
                logging.info(f"City found: {word}")

    # TODO Add a filter for cities, only return if we find another more than one city from the same country,
    # or mention the country

    return named_cities, named_countries


def get_named_geographies_spacy(text_sentences: list):
    """NLP extract GeoPoliticalEntities(GPE) or Locations(LOC) from text sentences"""
    text = " ".join(text_sentences)
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)

    # Extract named entities labeled as geopolitical entities or locations
    geographical_places = [
        word.text for word in doc.ents if word.label_ in ["GPE", "LOC"]
    ]

    return geographical_places


def save_to_json(entries: list, filename):
    """Takes list of dicts, formats and saves"""

    pattern = r"\d+$"  # Takes end digits only
    json_format_entries = {}

    # Extract keys from BBC URLs and create dictionary entries
    # TODO Generalise method for other RSS news feeds
    for item in entries:
        match = re.search(pattern, item["link"])
        if match:
            key = match.group()
            json_format_entries[key] = item

    with open(filename, "w") as f:
        json.dump(json_format_entries, f, indent=4)


def main():

    # cities_ref_set, countries_ref_set = get_geonames_cache()
    # URL of the BBC News RSS feed you want to fetch
    bbc_world_news_rss_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    desired_date = datetime.now().date()

    logging.info("Fetching RSS feed content")

    bbc_world_news_entries = fetch_bbc_news_rss(
        bbc_world_news_rss_url, desired_date, limit=20
    )

    for entry in tqdm(bbc_world_news_entries):

        logging.info(f"Title:, {entry['title']}")
        logging.info(f"Link:, {entry['link']}")

        article_sentences = extract_article_text(entry["link"])
        # print(article_sentences)

        named_geo_entities = get_named_geographies_spacy(article_sentences)

        entry["named_geo_entities"] = sorted(list(set(named_geo_entities)))

        logging.info(f"Named Entities: {named_geo_entities}")

    save_to_json(
        bbc_world_news_entries,
        f"./news_stories/{desired_date.strftime('%Y-%m-%d')}_news_entries.json",
    )


if __name__ == "__main__":
    main()
