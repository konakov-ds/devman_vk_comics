import os
import requests


def extract_img_url(url):
    response = requests.get(url)
    response.raise_for_status()

    response_extraction = response.json()
    img_url = response_extraction.get('img')
    if img_url:
        return img_url


def load_img(url, name, dir_path):

    img_path = os.path.join(dir_path, name)
    img_url = extract_img_url(url)

    response = requests.get(img_url)
    response.raise_for_status()

    with open(img_path, 'wb') as img:
        img.write(response.content)


if __name__ == '__main__':

    dir_path = 'xkcd_images'
    url = 'https://xkcd.com/353/info.0.json'
    name = '353.png'

    os.makedirs(dir_path, exist_ok=True)

    load_img(url, name, dir_path)
