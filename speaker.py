from abc import ABC, abstractmethod

# Base class
class Speaker(ABC):
    @abstractmethod
    def say_and_save(self):
        pass


class GoogleSpeaker(Speaker):
    def say_and_save(self):
        print('4')

class MicrosoftSpeaker(Speaker):
    pass


if __name__ == '__main__':
    gs = GoogleSpeaker()
    gs.say_and_save()
