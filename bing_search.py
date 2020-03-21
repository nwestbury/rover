#!/usr/bin/env python3
from bs4 import BeautifulSoup
import logging
import requests
import http.cookiejar
import json
import urllib.request, urllib.error, urllib.parse

logger = logging.getLogger('bing')

def get_image_keyword(keyword, limit=1):
    query = urllib.parse.urlencode({
        'q': keyword,
        'FORM': 'HDRSC2',
    })
    url = "https://www.bing.com/images/search?" + query

    logger.info(f'Searching bing with {url}')

    headers={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
    soup = BeautifulSoup(urllib.request.urlopen(urllib.request.Request(url, headers=headers)), features='lxml')

    found_images = []

    try:
        for a in soup.find_all('a', {'class': 'iusc'}, limit=limit):
            m = json.loads(a['m'])
            found_images.append({
                'url': m['murl'],
                'ref': m['purl'],
            })
    except Exception as e:
        logger.error(f'Failure to find images. Error: {e}')

    return found_images
    
if __name__ == '__main__':
    images = get_image_keyword("nikita zimov pleistocene park")
    logger.warning('Got images %s', images)
