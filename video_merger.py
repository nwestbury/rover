import logging
import os
from moviepy.editor import *
from gtts import gTTS

logger = logging.getLogger('video_merger')

class VideoMerger():
    def __init__(self):
        pass

    def load_frames(self, submission_frames):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        for submission in submission_frames:
            for frame in submission[:1]:
                t = gTTS(frame['Text'])
                fp = os.path.join('tmp', frame['Name'] + '.mp3')
                t.save(fp)
                clip = AudioFileClip(fp)

        # os.rmdir('tmp')
