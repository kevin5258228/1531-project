"""
Implementation of the user_profile_uploadphoto function.
H11A-quadruples, April 2020.
"""

import imghdr
from io import BytesIO
import requests
from PIL import Image
from error import AccessError, InputError
from database.database import AUTH_DATABASE, CHANNELS_DATABASE
from database.helpers_auth import is_token_valid, find_u_id, generate_code
from constants import PFP_FOLDER, DEFAULT_PFP

def user_profile_uploadphoto(token, img_url, x_start, y_start, x_end, y_end):
    """
    Given a url 'img_url' of a .jpg from the Internet, crops the image
    within bounds (x_start, y_start) and (x_end, y_end) and sets the user's
    profile picture to this cropped image.

    Args:
        token (str): Token of user who is uploading their photo.
        img_url (str): URL to the image on the Internet.
        x_start (int): left pixel to start crop.
        y_start (int): upper pixel to start crop.
        x_end (int): right pixel to end crop.
        y_end (int): lower pixel to end crop.
    Raises:
        AccessError: if token is invalid.
        InputError: if img_url does not return a HTTP status code 200.
        InputError: if any of x_start, y_start, x_end, y_end are out of image bounds.
        InputError: if image is not a JPG.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    response = requests.get(img_url)
    if response.status_code != 200:
        raise InputError(description="img_url did not return a 200 HTTP status")
    if imghdr.what(BytesIO(response.content)) != "jpeg":
        raise InputError(description="Image uploaded is not a JPG")

    ## Set the name of the image, eg. "jdH5ixbma3.jpg" and the path to
    ## the image relative to src, eg. "profile_pics/jdH5ixbma3.jpg"
    img_code = generate_code() if img_url != DEFAULT_PFP else "default"
    img_name = f"{img_code}.jpg"
    img_path = f"{PFP_FOLDER}/{img_name}"

    ## Open the image and check for InputErrors
    image = Image.open(BytesIO(response.content))
    width, height = image.size
    if x_start < 0 or x_end > width or y_start < 0 or y_end > height:
        raise InputError(description="Bounds are not within the dimensions of the image")

    ## Crop the image and save it
    image_cropped = image.crop((x_start, y_start, x_end, y_end))
    image_cropped.save(img_path)
    image.close()

    ## Set the url that contains the image and post the image to that url
    from port_settings import BASE_URL
    profile_img_url = f"{BASE_URL}/imgurl/{img_name}"
    requests.get(f"{profile_img_url}")

    ## Update the user's profile_img_url in the AUTH_DATABASE
    u_id = find_u_id(token)
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == u_id:
            user["profile_img_url"] = profile_img_url
            break
    AUTH_DATABASE.update(auth_data)

    ## Update the user's profile_img_url in the CHANNELS_DATABASE
    channel_data = CHANNELS_DATABASE.get()
    for channel in channel_data["channels"]:
        for member in channel["all_members"]:
            if member["u_id"] == u_id:
                member["profile_img_url"] = profile_img_url
                break
        for owner in channel["owner_members"]:
            if owner["u_id"] == u_id:
                owner["profile_img_url"] = profile_img_url
                break
    CHANNELS_DATABASE.update(channel_data)
    return {}
