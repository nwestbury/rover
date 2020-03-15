import logging
import os
import subprocess
import shutil
from moviepy.editor import *
from gtts import gTTS
from PIL import Image

from image_transformer import ImageTransformer
from speaker import MicrosoftSpeaker

logger = logging.getLogger('video_merger')

def run_cmd(cmd, cwd=None):
    out = subprocess.run(cmd, capture_output=True, cwd=cwd)
    if out.returncode:
        logger.warning('Got output %s', out.stderr)
    return out.stdout.strip().decode('utf-8')


class VideoMerger():
    def __init__(self):
        self.imageTransformer = ImageTransformer()
        self.speaker = MicrosoftSpeaker()
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.transition_clip_path = os.path.join(self.cwd, 'assets', 'static.mp4')
        self.transition_clip_audio_path = os.path.join(self.cwd, 'assets', 'static.mp3')
        self.transition_clip_duration = self.get_audio_duration(self.transition_clip_path)

        self.transition_clip = VideoFileClip(self.transition_clip_path)

    def get_largest_heights(self, submission_frames):
        largest_heights = {}
        for frame in reversed(submission_frames): # assume last frame has the largest height
            if frame['Group'] not in largest_heights:
                _, height = self.imageTransformer.get_image_size(frame['Path'])
                height = max(self.imageTransformer.height // 2 - height // 2, 0)
                largest_heights[frame['Group']] = height
        return largest_heights

    def get_audio_duration(self, audio_file_path, cwd=None):
        cmd = f'ffprobe -i {audio_file_path} -show_entries format=duration -v quiet -of csv="p=0"'
        return round(float(run_cmd(cmd, cwd=cwd)), 1)

    def merge_audio_files(self, audio_file_paths, out_audio_path, cwd=None):
        cmd = f'ffmpeg -y -i "concat:{"|".join(audio_file_paths)}" -acodec copy {out_audio_path}'
        return run_cmd(cmd, cwd=cwd)

    def merge_pictures_as_video(self, image_file_info, master_audio_fp, out_video_path, cwd=None):
        loops = []
        for x in image_file_info:
            if x['path'].endswith('mp4'):
                loop = f'-i {x["path"]}'
            else:
                loop = f'-loop 1 -t {x["duration"]} -i {x["path"]}'
            loops.append(loop)

        loop_cmd = ' '.join(loops)
        cmd = f'\
            ffmpeg -y -hide_banner -loglevel panic\
                {loop_cmd} \
                -i {master_audio_fp} \
                -filter_complex "concat=n={len(image_file_info)}" \
                -shortest \
                -c:v libx264 -pix_fmt yuv420p -c:a aac \
                {out_video_path} \
        '

        if cwd is not None:
            os.chdir(cwd)
        print('Command', cmd)
        os.system(cmd)
        os.chdir(self.cwd)

        # run_cmd(cmd, cwd=cwd)

    def load_frames(self, submission_frames, output_path=None):
        tmp_folder = os.path.join(self.cwd, 'tmp')
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)

        clips = [] # format: [{path: '', duration: ''} ...]
        audio_clips = [] # format: ['', ...]

        index = 0
        for submission in submission_frames:
            if not submission:
                continue

            largest_height_by_group = self.get_largest_heights(submission)
            last_group = submission[0]['Group']

            for frame in submission:
                logger.info('Working on frame %s', frame['Name'])

                cur_group = frame['Group']
                if cur_group != last_group:
                    clips.append({'path': self.transition_clip_path, 'duration': self.transition_clip_duration})
                    audio_clips.append(self.transition_clip_audio_path)
                    last_group = cur_group

                audio_fp = os.path.join(tmp_folder, f'{index}.mp3')
                original_image_fp = os.path.join(self.cwd, frame['Path'])
                image_fp = os.path.join(tmp_folder, f'{index}.jpeg')

                self.speaker.say_and_save(frame['Text'], audio_fp)
                duration = self.get_audio_duration(audio_fp)

                max_height = largest_height_by_group[cur_group]
                self.imageTransformer.save_new_image(original_image_fp, image_fp, y=max_height)
                
                clips.append({'path': f'{index}.jpeg', 'duration': duration})
                audio_clips.append(f'{index}.mp3')
                index += 1

        # For some reason, audio can get out of sync so make sure the last frame is shown longer
        # so at least we don't lose audio (it will get cut out by ffmpeg)
        clips[-1]['duration'] += 10

        title_fp = os.path.join(self.cwd, submission_frames[0][0]['Path'])
        shutil.copy(title_fp, os.path.join(self.cwd, 'video', 'posttitle.jpg'))

        logger.info('Merging all %d audio files', len(audio_clips))
        master_audio_fp = os.path.join(tmp_folder, 'master.mp3')
        self.merge_audio_files(audio_clips, master_audio_fp, cwd=tmp_folder)

        video_fp = os.path.join(self.cwd, 'video', 'out.mp4') if output_path is None else output_path
        logger.info('Creating video file %s', video_fp)
        self.merge_pictures_as_video(clips, master_audio_fp, video_fp, cwd=tmp_folder)

        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder, ignore_errors=True)

        return video_fp


"""
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

        title_fp = os.path.join(self.cwd, submission_frames[0][0]['Path'])
        shutil.copy(title_fp, os.path.join(self.cwd, 'video', 'posttitle.jpg'))

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
"""

if __name__ == '__main__':
    vm = VideoMerger()
    duration = vm.get_audio_duration('tmp/title.mp3')
    print('dru', duration)