import os
import requests
import subprocess
from urllib.parse import urlparse

def download_dataset(name, url, raw_dir):
    os.makedirs(raw_dir, exist_ok=True)

    parsed_url = urlparse(url)

    if parsed_url.scheme in ['http', 'https']:
        return _download_file(name, url, raw_dir)
    elif 'github.com' in url:
        return _clone_repo(url, raw_dir)
    else:
        raise ValueError("Unsupported URL")


def _download_file(name, url, raw_dir):
    filename = os.path.basename(url) or f"{name}.zip"
    filepath = os.path.join(raw_dir, filename)

    if os.path.exists(filepath):
        return filepath

    response = requests.get(url, stream=True)
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)

    return filepath


def _clone_repo(url, raw_dir):
    if os.listdir(raw_dir):
        return
    subprocess.run(['git', 'clone', url, raw_dir], check=True)