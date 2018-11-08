import os
import requests
from constants import *
from imgutility import predict
from hasher import md5_file_hasher
from ocrutility import ocr_text
from datetime import datetime
from elasticsearch import Elasticsearch
from multiprocessing.pool import ThreadPool

pool = ThreadPool(processes=1)

def disable_readonly_mode():
    url = 'http://localhost:9200/_all/_settings'
    headers = {'Content-type': 'application/json'}
    data = '''{"index.blocks.read_only_allow_delete": false}'''
    r = requests.put(url, headers=headers, data=data)
    print(r)

def indexing(abspath):    
    cpt = [abspath]
    new_cpt = [x for x in cpt if x.endswith(tuple(IMAGE_FORMATS)) or x.endswith(tuple(DOC_FORMATS))]

    for path in new_cpt:
        try:
            root_tmp, ext_tmp = os.path.splitext(abspath)
            ext_tmp = ext_tmp.lower()
            md5_digest = md5_file_hasher(abspath)

            text_content = ocr_text(abspath) # type str
            img_json = predict(abspath) # type list

            # by default we connect to localhost:9200
            es = Elasticsearch()

            disable_readonly_mode()

            es_url_index = 'documents'
            es_doc_type = '_doc'

            # dynamic mapping
            # datetimes will be serialized
            es.index(index=es_url_index, doc_type=es_doc_type, body={
                    "md5_hash": md5_digest,
                    "content": content,
                    "keyword": [],
                    "tag": img_json,
                    "file_name": os.path.basename(path),
                    "path_name": abspath,
                    "file_type": ext_tmp,
                    "last_edit_date": datetime.now(),
                    "file_owner": "",
                    "size_in_byte":os.path.getsize(abspath),
                }
            )
        except OSError as e:
            print(str(e)+"\n")
