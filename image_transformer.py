from PIL import Image

class ImageTransformer():
    def __init__(self):
        self.height = 1080
        self.width = 1920
        self.background_color = (26, 26, 26)

    def get_image_size(self, img_path):
        with Image.open(img_path) as image:
            return image.size # (width, height)

    def save_new_image(self, img_path, new_img_path, y=None):
        image = Image.open(img_path)
        if image.width > self.width or image.height > self.height:
            ratio = min(self.width / image.width, self.height / image.height)
            image = image.resize((int(image.width * ratio), int(image.height * ratio)))
            y = self.height // 2 - image.height // 2

        new_image = Image.new('RGB', (self.width, self.height), self.background_color)

        y = self.height // 2 - image.height // 2 if y is None else y
        y = max(y, 0)
        box = (self.width // 2 - image.width // 2, y)
        new_image.paste(image, box=box)
        new_image.save(new_img_path)


if __name__ == '__main__':
    imgt = ImageTransformer()
    imgt.save_new_image('img/IAmA_dguq41/comment1_level1_frame0.jpeg', 'tmp/test.jpeg')
