import sys

from abc import ABC, abstractmethod
from gtts import gTTS
import pyttsx3

if sys.platform == 'win32':
    import tts.sapi

# Base class
class Speaker(ABC):
    @abstractmethod
    def say_and_save(self, text, path):
        pass


class GoogleSpeaker(Speaker):
    def say_and_save(self, text, path):
        tts = gTTS(text=text, lang='en')
        tts.save(path)

class MicrosoftSpeaker(Speaker):
    def __init__(self):
        self.engine = tts.sapi.Sapi()
        self.engine.set_rate(2) # rate: -10 to 10
        self.engine.set_voice('David') # self.engine.get_voice_names()

    def say_and_save(self, text, path):
        if not path.endswith('.wav'):
            raise ValueError('Expect output path to be in wav format.')
        self.engine.create_recording(path, text)


class MultiPlatformSpeaker(Speaker):
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 200) # default=200

    def say_and_save(self, text, path):
        self.engine.say(text)
        self.engine.runAndWait() # cannot save directly :(


if __name__ == '__main__':
    ms = MicrosoftSpeaker()

    ms.say_and_save('I like pizza and pie.', './testomg.wav')

