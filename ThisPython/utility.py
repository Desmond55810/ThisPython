from luminoth.tools.checkpoint import get_checkpoint_config
from luminoth.utils.predicting import PredictorNetwork
from PIL import Image as ImagePIL
from wand.image import Image as ImageWand
import constants
import hashlib
import io
import os
import tesserocr

class Utility(object):
    @staticmethod
    def ocr_text(abspath):
        root_tmp, ext_tmp = os.path.splitext(abspath)

        if ext_tmp in constants.DOC_FORMATS:
            # Setup two lists which will be used to hold our images and final_text
            req_image = []
            final_text = []

            # Open the PDF file using wand and convert it
            with ImageWand(filename=abspath, resolution=300) as img_ori:
                with img_ori.convert('png') as image_png:

                    # wand has converted all the separate pages in the PDF into separate image
                    # blobs. We can loop over them and append them as a blob into the req_image
                    # list
                    for img in image_png.sequence:
                        with ImageWand(image=img) as img_page:
                            req_image.append(img_page.make_blob('png'))

                    # Now we just need to run OCR over the image blobs and store all of the 
                    # recognized text in final_text.
                    for img in req_image:
                        img_ocr = ImagePIL.open(io.BytesIO(img))
                        txt = tesserocr.image_to_text(img_ocr)
                        final_text.append(txt)
                    data = ''.join(final_text)
        elif ext_tmp in constants.IMAGE_FORMATS:
            img = ImagePIL.open(abspath)
            data = tesserocr.image_to_text(img)
        else:
            data = ""
        return data

    @staticmethod
    def img_predict(abspath):
        checkpoint = 'fast'
        config = get_checkpoint_config(checkpoint)
        network = PredictorNetwork(config)
        image = ImagePIL.open(abspath).convert('RGB')
        objects = network.predict_image(image)
        return objects

    @staticmethod
    def hash_md5(abspath):
        # BUF_SIZE is totally arbitrary, change for your app!
        BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

        md5_tool = hashlib.md5()

        with open(file=abspath, mode='rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                md5_tool.update(data)

        return md5_tool.hexdigest()

