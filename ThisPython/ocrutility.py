try:
    import Image as ImagePIL
except ImportError:
    from PIL import Image as ImagePIL

try:
    from wand.image import Image as ImageWand
except ImportError as e:
    print(e)

import io, os
import hasher
import tesserocr
from constants import *

def ocr_text(abspath):
    root_tmp, ext_tmp = os.path.splitext(abspath)

    if ext_tmp in DOC_FORMATS:
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
    elif ext_tmp in IMAGE_FORMATS:
        img = ImagePIL.open(abspath)
        data = tesserocr.image_to_text(img)
    else:
        data = ""
    return data