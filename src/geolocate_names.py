import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from tqdm import tqdm
import geojson
import random
from pathlib import Path
import matplotlib.pyplot as plt

import logging

logging.basicConfig(level=logging.INFO)


def geocode_location(location_name):
    """
    Geocodes a given location name using the Nominatim geocoding service.

    Parameters:
    - location_name: The name of the location to be geocoded.

    Returns:
    - A dict containing details of the geocoded location latitude, longitude, place type,
    and class type. Returns None if the location cannot be geocoded or if the geocoding
    service fails.
    """
    try:
        # Geocode the place name
        geolocator = Nominatim(user_agent="geo_coder", timeout=5)
        location = geolocator.geocode(location_name)
        valid_class_types = [
            "place",
            "boundary",
        ]  # Open Street Map administrative labels

        if location:
            # Store the geocoded location + details
            location_details = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "place_type": location.raw.get("type", None),
                "class_type": location.raw.get("class", None),
            }
            # Filter for relevant places
            if location_details["class_type"] not in valid_class_types:
                location_details = None
                logging.info(f"Low quality location returned for: {location_name}")

        else:
            # If location is not found, store None
            location_details = None

    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logging.info("Geocoding service failed for:", location_name)
        logging.warn(e)
        location_details = None

    return location_details


def locate_place_names(json_file):
    # Load the JSON file
    with open(json_file, "r") as f:
        data = json.load(f)

    # Iterate over each place name in the JSON file
    entity_coords_dict = dict()

    for key in data:
        named_entities = data[key]["named_geo_entities"]
        for entity_name in tqdm(named_entities):
            logging.info(f"Locating {entity_name}.")
            # Only query nominatim if we don't already know the location
            if entity_name in entity_coords_dict.keys():
                logging.info(f"{entity_name} already located.")
                geocode_details = entity_coords_dict[entity_name]
            else:
                geocode_details = geocode_location(entity_name)

            if geocode_details is not None:
                entity_coords_dict[entity_name] = geocode_details
            else:
                logging.info(f"No geocode found for {entity_name}.")
                logging.info(f"Removing {entity_name} from places.")
                # Remove the un-geocoded place from the data
                data[key]["named_geo_entities"].remove(entity_name)

        data[key]["named_geo_entities"] = entity_coords_dict

    return data


def convert_to_geojson(json_data):
    feature_collections = []
    colors = generate_random_colors(len(json_data))
    for article_id, entry in json_data.items():
        features = []
        marker_color = colors.pop()  # Color article locations all same
        logging.info(f"Color for {article_id}:{marker_color}")
        for location, details in entry["named_geo_entities"].items():
            latitude = details["latitude"]
            longitude = details["longitude"]
            point = geojson.Point((longitude, latitude))
            properties = {
                "article_id": article_id,
                "title": entry["title"],
                "link": entry["link"],
                "published": entry["published"],
                "summary": entry["summary"],
                "marker-color": marker_color,
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


# def add_colors_to_json(json_data):

#     num_articles = len(json_data)
#     colors = generate_random_colors(num_articles)
#     logging.info(f"Found {num_articles} articles to color with {colors}.")

#     for article_id in tqdm(json_data):
#         color = colors.pop()
#         logging.info(f"Color for {article_id}:{color}")
#         for place in json_data[article_id]["named_geo_entities"]:
#             json_data[article_id]["named_geo_entities"][place]["marker-color"] = color
#     logging.info("Colors applied.")

#     return json_data


def main():

    # Open the news stories JSON
    file_path = Path("news_stories/2024-03-05_news_entries.json")

    geocoded_json = locate_place_names(file_path)
    # geocoded_json_colored = add_colors_to_json(geocoded_json)
    geojson_data = convert_to_geojson(geocoded_json)

    # Extract the filename without extension
    new_filename = "./geojson/" + file_path.stem + "_geocoded.json"

    with open(new_filename, "w") as f:
        json.dump(geojson_data, f, indent=4)


if __name__ == "__main__":
    main()
