from pystac_client import Client
from urllib.parse import urlparse
from rioxarray import open_rasterio
import geopandas as gpd


def search_elemnt84_stac(bbox, datetime, collections=["sentinel-2-l2a"]):
    """
    Identify the sentinel image file to download from AWS using the Element 84 STAC database
    """

    client = Client.open("https://earth-search.aws.element84.com/v1")

    # Searching the sentinel-cogs location directly doesn't work for some reason
    # client = Client.open('https://sentinel-cogs.s3.us-west-2.amazonaws.com')

    search = client.search(
        max_items=10, collections=collections, bbox=bbox, datetime=datetime
    )
    print(f"{search.matched()} items found")

    item_collection = search.item_collection()

    return item_collection


def download_from_aws_s3(item, asset_type):
    """
    Save the image to a raster

    param :item_collection: Xarray collection of returned features from client search
    param :asset_types: See Element 84 docs for full list of images types eg. TCI (True Color Image)

    return:
    """
    # TODO Add comments etc

    image_href = item.assets[asset_type].href
    image_obj = open_rasterio(image_href)
    print(f"Filesize: {image_obj.nbytes/1024/1024:.2f}MB")

    return image_obj


if __name__ == "__main__":

    bbox = [32.68865076265763, 29.8744172395284, 32.47741813231619, 30.05545909539549]
    datetime = ["2024-02-20", "2024-02-23"]
    asset_types = ["thumbnail"]
    stac_items_to_download = search_elemnt84_stac(bbox, datetime)
    # TODO Create another script to locate desired files and save out as JSON

    for sentinel_capture in stac_items_to_download:
        for asset_type in asset_types:
            # Download imagery
            image_obj = download_from_aws_s3(sentinel_capture, asset_types=[asset_type])

            # Save images
            filename = sentinel_capture.id + ".jpg"
            data_path = f"./aws_data/{filename}"
            image_obj.rio.to_raster(data_path + filename)
            print(f"Saved image {filename}.")

        # Images to be exported outside Docker container and stored as a GitHub Artifact
