import logging
import os
import random
import sys
import requests
from environs import Env


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class VkApiError(Exception):
    pass


def raise_vk_api_error(response):
    if response.get('error'):
        raise VkApiError(f'Something wrong with vk api:\n{response["error"]}')


def get_comics_amount(url):
    response = requests.get(url)
    response.raise_for_status()
    response_extraction = response.json()
    return response_extraction['num']


def download_img(img_url, name, dir_path):

    img_path = os.path.join(dir_path, name)

    response = requests.get(img_url)
    response.raise_for_status()

    with open(img_path, 'wb') as img:
        img.write(response.content)


def get_wall_upload_server(group_id, access_token):

    server_url = 'https://api.vk.com/method/photos.getWallUploadServer/'
    params = {
        'access_token': access_token,
        'group_id': group_id,
        'v': '5.131'
    }

    response = requests.get(server_url, params=params)
    response.raise_for_status()
    response_extraction = response.json()
    raise_vk_api_error(response_extraction)
    logging.info('Get url for upload image')
    return response_extraction['response']['upload_url']


def send_photo_to_server(url, dir_path, photo):

    img_path = os.path.join(dir_path, photo)
    with open(img_path, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
    response.raise_for_status()
    response_extraction = response.json()
    raise_vk_api_error(response_extraction)
    logging.info('Send image to vk server')
    params_from_server = [
        response_extraction.get('server'),
        response_extraction.get('photo'),
        response_extraction.get('hash'),
    ]
    if all(params_from_server):
        return params_from_server
    else:
        print('Something wrong with send photo to server')


def save_photo_to_wall(
        group_id, access_token, server, photo, vk_hash
):

    wall_photo_url = 'https://api.vk.com/method/photos.saveWallPhoto/'
    params = {
        'server': server,
        'photo': photo,
        'hash': vk_hash,
        'group_id': group_id,
        'access_token': access_token,
        'v': '5.131',
    }

    response = requests.post(wall_photo_url, params=params)
    response.raise_for_status()
    response_extraction = response.json()
    raise_vk_api_error(response_extraction)
    logging.info('Save image to vk wall')

    params_from_wall = [
        response_extraction['response'][0].get('owner_id'),
        response_extraction['response'][0].get('id'),
    ]

    if all(params_from_wall):
        return params_from_wall
    else:
        logging.error('Something wrong with saving photo to wall')


def post_photo_to_wall(
        access_token, message, group_id, owner_id, media_id
):
    wall_post_url = 'https://api.vk.com/method/wall.post/'
    attachments = f'photo{owner_id}_{media_id}'
    params = {
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': message,
        'attachments': attachments,
        'access_token': access_token,
        'v': '5.131',
    }

    response = requests.post(wall_post_url, params=params)
    response.raise_for_status()
    response_extraction = response.json()
    raise_vk_api_error(response_extraction)

    logging.info('Image successfully posted!')

    return response.json()


def download_xkcd_img(dir_name, comics_id):
    os.makedirs(dir_name, exist_ok=True)

    comics_url = f'https://xkcd.com/{comics_id}/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()
    comics_info = response.json()

    comics_img_url = comics_info['img']
    comics_img_comment = comics_info['alt']
    img_name = f'{comics_id}.png'

    download_img(comics_img_url, img_name, dir_name)

    return comics_img_comment, img_name


def post_photo(
        dir_name, photo, img_comment, group_id, access_token,
):
    img_server_url = get_wall_upload_server(group_id, access_token)
    server_response = send_photo_to_server(img_server_url, dir_name, photo)
    wall_response = save_photo_to_wall(
        group_id, access_token, *server_response
    )

    post_photo_to_wall(
        access_token, img_comment, group_id, *wall_response
    )
    os.remove(os.path.join(dir_name, photo))


if __name__ == '__main__':

    env = Env()
    env.read_env()

    vk_access_token = env('VK_ACCESS_TOKEN')
    group_id = env('VK_GROUP_ID')
    vk_img_dir = env('VK_IMG_DIR')

    xkcd_api_url = 'https://xkcd.com/info.0.json'

    comics_amount = get_comics_amount(xkcd_api_url)
    random_comics_id = random.randint(1, comics_amount)

    comics_img_comment, img_name = download_xkcd_img(
        vk_img_dir, random_comics_id
    )

    post_photo(
        vk_img_dir, img_name, comics_img_comment, group_id, vk_access_token
    )
