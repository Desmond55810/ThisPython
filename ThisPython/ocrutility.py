from PIL import ImageEnhance, ImageFilter
try:
    import Image as ImagePIL
except ImportError:
    from PIL import Image as ImagePIL

import argparse
import json
import sys, io, os
#from crawler import Crawler

#from tqdm import tqdm
import hasher
import tesserocr

#from checksum import Checksum

from wand.image import Image as ImageWand

from constants import *
from esutility import *
def isBlank (myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return False
    #myString is None OR myString is empty or blank
    return True

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def enhance_img(img):
    # img = img.convert('RGB')
    # img = img.filter(ImageFilter.MedianFilter())
    # img.convert('L')
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    return img

def ocr_text(abspath):
    root_tmp, ext_tmp = os.path.splitext(abspath)

    # Setup two lists which will be used to hold our images and final_text
    req_image = []
    final_text = []

    if ext_tmp in DOC_FORMATS:
        # Open the PDF file using wand and convert it
        with ImageWand(filename=abspath, resolution=300) as img_ori:
            #w, h = image_pdf.size
            #image_pdf.resize(w*3, h*3, filter="triangle")
            with img_ori.convert('jpeg') as image_jpeg:

                # wand has converted all the separate pages in the PDF into separate image
                # blobs. We can loop over them and append them as a blob into the req_image
                # list
                for img in image_jpeg.sequence:
                    with ImageWand(image=img) as img_page:
                        req_image.append(img_page.make_blob('jpeg'))

                # Now we just need to run OCR over the image blobs and store all of the 
                # recognized text in final_text.
                for img in req_image:
                    img_ocr = ImagePIL.open(io.BytesIO(img))
                    img_ocr = enhance_img(img_ocr)
                    txt = tesserocr.image_to_text(img_ocr)
                    final_text.append(txt)
                data = ''.join(final_text)
    elif ext_tmp in IMAGE_FORMATS:
        img = ImagePIL.open(abspath)
        # img = enhance_img(img)
        data = tesserocr.image_to_text(img)
    else:
        data = ""
        #raise TypeError('The file type (' + ext_tmp + ') is not supported')
    return data

def ocrutilityX(abspath):
    #if output_ext and not output_ext.startswith("."):
    #    tqdm.write("")
    #    sys.exit()

    #if not os.path.exists(dir_scan):
    #    tqdm.write("")
    #    sys.exit()

    #if os.path.isdir(dir_scan):
    #    cpt = Crawler.craw_dir(dir_scan)
    #else:
    #    cpt = [dir_scan]
    
    cpt = [abspath]
    new_cpt = [x for x in cpt if x.endswith(tuple(IMAGE_FORMATS)) or x.endswith(tuple(DOC_FORMATS))]

    if True:
        #sha1_obj = Checksum("files_sha1_checksum.txt")

        try:
            #pbar = tqdm(iterable=new_cpt, ascii=True, unit="files", total=len(new_cpt))
            for abspath in new_cpt:
                root_tmp, ext_tmp = os.path.splitext(abspath)
                ext_tmp = ext_tmp.lower()

                #pbar.set_postfix(processing=os.path.basename(abspath))
                md5_digest = hasher.md5_file_hasher(abspath)

                #if sha1_obj.is_checksum_exist(sha1):
                    #tqdm.write("checksum exist, skip \"" + abspath + "\"")
                    #pbar.update()
                    #continue

                result = ocr_text(abspath=abspath)
        
                if isBlank(result):
                    pass
                    #tqdm.write("Blank \"" + str(abspath) + "\"")
                else:
                    # write ocr into text file
                    try:
                        print("ok\n")

                        create_data(md5_digest, result, os.path.basename(abspath), abspath, "x")

                            #with open(root_tmp + output_ext, "w", encoding="utf-8") as text_file:
                            #    text_file.write(result)
                            #    sha1_obj.save_checksum(sha1)
                        #tqdm.write("OCRed \"" + str(abspath) + "\"")
                    except OSError as e:
                        print(str(e)+"\n")
                        #tqdm.write(str(e))
                #pbar.update()
        finally:
            pass
            #pbar.set_postfix()
            #pbar.close()
            
    else:
        for abspath in new_cpt:
            print(ocr_text(abspath=abspath))


#if __name__ == "__main__":
#    parser = argparse.ArgumentParser(description="Simple Prototype")
#    parser.add_argument('-d', type=str, help="Path to the directory", required=True)
#    parser.add_argument('-o', type=str, help="output file extension")
#    args = parser.parse_args()

#    #args.d = r"Z:\sample"
#    #args.d = r"Z:\documents"
#    #args.d = r"Z:\ocr\English\Checkmark"
#    args.d = r"Z:\scandoc"
#    args.o = ".txt"

#    output_ext = args.o
#    dir_scan = args.d
    
#    ocrutility(output_ext, dir_scan)
