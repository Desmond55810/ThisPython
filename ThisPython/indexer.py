import os
import requests
from utility import Utility
from datetime import datetime
from elasticsearch import Elasticsearch
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool
import constants
from extractor import Extractor

class Indexer(object):
    def __init__(self):
        # by default we connect to localhost:9200
        self.es = Elasticsearch(timeout=30, max_retries=10, retry_on_timeout=True)

        self.ex = Extractor()

        # test if the elasticsearch is ok or not
        if not self.es.ping():
            raise ValueError("*** ElasticSearch connection failed ***")

        # only wait for 1 second, regardless of the client's default
        self.es.cluster.health(wait_for_status='yellow', request_timeout=1)

        # ignore 400 cause by IndexAlreadyExistsException when creating an index
        self.es.indices.create(index=constants.ES_URL_INDEX, ignore=400) 

    def disable_readonly_mode(self):
        url = 'http://localhost:9200/_all/_settings'
        headers = {'Content-type': 'application/json'}
        data = '''{"index.blocks.read_only_allow_delete": false}'''
        requests.put(url, headers=headers, data=data)

    def index(self, abspath, text_content=None, soundex_list=None, img_json=None):    
        cpt = [abspath]
        new_cpt = [x for x in cpt if x.endswith(tuple(constants.IMAGE_FORMATS)) or x.endswith(tuple(constants.DOC_FORMATS))]

        if (len(new_cpt) <= 0):
            return False

        for path in new_cpt:
            try:
                root_tmp, ext_tmp = os.path.splitext(abspath)
                ext_tmp_lower = ext_tmp.lower()
                md5_digest = Utility.hash_md5(abspath)

                if (text_content is None) or (soundex_list is None) or (img_json is None):
                    text_content, soundex_list, img_json, _ = self.ex.process(abspath)
                    del _

                self.disable_readonly_mode()

                # dynamic mapping
                # datetimes will be serialized
                self.es.index(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                        "md5_hash": md5_digest,
                        "content": text_content,
                        "soundex_keyword": soundex_list,
                        "tag": img_json,
                        "file_name": os.path.basename(path),
                        "path_name": abspath,
                        "file_type": ext_tmp,
                        "last_edit_date": datetime.now(),
                        "size_in_byte":os.path.getsize(abspath),
                    }
                )
                return True
            except OSError as e:
                print(str(e))
        return False

    def reindex(self, abspath):
        # delete the info first
        unindex(abspath)
        # then create new one 
        index(abspath)

    def unindex(self, abspath):
        self.es.delete_by_query(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                        "query": {
                            "match_phrase": { "path_name": abspath }
                            }
                        })

    def check_db_md5_exist(self, abspath):
        try:
            md5_digest = Utility.hash_md5(abspath)
            res = self.es.search(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                            "query": {
                                "match_phrase": { "md5_hash": md5_digest }
                                }
                            })
        except Exception as e:
            print(str(e))
            return 0
        return res['hits']['total']

    def check_db_path_exist(self, abspath):
        try:
            res = self.es.search(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                            "query": {
                                "match_phrase": { "path_name": abspath }
                                }
                            })
        except Exception as e:
            print(str(e))
            return 0
        return res['hits']['total']