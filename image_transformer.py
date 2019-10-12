from PIL import Image

class ImageTransformer():
    def __init__(self):
        self.width = 1080
        self.height = 1980
        self.background_color = (26, 26, 26)

    def save_new_image(self, img, path):
        image = Image.open(img)
        new_image = Image.new('RGB', (self.height, self.width), self.background_color)
        new_image.paste(image)
        new_image.save(path)


if __name__ == '__main__':
    imgt = ImageTransformer()
    imgt.save_new_image('img/IAmA_dguq41/comment1_level1_frame0.jpeg', 'tmp/omg.jpeg')
