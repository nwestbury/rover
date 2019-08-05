import praw
import logging
import os
import json
import subprocess
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S%p',
    level=logging.INFO
)
logger = logging.getLogger('reddit_video')

class RedditVideo():
    def __init__(self):
        with open('config.json') as f:
            config = json.load(f)

        self.reddit = praw.Reddit(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            password=config['password'],
            user_agent=('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/58.0.3029.110 Safari/537.36'),
            username=config['username'],
        )

        self.metadata_dir = config['METADATA_DIR']

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
        submission_ids = self.fetch_sub_post(subreddit_info)

        for submission_id in submission_ids:
            self.create_video_frames(subreddit_info['name'], submission_id)

    def fetch_sub_post(self, subreddit_info):
        sub_reddit = self.reddit.subreddit(subreddit_info['name'])

        submissions = []
        for submission in sub_reddit.top(time_filter='day', limit=subreddit_info['num_posts']):
            submissions.append(submission.id)
            logger.info('Got Submission Glidings: %s', submission.gildings)
            # print(submission.title, submission.score, submission.url, submission.num_comments, submission.gildings)

        logger.info('Got Submission IDs: %s', submissions)
        return submissions

    def create_video_frames(self, subreddit_name, submission_id):
        path = os.path.join(self.metadata_dir, f"{subreddit_name}_{submission_id}.csv")
        if os.path.isfile(path):
            logger.info('Skipping already fetched file: %s', path)
            return path

        cmd = ["node", "save_reddit.js", subreddit_name, submission_id]
        logger.info('Scraping %s %s... [%s]', submission_id, submission_id, ' '.join(cmd))
        out = subprocess.run(cmd, capture_output=True)
        logger.info('Got output %s', out)

        return path
