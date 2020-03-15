import logging
import os
from datetime import datetime

from reddit_scraper import RedditScraper
from video_merger import VideoMerger
from youtube_uploader import YouTubeUploader
from thumbnail_creator import ThumbnailCreator

logger = logging.getLogger('reddit_video')

class RedditVideo():
    def __init__(self):
        self.scraper = RedditScraper()
        self.merger = VideoMerger()
        self.uploader = YouTubeUploader()
        self.thumbnail_creator = ThumbnailCreator()
        self.subreddits_info = [
            {'name': 'AskReddit', 'num_posts': 2},
            {'name': 'Showerthoughts', 'num_posts': 4},
            {'name': 'tifu', 'num_posts': 2},
        ]
        cwd = os.path.dirname(os.path.realpath(__file__))
        self.default_video_path = os.path.join(cwd, 'video', 'out.mp4')
        self.default_thumbnail_path = os.path.join(cwd, 'video', 'thumbnail.jpeg')

    def select_subreddit(self):
        now = datetime.now()
        weekday_index = datetime.weekday(now)
        index = weekday_index % len(self.subreddits_info)
        return self.subreddits_info[index]

    def upload_video(self):
        subreddit_info = self.select_subreddit()
        submissions, paths = self.scraper.fetch_and_create_frames(subreddit_info)

        self._upload_video(subreddit_info['name'], submissions, self.default_video_path, self.default_thumbnail_path)

    def _upload_video(self, subreddit_name, submissions, video_path, thumbnail_path, credits={}):
        title = submissions[0]['title']
        posts = [f"{i}: {submission['url']}" for i, submission in enumerate(submissions, 1)]
        video_id = self.uploader.upload(video_path, title, subreddit_name, posts, credits=credits)
        self.uploader.upload_thumbnail(thumbnail_path, video_id)

    def create_video(self, upload=False):
        subreddit_info = self.select_subreddit()
        submissions, paths = self.scraper.fetch_and_create_frames(subreddit_info)
        video_path = self.merger.load_frames(paths)

        title = submissions[0]['title']
        thumbnail_path, ref_link = self.thumbnail_creator.create_thumbnail(self.default_thumbnail_path, title)

        if upload:
            credits = {
                'Thumbnail Image': ref_link
            }
            self._upload_video(subreddit_info['name'], submissions, video_path, thumbnail_path, credits=credits)
