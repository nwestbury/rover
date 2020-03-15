import os
from youtube_upload import initialize_upload, upload_thumbnail

class YouTubeUploader():
    def __init__(self):
        pass

    def upload_thumbnail(self, thumbNailPath, video_id):
        upload_thumbnail(video_id, thumbNailPath)

    def upload(self, videoPath, postTitle, subReddit, postList, credits={}):
        title = f'{postTitle} (r/{subReddit} | Reddit Rover)'
        extra_credits = os.linesep + os.linesep.join(f'{key}: {link}' for key, link in credits.items())

        description = f'''► {title}
► I am Reddit Rover, I explore Reddit and find the highlights for your enjoyment! New videos every day.

⭐ Click the Subscribe button to get video in your feed
👍 Like the video!
📝 Write a comment to respond with your own story!


Credits:
Distorted Bars: Video (https://www.youtube.com/watch?v=dnPB0WRUUdE) and audio from Joe Jabon (https://www.youtube.com/watch?v=Y62EgHvwa8k)
Rover Icon: https://www.flaticon.com/free-icon/mars-rover_81850
Sub Reddit: r/{subReddit}{extra_credits}

Posts:
{os.linesep.join(postList)}
'''
        tags = ['Reddit Rover', 'Reddit', 'Reader']
        categoryId = '24'
        privacyStatus = 'public'
        return initialize_upload(videoPath, title, description, tags, categoryId, privacyStatus)

if __name__ == "__main__":
    ytu = YouTubeUploader()
    ytu.upload('Omg title', 'AskReddit', ['1:03 - link 1', '1:04 - link 2'])