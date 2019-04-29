#!/usr/bin/env python3

import praw

if __name__ == '__main__':
    reddit = praw.Reddit(
        client_id='p_QH2tyER07oHg',
        client_secret='e-AfeUZ0eiazIKF4ev6c7ecHYwE',
        password='PEpw4&A%buAVmetkx@w!l%HzH2GPEXVz',
        user_agent=('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/58.0.3029.110 Safari/537.36'),
        username='Reddit_Rover_',
    )

    sub_reddit = reddit.subreddit('uwaterloo')

    for submission in sub_reddit.top(limit=1):
        print(submission.title, submission.score, submission.url, submission.num_comments)
        print('GLIDINGS!!', submission.gildings)

        submission.comment_sort = 'top'
        submission.comment_limit = 5
        submission.comments.replace_more(limit=1)

        for i, top_level_comment in enumerate(submission.comments):
            print('C', i, top_level_comment.gildings)

            for next_level_comment in top_level_comment.comments:
                print('???', next_level_comment.body)

    print(reddit.user.me())
