#!/usr/bin/env python3

import argparse
import logging
logging.basicConfig(
    format='%(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S%p',
    level=logging.INFO
)

from reddit_video import RedditVideo

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-create', dest='create', action='store_false', help='Don\'t create only?')
    parser.add_argument('--upload', dest='upload', action='store_true', help='Upload only?')
    parser.set_defaults(create=True, upload=False)
    args = parser.parse_args()

    rv = RedditVideo()
    if args.create:
        rv.create_video(args.upload)
    elif args.upload:
        rv.upload_video()
