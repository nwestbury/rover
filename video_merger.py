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
            clips = []
            for frame in submission[:1]:
                t = gTTS(frame['Text'])
                fp = os.path.join('tmp', frame['Name'] + '.mp3')
                t.save(fp)

                audio_clip = AudioFileClip(fp)
                clip = ImageClip(frame['Path'], duration=audio_clip.duration)
                clip.set_audio(audio_clip)
                clips.append(clip)

            print('sub', submission)

            vp = os.path.join('tmp', 'test.mp4')
            logger.info('Creating video file %s', vp)
            final_clip = concatenate_videoclips(clips, method='compose')
            final_clip.write_videofile(vp, fps=24)
            print('got clip', vp, clip)

        # os.rmdir('tmp')
