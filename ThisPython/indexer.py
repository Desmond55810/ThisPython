import os
import requests
from utility import Utility
from datetime import datetime
from elasticsearch import Elasticsearch
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool
import constants

class Indexer(object):
    def __init__(self):
        # by default we connect to localhost:9200
        self.es = Elasticsearch()

        # test if the elasticsearch is ok or not
        if not self.es.ping():
            raise ValueError("ElasticSearch connection failed")

        # ignore 400 cause by IndexAlreadyExistsException when creating an index
        self.es.indices.create(index=constants.ES_URL_INDEX, ignore=400)

    def disable_readonly_mode(self):
        url = 'http://localhost:9200/_all/_settings'
        headers = {'Content-type': 'application/json'}
        data = '''{"index.blocks.read_only_allow_delete": false}'''
        requests.put(url, headers=headers, data=data)

    def index(self, abspath):    
        cpt = [abspath]
        new_cpt = [x for x in cpt if x.endswith(tuple(constants.IMAGE_FORMATS)) or x.endswith(tuple(constants.DOC_FORMATS))]

        for path in new_cpt:
            try:
                root_tmp, ext_tmp = os.path.splitext(abspath)
                ext_tmp_lower = ext_tmp.lower()
                md5_digest = Utility.hash_md5(abspath)

                pool = Pool(processes=1)

                if ext_tmp_lower in constants.IMAGE_FORMATS:
                    # submit task to thread pool
                    async_result = pool.apply_async(func=Utility.img_predict, args=(abspath,)) # type list
                else:
                    img_json = []

                # do some other stuff in the main process
                if ext_tmp_lower in constants.DOC_FORMATS or ext_tmp in constants.IMAGE_FORMATS:
                    text_content = Utility.ocr_text(abspath) # type str
                else:
                    text_content = ""

                # get result from pool
                img_json = async_result.get()

                self.disable_readonly_mode()

                # dynamic mapping
                # datetimes will be serialized
                self.es.index(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
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
                print(str(e))

    def reindex(self, abspath):
        # delete the info first
        unindex(abspath)
        # then create new one 
        index(abspath)

    def unindex(self, abspath):
        self.es.delete_by_query(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                        "query": {
                            "match": { "path_name": abspath }
                            }
                        })

    def check_db_md5_exist(self, abspath):
        try:
            md5_digest = Utility.hash_md5(abspath)
            res = self.es.search(index=ES_URL_INDEX, doc_type=ES_DOC_TYPE, body={
                            "query": {
                                "match": { "md5_hash": md5_digest }
                                }
                            })
        except Exception as e:
            return 0
        return res['hits']['total']

    def check_db_path_exist(self, abspath):
        try:
            res = self.es.search(index=ES_URL_INDEX, doc_type=ES_DOC_TYPE, body={
                            "query": {
                                "match": { "path_name": abspath }
                                }
                            })
        except Exception as e:
            return 0
        return res['hits']['total']