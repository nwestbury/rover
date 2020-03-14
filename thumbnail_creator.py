import os
from PIL import Image
import requests
from io import BytesIO

from image_transformer import ImageTransformer
from bing_search import get_image_keyword

class ThumbnailCreator():
    def __init__(self):
        self.dimensions = (1280, 720)
        self.background_color = (26, 26, 26)

        self.cwd = os.path.dirname(os.path.realpath(__file__))

        self.it = ImageTransformer()
        self.it.set_width_height(*self.dimensions)

    def fetch_image(self, title):
        image_infos = [] # get_image_keyword(title)

        if not image_infos:
            img = Image.open(os.path.join(self.cwd, 'assets', 'shrug.png'))
            ref_link = 'https://www.pngkey.com/download/u2q8e6u2y3t4a9t4_shrug-emoji-old-man-shrugging-old-man-png/'
            return img, ref_link

        url, ref_link = image_infos[0]['url'], image_infos[0]['ref']
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))

        return img, ref_link

    def create_thumbnail(self, path, title):
        canvas = Image.new('RGB', self.dimensions, self.background_color)

        icon_img = Image.open(os.path.join(self.cwd, 'assets', 'rover-white.png'))
        ratio = (self.dimensions[1] // 3) / icon_img.height
        icon_img = icon_img.resize((int(icon_img.width * ratio), int(icon_img.height * ratio)))
        icon_box = (self.dimensions[0] - icon_img.width - 20, self.dimensions[1] - icon_img.height - 20)
        canvas.paste(icon_img, box=icon_box, mask=icon_img)

        title_img = Image.open(os.path.join(self.cwd, 'video', 'posttitle.jpg'))
        ratio = (self.dimensions[0] - 40) / title_img.width
        title_img = title_img.resize((int(title_img.width * ratio), int(title_img.height * ratio)))
        title_box = (20, 20)
        canvas.paste(title_img, box=title_box)
        
        pic_img, ref_link = self.fetch_image(title)
        max_width = self.dimensions[0] - 40 - 5 - icon_img.width
        max_height = self.dimensions[1] - 40 - 20 - title_img.height
        pic_img.thumbnail((max_width, max_height))
        x = int((max_width - pic_img.width) / 2) + 10
        y = int((max_height - pic_img.height) / 2) + 20 + 20 + title_img.height
        canvas.paste(pic_img, box=(x, y))

        canvas.save(path)

        return path, ref_link

if __name__ == "__main__":
    tc = ThumbnailCreator()
    tc.create_thumbnail(os.path.join(tc.cwd, 'video', 'thumnail.jpg'), 'test')
