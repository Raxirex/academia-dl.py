#!/usr/bin/env python3

import os
import sys
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
import tldextract

REFERER = 'http://scholar.google.com'
PREFIX = 'https://www.academia.edu/download'
MAX_RETRIES = 5

def validate_url(academia_url):
    parsed_url = urlparse(academia_url)
    if not parsed_url.scheme or not parsed_url.netloc or not parsed_url.path:
        return False

    if not parsed_url.scheme in {"http", "https"}:
        return False

    extracted = tldextract.extract(parsed_url.netloc)
    if extracted.domain != "academia" or extracted.suffix != "edu":
        return False

    return True

def fetch_html(url):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers={"Referer": REFERER}, allow_redirects=True)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            sys.stderr.write(f"{e}\n")
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(5)
            else:
                sys.stderr.write(f"Max retries (= {MAX_RETRIES}) reached, exiting after trying to open URL: {url}\n")
                sys.exit(1)

def get_download_url(soup):
    download_url = soup.select_one("a.js-swp-download-button")["href"]
    download_id = download_url.split("/")[-2]
    return f"{PREFIX}/{download_id}"

def download_file(download_url, filename):
    response = requests.get(download_url, headers={"Referer": REFERER}, stream=True, allow_redirects=True)
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def process_url(academia_url):
    if not validate_url(academia_url):
        sys.stderr.write(f"Error parsing URL: {academia_url}\n")
        sys.exit(1)

    filename = f"{os.path.basename(urlparse(academia_url).path)[:250]}.pdf"
    if os.path.exists(filename):
        sys.stderr.write(f"{filename} already exists, skipping\n")
    else:
        html_content = fetch_html(academia_url)
        soup = BeautifulSoup(html_content, "html.parser")
        download_url = get_download_url(soup)
        download_file(download_url, filename)
        sys.stderr.write(f"Downloaded {filename}\n")

def main():
    with ThreadPoolExecutor() as executor:
        executor.map(process_url, sys.argv[1:])

if __name__ == "__main__":
    main()
