from pystac_client import Client
import rioxarray
import logging
from tqdm import tqdm
import os
import argparse
from geopy import Point, distance


# Ignore lack of georeference for image thumbnails
logging.basicConfig(level=logging.INFO)


def search_elemnt84_stac(bbox, datetime, collections=["sentinel-2-l2a"]):
    """
    Identify the sentinel image file to download from AWS using the Element 84 STAC database

    param :collections: List of satellite imagery STACs to look for. Use "sentinel-2-l2a" or "sentinel-s1-l1c"
    param :datetime: string, list or tuple containing datetime or a daterange eg. "2024-02-21". See pystac docs for full details
    param :bbox: List of lat/lon coords top-left, bottom-right of bounding box
    """

    client = Client.open("https://earth-search.aws.element84.com/v1")

    # Searching the sentinel-cogs location directly doesn't work
    # client = Client.open('https://sentinel-cogs.s3.us-west-2.amazonaws.com')

    search = client.search(
        max_items=10, collections=collections, bbox=bbox, datetime=datetime
    )

    item_collection = search.item_collection()

    return item_collection


def download_from_aws_s3(item, asset_name, save_dir, file_extension, bbox=None):
    """
    Save the image to a raster.

    param :item: pystac.client item returned from in STAC format
    param :asset_name: String of Sentinel asset type eg. TCI (True Color Image). See sentinel docs for full list.
    param :save_dir: Directory to save the images to
    param :file_extension: String of file format for image to download, can be "tiff" or "jpg"
    """
    # TODO Add comments etc

    asset_name = asset_name.lower()

    if file_extension == "jp2":
        image_path_s3 = item.assets[asset_name + "-" + file_extension].href
        # NOTE jp2 files are currently restricted for public download
    else:
        image_path_s3 = item.assets[asset_name].href
    image_obj = rioxarray.open_rasterio(image_path_s3)
    logging.info(f"Filesize: {image_obj.nbytes/1024/1024:.2f}MB")

    # Get file extension from path eg .jpg, check it is correct
    href_filetype = os.path.splitext(image_path_s3)[-1]
    assert href_filetype == "." + file_extension

    # Use Sentinel data structured name (item.id) for image
    file_name = item.id + "-" + asset_name + href_filetype
    file_path = save_dir + file_name

    # TODO Implement image clipping
    if bbox:
        # image_obj = image_obj.rio.clip_box()
        pass

    # Save images
    image_obj.rio.to_raster(file_path)
    logging.info(f"Saved image to {file_path}.")

    return


def create_bounding_box(lat, lon, distance_km):
    center_point = Point(lat, lon)

    # Calculate the coordinates of the points approximately 5 km north and south of the center
    ne_point = distance.distance(kilometers=distance_km).destination(
        center_point, 45
    )  # 45 degrees is northeast
    sw_point = distance.distance(kilometers=distance_km).destination(
        center_point, 225
    )  # 225 degrees is southwest

    center_point

    return [
        sw_point.latitude,
        sw_point.longitude,
        ne_point.latitude,
        ne_point.longitude,
    ]


def main(args):

    bbox = create_bounding_box(args.lat, args.lon, distance_km=args.extents)
    logging.info(
        f"Extracting satellite imagery at coords:{args.lat, args.lon} for date/daterange {args.date}."
    )

    stac_items_to_download = search_elemnt84_stac(
        bbox, args.date, collections=args.source
    )

    logging.info(
        f"{len(stac_items_to_download)} items found in {args.source} collections."
    )
    logging.info(f"Assets available: {stac_items_to_download[0].assets.keys()}")

    # NOTE thumbnail.jpg and GeoTiff are available for open download, jpeg2000 are not

    save_dir = "./aws_data/"

    for item in tqdm(stac_items_to_download):
        for asset_name in args.assets:
            # Download imagery
            download_from_aws_s3(item, asset_name, save_dir, file_extension="jpg")

    # Check files have been saved
    logging.info(f"Files saved to {save_dir}: {os.listdir(save_dir)}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Extract news article from BBC RSS feed"
    )

    parser.add_argument(
        "-s",
        "--source",
        type=str,
        default="sentinel-2-l2a",
        help="'sentinel-2-l2a' or 'sentinel-s1-l1c'",
    )
    parser.add_argument(
        "-a",
        "--assets",
        type=list,
        default=["thumbnail"],
        help="Asset types to download",
    )
    parser.add_argument(
        "-d",
        "--date",
        type=str,
        default=None,
        required=True,
        help="YYYY-MM-DD date to extract nearest imagery",
    )
    parser.add_argument(
        "-lat",
        type=float,
        default=None,
        required=True,
        help="Latitude to extract satellite image",
    )
    parser.add_argument(
        "-lon",
        type=float,
        default=None,
        required=True,
        help="Longitude to extract satellite image",
    )
    parser.add_argument(
        "-e",
        "--extents",
        type=int,
        default=5,
        help="Size of desired bounding box in km",
    )

    args = parser.parse_args()
    main(args)
