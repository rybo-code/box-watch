import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from tqdm import tqdm
import geojson
import random
from pathlib import Path
import argparse

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

    if len(data) > 0:
        pass
    else:
        logging.warning(f"No data found in {json_file}")
        return None
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

    if len(feature_collections) > 0:

        # Merge features into single
        merged_features = []

        for feature_collection in feature_collections:
            merged_features.extend(feature_collection["features"])
            merged_feature_collection = geojson.FeatureCollection(merged_features)
    else:
        logging.warning("No locations found in data.")
        merged_feature_collection = None

    return merged_feature_collection


def generate_random_colors(num_colors):
    """Literal chatGPT copypasta"""
    colors = []
    for _ in range(num_colors):
        colors.append(
            "#{:06x}".format(random.randint(0, 0xFFFFFF))
        )  # Generate a random hex color
    return colors


def main(args):

    # Open the news stories JSON
    file_path_in = Path(args.input)

    geocoded_json = locate_place_names(file_path_in)
    if geocoded_json:
        geojson_data = convert_to_geojson(geocoded_json)
        if args.output:
            file_path_out = args.output
            if not file_path_out.endswith(".json"):
                file_path_out = file_path_out + ".json"
                # Extract the filename without extension
        else:
            file_path_out = file_path_in.stem + "_geocoded.json"

        with open(file_path_out, "w") as f:
            json.dump(geojson_data, f, indent=4)
    else:
        logging.warning("No data to geocode, please check inputs.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Geolocate places in news stories")
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="JSON file of news articles"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Location to save GeoJSON",
    )
    args = parser.parse_args()

    main(args)
