from pystac_client import Client
import rioxarray
import logging
from tqdm import tqdm
import os


# Ignore lack of georeference for image thumbnails
logging.basicConfig(level=logging.INFO)


def search_elemnt84_stac(bbox, datetime, collections=["sentinel-2-l2a"]):
    """
    Identify the sentinel image file to download from AWS using the Element 84 STAC database

    param :collections: List of satellite imagery STACs to look for. Use "sentinel-2-l2a" or "sentinel-s1-l1c"
    """

    client = Client.open("https://earth-search.aws.element84.com/v1")

    # Searching the sentinel-cogs location directly doesn't work for some reason
    # client = Client.open('https://sentinel-cogs.s3.us-west-2.amazonaws.com')

    search = client.search(
        max_items=10, collections=collections, bbox=bbox, datetime=datetime
    )

    item_collection = search.item_collection()

    return item_collection


def download_from_aws_s3(item, asset_name, file_extension):
    """
    Save the image to a raster
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

    # Get Sentinel data structured name for image
    file_name = item.id + href_filetype
    file_path = f"./aws_data/{file_name}"

    # Save images
    image_obj.rio.to_raster(file_path)
    logging.info(f"Saved image to {file_path}.")

    return


if __name__ == "__main__":

    bbox = [
        30.696510174036007,
        46.265163784414824,
        30.555737616687253,
        46.35892215257451,
    ]

    collections_to_search = ["sentinel-2-l2a"]
    datetime = ["2024-02-20", "2024-02-21"]
    asset_names = ["thumbnail"]
    stac_items_to_download = search_elemnt84_stac(
        bbox, datetime, collections=collections_to_search
    )

    logging.info(
        f"{len(stac_items_to_download)} items found in {collections_to_search} collections for date/daterange {datetime}."
    )
    logging.info(f"Assets available: {stac_items_to_download[0].assets.keys()}")

    # NOTE thumbnail.jpg and GeoTiff are available for open download, jpeg200 are not

    for item in tqdm(stac_items_to_download):
        for asset_name in asset_names:
            # Download imagery
            download_from_aws_s3(item, asset_name, file_extension="tif")
