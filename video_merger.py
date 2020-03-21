import logging
import os
import subprocess
import shutil
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
        self.transition_clip_path = os.path.join(self.cwd, 'assets', 'static.mkv')

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
        return run_cmd(cmd, cwd=cwd)

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

        logger.info('Command: %s', cmd)
        os.system(cmd)
        os.chdir(self.cwd)

        # run_cmd(cmd, cwd=cwd)

    def create_clip(self, image_fp, audio_fp, video_fp, cwd=None):
        duration = self.get_audio_duration(audio_fp)
        cmd = f'ffmpeg -y -loop 1 -i {image_fp} -i {audio_fp} -c:v libx264 -tune stillimage -c:a aac -shortest -t {duration} {video_fp}'
        return run_cmd(cmd, cwd=cwd)

    def merge_mkvs(self, clips, video_fp, tmp_folder):
        with open(os.path.join(tmp_folder, 'list.txt'), 'w') as f:
            f.writelines(os.linesep.join((f"file '{clip}'" for clip in clips)))

        cmd = f"ffmpeg -y -f concat -safe 0 -i list.txt -c copy -c:v libx264 -c:a aac {video_fp}"
        return run_cmd(cmd, cwd=tmp_folder)

    def load_frames(self, submission_frames, output_path=None):
        tmp_folder = os.path.join(self.cwd, 'tmp')
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)

        clips = [] # format: [''...]
        index = 0
        for submission in submission_frames:
            if not submission:
                continue

            largest_height_by_group = self.get_largest_heights(submission)
            last_group = submission[0]['Group']

            if index > 0:
                clips.append(self.transition_clip_path)

            for frame in submission:
                logger.info('Working on frame %s', frame['Name'])

                cur_group = frame['Group']
                if cur_group != last_group:
                    clips.append(self.transition_clip_path)
                    last_group = cur_group

                audio_fp = os.path.join(tmp_folder, f'{index}.mp3')
                original_image_fp = os.path.join(self.cwd, frame['Path'])
                image_fp = os.path.join(tmp_folder, f'{index}.jpeg')
                video_fp = os.path.join(tmp_folder, f'{index}.mkv')

                self.speaker.say_and_save(frame['Text'], audio_fp)

                max_height = largest_height_by_group[cur_group]
                self.imageTransformer.save_new_image(original_image_fp, image_fp, y=max_height)
                

                self.create_clip(image_fp, audio_fp, video_fp, cwd=tmp_folder)
                clips.append(video_fp)
                index += 1

        title_fp = os.path.join(self.cwd, submission_frames[0][0]['Path'])
        shutil.copy(title_fp, os.path.join(self.cwd, 'video', 'posttitle.jpg'))

        video_fp = os.path.join(self.cwd, 'video', 'out.mp4') if output_path is None else output_path
        logger.info('Creating video file %s', video_fp)
        self.merge_mkvs(clips, video_fp, tmp_folder)

        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder, ignore_errors=True)

        return video_fp

if __name__ == '__main__':
    vm = VideoMerger()
    duration = vm.get_audio_duration('tmp/title.mp3')
    logger.warning('Duration %d', duration)
