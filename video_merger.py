import logging
import os
from moviepy.editor import *
from gtts import gTTS
from PIL import Image

from image_transformer import ImageTransformer
from speaker import GoogleSpeaker

logger = logging.getLogger('video_merger')

class VideoMerger():
    def __init__(self):
        self.imageTransformer = ImageTransformer()
        self.speaker = GoogleSpeaker()
        self.transition_clip = VideoFileClip(os.path.join('clips', 'static.mp4'))

    def get_largest_heights(self, submission_frames):
        largest_heights = {}
        for frame in reversed(submission_frames): # assume last frame has the largest height
            if frame['Group'] not in largest_heights:
                _, height = self.imageTransformer.get_image_size(frame['Path'])
                height = max(self.imageTransformer.height // 2 - height // 2, 0)
                largest_heights[frame['Group']] = height
        return largest_heights

    def load_frames(self, submission_frames):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        for submission in submission_frames:
            clips = []
            if not submission:
                continue

            largest_height_by_group = self.get_largest_heights(submission)
            last_group = submission[0]['Group']
            for frame in submission:
                logger.info('Working on frame %s', frame['Name'])

                cur_group = frame['Group']
                if cur_group != last_group:
                    clips.append(self.transition_clip)
                    last_group = cur_group

                fp = os.path.join('tmp', frame['Name'] + '.mp3')
                fp2 = os.path.join('tmp', frame['Name'] + '.jpeg')


                self.speaker.say_and_save(frame['Text'], fp)

                audio_clip = AudioFileClip(fp)
                max_height = largest_height_by_group[cur_group]
                self.imageTransformer.save_new_image(frame['Path'], fp2, y=max_height)
                clip = ImageClip(fp2, duration=audio_clip.duration)
                clip = clip.set_audio(audio_clip)
                clips.append(clip)

            vp = os.path.join('tmp', 'test.mp4')
            logger.info('Creating video file %s', vp)
            final_clip = concatenate_videoclips(clips, method='compose')
            final_clip.write_videofile(vp, fps=24)
            print('got clip', vp, clip)

        # os.rmdir('tmp')
