import logging
import os
import random
import sys
import requests
from environs import Env


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def get_amount_comics(url):
    response = requests.get(url)
    response.raise_for_status()
    response_extraction = response.json()
    if response_extraction.get('num'):
        return response_extraction['num']


def create_comics_url(comics_id):
    return f'https://xkcd.com/{comics_id}/info.0.json'


def extract_comics_info(url):
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def load_img(img_url, name, dir_path):

    img_path = os.path.join(dir_path, name)

    response = requests.get(img_url)
    response.raise_for_status()

    with open(img_path, 'wb') as img:
        img.write(response.content)


def get_wall_upload_server(url, group_id, access_token):

    params = {
        'access_token': access_token,
        'group_id': group_id,
        'v': '5.131'
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response_extraction = response.json()

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
        url, group_id, access_token, server, photo, hash
):

    params = {
        'server': server,
        'photo': photo,
        'hash': hash,
        'group_id': group_id,
        'access_token': access_token,
        'v': '5.131',
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    response_extraction = response.json()

    params_from_wall = [
        response_extraction['response'][0].get('owner_id'),
        response_extraction['response'][0].get('id'),
    ]

    if all(params_from_wall):
        return params_from_wall
    else:
        print('Something wrong with save photo to wall')


def post_photo_to_wall(
        url, access_token, message, group_id, owner_id, media_id
):
    attachments = f'photo{owner_id}_{media_id}'
    params = {
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': message,
        'attachments': attachments,
        'access_token': access_token,
        'v': '5.131',
    }

    response = requests.post(url, params=params)
    response.raise_for_status()

    return response.json()


def save_img_pipeline(dir_name, comics_id):
    os.makedirs(dir_name, exist_ok=True)

    comics_url = create_comics_url(comics_id)
    comics_info = extract_comics_info(comics_url)
    comics_img_url = comics_info['img']
    comics_img_comment = comics_info['alt']
    img_name = f'{comics_id}.png'
    load_img(comics_img_url, img_name, dir_name)
    return comics_img_comment, img_name


def post_photo_pipeline(
        dir_name, photo, img_comment, group_id, access_token,
        server_url, wall_photo_url, wall_post_url
):
    img_server_url = get_wall_upload_server(server_url, group_id, access_token)
    response_server = send_photo_to_server(
        img_server_url, dir_name, photo
    )
    response_wall = save_photo_to_wall(
        wall_photo_url, group_id, access_token, *response_server
    )

    response_post = post_photo_to_wall(
        wall_post_url, access_token, img_comment, group_id, *response_wall
    )
    if response_post.get('response'):
        logging.info('Image successfully posted!')
        os.remove(os.path.join(dir_name, photo))
    else:
        logging.error('Something wrong with post photo to wall')


if __name__ == '__main__':

    env = Env()
    env.read_env()

    access_token = env('ACCESS_TOKEN')
    group_id = env('GROUP_ID')
    dir_name = env('DIR_NAME')

    xkcd_api_url = 'https://xkcd.com/info.0.json'
    server_url = 'https://api.vk.com/method/photos.getWallUploadServer/'
    wall_photo_url = 'https://api.vk.com/method/photos.saveWallPhoto/'
    wall_post_url = 'https://api.vk.com/method/wall.post/'

    amount_comics = get_amount_comics(xkcd_api_url)
    comics_random_id = random.choice(range(amount_comics))

    comics_img_comment, img_name = save_img_pipeline(
        dir_name, comics_random_id
    )

    post_photo_pipeline(
        dir_name, img_name, comics_img_comment, group_id, access_token,
        server_url, wall_photo_url, wall_post_url
    )
