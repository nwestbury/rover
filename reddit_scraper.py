import json
import logging
import praw
import os
import csv
import subprocess

logger = logging.getLogger('reddit_scraper')

class RedditScraper():
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

    def fetch_sub_post(self, subreddit_info):
        sub_reddit = self.reddit.subreddit(subreddit_info['name'])

        submissions = []
        for submission in sub_reddit.top(time_filter='day', limit=subreddit_info['num_posts']):
            submissions.append({
                'id': submission.id,
                'title': submission.title,
                'url': submission.url,
                'num_comments': submission.num_comments,
                'gildings': submission.gildings,
            })
            logger.warning('Got Submission Glidings: %s', submission.gildings)

        logger.warning('Got Submission IDs: %s', [sub['id'] for sub in submissions])
        return submissions
    
    def create_submission_video_frames(self, subreddit_name, submission_id):
        path = os.path.join(self.metadata_dir, f"{subreddit_name}_{submission_id}.csv")
        if os.path.isfile(path):
            logger.warning('Skipping already fetched file: %s', path)
            return path

        cmd = ["node", "save_reddit.js", subreddit_name, submission_id]
        logger.warning('Scraping %s... [%s]', submission_id, ' '.join(cmd))
        out = subprocess.run(cmd, capture_output=True)
        if out.returncode:
            logger.warning('Got output %s', out)

        return path

    def read_csv(self, csv_path):
        with open(csv_path, encoding='utf8') as csv_file:
            csv_dict = list(csv.DictReader(csv_file))
        return csv_dict


    def fetch_and_create_frames(self, subreddit_info):
        submissions = self.fetch_sub_post(subreddit_info)

        frame_paths = []
        for submission in submissions:
            csv_path = self.create_submission_video_frames(subreddit_info['name'], submission['id'])
            csv_data = self.read_csv(csv_path)
            frame_paths.append(csv_data)

        for index in range(len(frame_paths)):
            frame_paths[index].sort(key=lambda x: x['Group'])

        return submissions, frame_paths
