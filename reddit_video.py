import logging
from datetime import datetime

from reddit_scraper import RedditScraper
from video_merger import VideoMerger
from youtube_uploader import YouTubeUploader

logger = logging.getLogger('reddit_video')

class RedditVideo():
    def __init__(self):
        self.scraper = RedditScraper()
        self.merger = VideoMerger()
        self.uploader = YouTubeUploader()
        self.subreddits_info = [
            {'name': 'AskReddit', 'num_posts': 1},
            {'name': 'IAmA', 'num_posts': 1},
            {'name': 'Showerthoughts', 'num_posts': 1},
            {'name': 'tifu', 'num_posts': 1},
        ]
        self.default_video_path = './video/out.mp4'

    def select_subreddit(self):
        now = datetime.now()
        weekday_index = datetime.weekday(now)
        index = weekday_index % len(self.subreddits_info)
        return self.subreddits_info[index]

    def upload_video(self):
        subreddit_info = self.select_subreddit()
        submissions, paths = self.scraper.fetch_and_create_frames(subreddit_info)
        self._upload_video(subreddit_info['name'], submissions, self.default_video_path)

    def _upload_video(self, subreddit_name, submissions, video_path):
        title = submissions[0]['title']
        posts = [f"{i}: {submission['url']}" for i, submission in enumerate(submissions)]
        video_id = self.uploader.upload(title, subreddit_name, posts)
        self.uploader.upload_thumbnail(video_id)

    def create_video(self, upload=False):
        subreddit_info = self.select_subreddit()
        submissions, paths = self.scraper.fetch_and_create_frames(subreddit_info)
        video_path = self.merger.load_frames(paths)

        if upload:
            self._upload_video(subreddit_info['name'], submissions, video_path)
