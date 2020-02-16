import sys, os
import logging

from abc import ABC, abstractmethod
from gtts import gTTS
from pydub import AudioSegment
import pyttsx3


logger = logging.getLogger('speaker')
# logger.setLevel(logging.DEBUG) # Why no work?

if sys.platform == 'win32':
    try:
        import tts.sapi
    except:
        logger.error('Some weird unfixable error import tts.sapi, just move on...')

# Base class
class Speaker(ABC):
    @abstractmethod
    def say_and_save(self, text, path):
        pass

    @property
    @abstractmethod
    def audio_format(self):
        pass


class GoogleSpeaker(Speaker):
    def say_and_save(self, text, path):
        tts = gTTS(text=text, lang='en')
        tts.save(path)

    @property
    def audio_format(self):
        return 'mp3'

# Best voice is probably this one: https://harposoftware.com/en/english-uk/191-Daniel-Nuance-Voice.html
class MicrosoftSpeaker(Speaker):
    def __init__(self):
        self.engine = tts.sapi.Sapi()
        self.engine.set_rate(2) # rate: -10 to 10

        logger.info('Voices %s', self.engine.get_voice_names())
        try:
            self.engine.set_voice('Daniel') # self.engine.get_voice_names()
        except IndexError:
            logger.error('Is the "Daniel" voice installed?')
            self.engine.set_voice('David')

    def say_and_save(self, text, path):
        if not path.endswith(('mp3', 'wav')):
            raise ValueError('Expect format output path to be wav or mp3 only')

        tmp_path = path + '.wav' if path.endswith('mp3') else path            
        self.engine.create_recording(tmp_path, text)

        if path.endswith('mp3'):
            AudioSegment.from_wav(tmp_path).export(path, format='mp3')
            os.remove(tmp_path)

    @property
    def audio_format(self):
        return 'mp3'

    def check_voices(self):
        logger.info('Voices %s', self.engine.get_voice_names())


class MultiPlatformSpeaker(Speaker):
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 200) # default=200

        voiceId = self.voices[0].id
        for voice in self.voices:
            if 'Daniel' in voice.name:
                voiceId = voice.id
                break
        self.engine.setProperty('voice', voiceId)

    def say_and_save(self, text, path):
        self.engine.say(text)
        self.engine.save_to_file(text, './omg/go.mp3')

    @property
    def audio_format(self):
        return None

    @property
    def voices(self):
        return self.engine.getProperty('voices')

    def check_voices(self):
        for voice in self.voices:
            logger.warning('Voice %s (id: %s)', voice.name, voice.id)

if __name__ == '__main__':
    mps = MultiPlatformSpeaker()
    mps.say_and_save('Hello World!', './test.mp3')
