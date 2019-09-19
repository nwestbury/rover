#!/usr/bin/env python3

import logging
logging.basicConfig(
    format='%(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S%p',
    level=logging.INFO
)

from reddit_video import RedditVideo

if __name__ == '__main__':
    rv = RedditVideo()
    rv.create_video()
