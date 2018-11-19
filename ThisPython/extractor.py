import constants
import os
import io
from PIL import Image as ImagePIL
from luminoth.tools.checkpoint import get_checkpoint_config
from luminoth.utils.predicting import PredictorNetwork
import docx
import platform
import tesserocr
import subprocess

class Extractor(object):
    def __init__(self):
        # luminoth (image object detection) setup
        checkpoint = 'fast'
        config = get_checkpoint_config(checkpoint)
        self.predictor_network = PredictorNetwork(config)

        # cross platform check
        self.MY_OS_IS = platform.system()

    def docx2text(self, filename):
        doc = docx.Document(filename)
        fullText = []
        for para in doc.paragraphs:
            fullText.append(para.text)
        return '\n'.join(fullText)

    def pdf2img(self, abspath):
        img_list = []

        # use subprocess to execute other program in order to convert pdf to images
        pdf = open(abspath)
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

    def img_predict(self, img_pil):
        image = img_pil.convert('RGB')
        objects = self.predictor_network.predict_image(image)
        return objects

    def process(self, abspath):
        root_tmp, ext_tmp = os.path.splitext(abspath)
        ext_tmp_lower = ext_tmp.lower()

        img_json = []
        full_text_data = ""

        if (ext_tmp_lower in constants.IMAGE_FORMATS):
            img_pil = ImagePIL.open(abspath).convert('RGB')
            img_json.append(self.img_predict(img_pil))
            full_text_data = tesserocr.image_to_text(img_pil)
        elif (ext_tmp_lower in constants.DOC_FORMATS) and (ext_tmp_lower.endswith(".pdf")):
            # Setup two lists which will be used to hold our images and final_text
            pdf_page_img = []
            pdf_page_text = []
            
            pdf_page_img = self.pdf2img(abspath)

            # Now we just need to run OCR over the image blobs and store all of the 
            # recognized text in final_text.
            for img in pdf_page_img:
                img_pil = ImagePIL.open(io.BytesIO(img))
                img_json.append(self.img_predict(img_pil))
                pdf_page_text.append(tesserocr.image_to_text(img_pil))
            full_text_data = ''.join(pdf_page_text)
        elif (ext_tmp_lower in constants.DOC_FORMATS) and (ext_tmp_lower.endswith(".docx")):
            full_text_data = self.docx2text(abspath)
        else:
            pass

        return full_text_data, img_json