import os
from constants import *
from esutility import create_data
from hasher import md5_file_hasher
from ocrutility import ocr_text

def is_blank (myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return False
    #myString is None OR myString is empty or blank
    return True

def indexing(abspath):    
    cpt = [abspath]
    new_cpt = [x for x in cpt if x.endswith(tuple(IMAGE_FORMATS)) or x.endswith(tuple(DOC_FORMATS))]

    for path in new_cpt:
        root_tmp, ext_tmp = os.path.splitext(path)
        ext_tmp = ext_tmp.lower()
        md5_digest = md5_file_hasher(path)
        result = ocr_text(abspath=path)
        
        if is_blank(result):
            pass
        else:
            try:
                pass
                # create_data(md5_digest, result, os.path.basename(path), path, ext_tmp)
            except OSError as e:
                print(str(e)+"\n")