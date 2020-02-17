import logging
import os
import shutil
from moviepy.editor import *
from gtts import gTTS
from PIL import Image

from image_transformer import ImageTransformer
from speaker import MicrosoftSpeaker

logger = logging.getLogger('video_merger')

class VideoMerger():
    def __init__(self):
        self.imageTransformer = ImageTransformer()
        self.speaker = MicrosoftSpeaker()
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.transition_clip = VideoFileClip(os.path.join(self.cwd, 'clips', 'static.mp4'))

    def get_largest_heights(self, submission_frames):
        largest_heights = {}
        for frame in reversed(submission_frames): # assume last frame has the largest height
            if frame['Group'] not in largest_heights:
                _, height = self.imageTransformer.get_image_size(frame['Path'])
                height = max(self.imageTransformer.height // 2 - height // 2, 0)
                largest_heights[frame['Group']] = height
        return largest_heights

    def load_frames(self, submission_frames, output_path=None):
        tmp_folder = os.path.join(self.cwd, 'tmp')
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)

        clips = []
        for submission in submission_frames:
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

                audio_fp = os.path.join(tmp_folder, frame['Name'] + '.mp3')
                original_image_fp = os.path.join(self.cwd, frame['Path'])
                image_fp = os.path.join(tmp_folder, frame['Name'] + '.jpeg')

                self.speaker.say_and_save(frame['Text'], audio_fp)

                audio_clip = AudioFileClip(audio_fp)
                max_height = largest_height_by_group[cur_group]
                self.imageTransformer.save_new_image(original_image_fp, image_fp, y=max_height)
                clip = ImageClip(image_fp, duration=audio_clip.duration)
                clip = clip.set_audio(audio_clip)
                clips.append(clip)

        thumbnail_fp = os.path.join(self.cwd, submission_frames[0][0]['Path'])
        shutil.copy(thumbnail_fp, os.path.join(self.cwd, 'video', 'thumbnail.jpg'))

        video_fp = os.path.join(self.cwd, 'video', 'out.mp4') if output_path is None else output_path
        logger.info('Creating video file %s', video_fp)
        final_clip = concatenate_videoclips(clips, method='compose')
        final_clip.write_videofile(
            video_fp, fps=24, remove_temp=False,
            temp_audiofile=os.path.join(tmp_folder, 'TMPaudio.mp3')
        ) # not sure but remove_temp=False is needed

        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder)

        return video_fp
