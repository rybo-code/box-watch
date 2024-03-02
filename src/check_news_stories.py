import feedparser
from datetime import datetime
from geotext import GeoText
from bs4 import BeautifulSoup
import requests
import json


def fetch_bbc_news_rss(url, date, limit):
    # Parse the RSS feed
    feed = feedparser.parse(url)

    # Extract information from the feed
    entries = []
    for entry in feed.entries[:limit]:
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
    text_blocks = main_content.find_all("div", {"data-component": "text-block"})

    # Extract text from each text block and concatenate with a line break
    article_text = "\n".join(
        text_block.get_text(separator=" ", strip=True) for text_block in text_blocks
    )

    return article_text


def save_to_json(entries, filename):
    with open(filename, "w") as f:
        json.dump(entries, f, indent=4)


def main():

    # URL of the BBC News RSS feed you want to fetch
    bbc_world_news_rss_url = "http://feeds.bbci.co.uk/news/world/rss.xml"

    # BBC RSS feed focused on latest articles, not an archive
    desired_date = datetime.now().date()
    # desired_date = datetime(year=2024, month=2, day=1).date()

    # Fetch and parse the RSS feed for the desired date
    bbc_world_news_entries = fetch_bbc_news_rss(
        bbc_world_news_rss_url, desired_date, limit=2
    )

    named_cities = set()
    named_countries = set()

    # Display the title and link of each news article
    for entry in bbc_world_news_entries:
        # print("Title:", entry['title'])
        # print("Link:", entry['link'])
        article_text = extract_article_text(entry["link"])
        article_geotext = GeoText(article_text)
        cities = article_geotext.cities
        countries = article_geotext.countries
        named_countries.update(countries)
        named_cities.update(cities)

    save_to_json(
        bbc_world_news_entries,
        f"./news_stories/{desired_date.strftime('%Y-%m-%d')}_news_entries.json",
    )
    print(f"Named Cities: {named_cities}")
    print(f"Named Countries: {named_countries}")


if __name__ == "__main__":
    main()
