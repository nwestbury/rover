import os
from PIL import Image
from image_transformer import ImageTransformer

class ThumbnailCreator():
    def __init__(self):
        self.dimensions = (1280, 720)
        self.background_color = (26, 26, 26)

        self.it = ImageTransformer()
        self.it.set_width_height(*self.dimensions)

    def create_thumbnail(self, out_path):
        canvas = Image.new('RGB', self.dimensions, self.background_color)


if __name__ == "__main__":
    cwd = os.path.dirname(os.path.realpath(__file__))

    tc = ThumbnailCreator()
    tc.create_thumbnail(os.path.join(cwd, 'video', 'thumnail.jpg'))