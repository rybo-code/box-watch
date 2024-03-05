import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from tqdm import tqdm
import geojson
import random
from pathlib import Path

import logging

logging.basicConfig(level=logging.INFO)


def geocode_location(location_name, store_place_details):
    """"""
    try:
        # Geocode the place name
        geolocator = Nominatim(user_agent="geo_coder", timeout=5)
        location = geolocator.geocode(location_name)

        if location:
            if store_place_details == True:
                # Store the geocoded location+details
                location_details = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "place_type": location.raw.get("type", None),
                    "class_type": location.raw.get("class", None),
                }
            else:
                location_details = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }

        else:
            # If location is not found, store None
            location_details = None

    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logging.info("Geocoding service failed to return for:", location_name)
        logging.warn(e)
        location_details = None

    return location_details


def geocode_place_names(json_file, store_place_details=False):
    # Load the JSON file
    with open(json_file, "r") as f:
        data = json.load(f)

    # Iterate over each place name in the JSON file
    for key in data:
        named_entities = data[key]["named_geo_entities"]
        entity_coords_dict = dict()
        for entity_name in tqdm(named_entities):
            # Only query nominatim if we don't already know the location
            if entity_name in entity_coords_dict.keys():
                coords = entity_coords_dict[entity_name]
            else:
                logging.info(f"Geocoding: {entity_name}")
                geocode_details = geocode_location(entity_name, store_place_details)

                if geocode_details:
                    entity_coords_dict[entity_name] = geocode_details
                else:
                    logging.warning(f"No geocode found for {entity_name}.")
                    # print(data[key]['named_geo_entities'])
                    logging.info(f"Removing {entity_name}")
                    # Remove the un-geocoded place from the data
                    data[key]["named_geo_entities"].remove(entity_name)
            # print(entity_name)
            # print(coords)

        data[key]["named_geo_entities"] = entity_coords_dict

    return data


def convert_to_geojson(json_data):
    feature_collections = []
    for key, entry in json_data.items():
        features = []
        for location, details in entry["named_geo_entities"].items():
            latitude = details["latitude"]
            longitude = details["longitude"]
            point = geojson.Point((longitude, latitude))
            properties = {
                "title": entry["title"],
                "link": entry["link"],
                "published": entry["published"],
                "summary": entry["summary"],
                "marker-color": details["marker-color"],
                "location": location,  # Include the name of the location as a property
            }
            feature = geojson.Feature(geometry=point, properties=properties)
            features.append(feature)
        feature_collections.append(geojson.FeatureCollection(features))

    # Merge features into single
    merged_features = []

    for feature_collection in feature_collections:
        merged_features.extend(feature_collection["features"])
        merged_feature_collection = geojson.FeatureCollection(merged_features)

    return merged_feature_collection


def generate_random_colors(num_colors):
    """Literal chatGPT copypasta"""
    colors = []
    for _ in range(num_colors):
        colors.append(
            "#{:06x}".format(random.randint(0, 0xFFFFFF))
        )  # Generate a random hex color
    return colors


def add_colors_to_json(json_data):

    num_articles = len(json_data)
    colors = generate_random_colors(num_articles)

    for article_id in json_data:
        color = colors.pop()
        for place in json_data[article_id]["named_geo_entities"]:
            json_data[article_id]["named_geo_entities"][place]["marker-color"] = color

    return json_data


def main():

    # Open the news stories JSON
    file_path = Path("news_stories/2024-03-05_news_entries.json")

    geocoded_json = geocode_place_names(file_path)
    geocoded_json_colored = add_colors_to_json(geocoded_json)
    geojson_data = convert_to_geojson(geocoded_json_colored)

    # Extract the filename without extension
    new_filename = "./geojson/" + file_path.stem + "_geocoded.json"

    with open(new_filename, "w") as f:
        json.dump(geojson_data, f, indent=4)


if __name__ == "__main__":
    main()
