from PIL import Image

class ImageTransformer():
    def __init__(self):
        self.height = 1080
        self.width = 1980
        self.background_color = (26, 26, 26)

    def save_new_image(self, img_path, new_img_path, y=None):
        image = Image.open(img_path)
        if image.width > self.width or image.height > self.height:
            ratio = min(self.width / image.width, self.height / image.height)
            image = image.resize((self.width * ratio, self.height * ratio))

        new_image = Image.new('RGB', (self.width, self.height), self.background_color)

        y = self.height // 2 - image.height // 2 if y is None else y
        box = (self.width // 2 - image.width // 2, y)
        new_image.paste(image, box=box)
        new_image.save(new_img_path)


if __name__ == '__main__':
    imgt = ImageTransformer()
    imgt.save_new_image('img/IAmA_dguq41/comment1_level1_frame0.jpeg', 'tmp/omg.jpeg')
