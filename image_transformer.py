from PIL import Image

class ImageTransformer():
    def __init__(self):
        self.width = 1080
        self.height = 1980
        self.background_color = (26, 26, 26)

    def test(self, img):
        image = Image.open(img)
        new_image = Image.new('RGB', (self.height, self.width), self.background_color)
        new_image.paste(image)
        new_image.save('test.jpeg')


if __name__ == '__main__':
    imgt = ImageTransformer()
    imgt.test('img/IAmA_dahvhb/comment1_level1_frame0.jpeg')
