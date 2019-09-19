import logging
from datetime import datetime

from reddit_scraper import RedditScraper
from video_merger import VideoMerger

logger = logging.getLogger('reddit_video')

class RedditVideo():
    def __init__(self):
        self.scraper = RedditScraper()
        self.merger = VideoMerger()
        self.subreddits_info = [
            {'name': 'AskReddit', 'num_posts': 1},
            {'name': 'IAmA', 'num_posts': 1},
            {'name': 'Showerthoughts', 'num_posts': 1},
            {'name': 'tifu', 'num_posts': 1},
        ]

    def select_subreddit(self):
        now = datetime.now()
        weekday_index = datetime.weekday(now)
        index = weekday_index % len(self.subreddits_info)
        return self.subreddits_info[index]

    def create_video(self):
        subreddit_info = self.select_subreddit()
        paths = self.scraper.fetch_and_create_frames(subreddit_info)
        video_path = self.merger.load_frames(paths)
