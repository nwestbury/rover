import os
from youtube_upload import initialize_upload, upload_thumbnail

class YouTubeUploader():
    def __init__(self):
        pass

    def upload_thumbnail(self, video_id):
        path = './video/thumbnail.jpg'
        upload_thumbnail(video_id, path)

    def upload(self, postTitle, subReddit, postList):
        title = f'{postTitle} (r/{subReddit})'
        path = './video/out.mp4'
        description = f'''► {title}
► I am Reddit Rover, I explore Reddit and find the highlights for your enjoyment!

⭐ Click the Subscribe button to get video in your feed
👍 Like the video!
📝 Write a comment to respond with your own story!


Credits:
Distorted Bars: Video (https://www.youtube.com/watch?v=dnPB0WRUUdE) and audio from Joe Jabon (https://www.youtube.com/watch?v=Y62EgHvwa8k)
Sub Reddit: r/{subReddit}

Posts:
{os.linesep.join(postList)}
'''
        tags = ['Reddit Rover', 'Reddit', 'Reader']
        categoryId = '24'
        privacyStatus = 'public'
        return initialize_upload(path, title, description, tags, categoryId, privacyStatus)

if __name__ == "__main__":
    ytu = YouTubeUploader()
    ytu.upload('Omg title', 'AskReddit', ['1:03 - link 1', '1:04 - link 2'])