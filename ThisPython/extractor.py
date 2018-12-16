from PIL import Image as ImagePIL
from luminoth.tools.checkpoint import get_checkpoint_config
from luminoth.utils.predicting import PredictorNetwork
from utility import Utility
import constants
import docx
import io
import os
import platform
import subprocess
import tesserocr

class Extractor(object):
    # luminoth (image object detection) setup
    predictor_network = PredictorNetwork(get_checkpoint_config('fast'))

    def __init__(self):
        # cross platform check
        self.MY_OS_IS = platform.system()

    # extract text from microsoft docx file
    def docx2text(self, filename):
        msdocx = docx.Document(filename)
        fullText = []
        for para in msdocx.paragraphs:
            fullText.append(para.text)
        return '\n'.join(fullText)

    # convert all pages in the pdf file into images
    def pdf2img(self, abspath):
        img_list = []

        # use subprocess to execute other program in order to convert pdf to images
        with open(abspath) as pdf:
            if (self.MY_OS_IS == "Linux"):
                p = subprocess.Popen(['pdftoppm',  '-png'], stdin=pdf, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif (self.MY_OS_IS == "Windows"):
                p = subprocess.Popen(['poppler/pdftoppm.exe',  '-png'], stdin=pdf, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                sys.exit("Unsupported operating system platform, expecting Windows or Linux")

        # retrive data from PIPE
        data, error = p.communicate()

        # split each page
        img_list = data.split(b'\x89PNG')

        # remove empty string if any
        img_list = list(filter(None, img_list))

        # add back png magic value
        for i in range(len(img_list)):
            img_list[i] = b'\x89PNG' + img_list[i]

        return img_list

    # predict what object is in the image
    def img_predict(self, img_pil):
        image = img_pil.convert('RGB')
        objects = Extractor.predictor_network.predict_image(image)
        return objects

    # extract information (text, object) from file
    def extract(self, abspath):
        Utility.print_event("Process file " + abspath)

        root_tmp, ext_tmp = os.path.splitext(abspath)
        ext_tmp_lower = ext_tmp.lower()

        img_json = []
        final_text = ""

        if (ext_tmp_lower in constants.IMAGE_FORMATS):
            # identify object and text from image.
            with ImagePIL.open(abspath).convert('RGB') as img_pil:
                img_json.append(self.img_predict(img_pil))
                final_text = tesserocr.image_to_text(img_pil)
        elif (ext_tmp_lower in constants.DOC_FORMATS) and (ext_tmp_lower.endswith(".pdf")):
            # Setup two lists which will be used to hold our images and final_text
            img_pages = []
            text_pages = []
            
            img_pages = self.pdf2img(abspath)

            # Now we just need to run OCR over the image blobs
            for img in img_pages:
                with ImagePIL.open(io.BytesIO(img)) as img_pil:
                    img_json.append(self.img_predict(img_pil))
                    text_pages.append(tesserocr.image_to_text(img_pil))
            # store all of the recognized text in final_text.
            final_text = ''.join(text_pages)
        elif (ext_tmp_lower in constants.DOC_FORMATS) and (ext_tmp_lower.endswith(".docx")):
            # get all the words in the docx
            final_text = self.docx2text(abspath)

        return final_text, img_json
