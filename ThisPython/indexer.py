import os
import requests
from constants import *
from imgutility import predict
from hasher import md5_file_hasher
from ocrutility import ocr_text
from datetime import datetime
from elasticsearch import Elasticsearch
from multiprocessing.pool import ThreadPool
from constants import ES_DOC_TYPE, ES_URL_INDEX
from multiprocessing import Pool

def disable_readonly_mode():
    url = 'http://localhost:9200/_all/_settings'
    headers = {'Content-type': 'application/json'}
    data = '''{"index.blocks.read_only_allow_delete": false}'''
    r = requests.put(url, headers=headers, data=data)
    print(r)

def index(abspath):    
    cpt = [abspath]
    new_cpt = [x for x in cpt if x.endswith(tuple(IMAGE_FORMATS)) or x.endswith(tuple(DOC_FORMATS))]

    for path in new_cpt:
        try:
            root_tmp, ext_tmp = os.path.splitext(abspath)
            ext_tmp = ext_tmp.lower()
            md5_digest = md5_file_hasher(abspath)

            pool = Pool(processes=1)

            if ext_tmp in IMAGE_FORMATS:
                # submit task to thread pool
                async_result = pool.apply_async(func=predict, args=(abspath,)) # type list
            else:
                img_json = []

            # do some other stuff in the main process
            if ext_tmp in DOC_FORMATS or ext_tmp in IMAGE_FORMATS:
                text_content = ocr_text(abspath) # type str
            else:
                text_content = ""

            # get result from pool
            img_json = async_result.get()

            disable_readonly_mode()

            # by default we connect to localhost:9200
            es = Elasticsearch()

            # dynamic mapping
            # datetimes will be serialized
            es.index(index=ES_URL_INDEX, doc_type=ES_DOC_TYPE, body={
                    "md5_hash": md5_digest,
                    "content": text_content,
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
        print("End index\n")

def check_md5_exist(abspath):
    try:
        # by default we connect to localhost:9200
        es = Elasticsearch()
        md5_digest = md5_file_hasher(abspath)
        res = es.search(index=ES_URL_INDEX, doc_type=ES_DOC_TYPE, body={
                        "query": {
                            "match": { "md5_hash": md5_digest }
                            }
                        })
    except Exception as e:
        print(str(e) + "\n")
        print("def check_exist")
        return 0
    return res['hits']['total']

def check_path_exist(abspath):
    try:
        # by default we connect to localhost:9200
        es = Elasticsearch()
        md5_digest = md5_file_hasher(abspath)
        res = es.search(index=ES_URL_INDEX, doc_type=ES_DOC_TYPE, body={
                        "query": {
                            "match": { "path_name": abspath }
                            }
                        })
    except Exception as e:
        print(str(e) + "\n")
        print("def check_exist")
        return 0
    return res['hits']['total']

def reindex(abspath):
    # delete the info first
    # then create new one 
    unindex(abspath)
    index(abspath)

def unindex(abspath):
    # by default we connect to localhost:9200
    es = Elasticsearch()
    es.delete_by_query(index=ES_URL_INDEX, doc_type=ES_DOC_TYPE, body={
                    "query": {
                        "match": { "path_name": abspath }
                        }
                    })