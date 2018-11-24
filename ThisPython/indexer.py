from datetime import datetime
from elasticsearch import Elasticsearch, ElasticsearchException
from extractor import Extractor
from utility import Utility
import constants
import os
import requests

class Indexer(object):
    def __init__(self):
        # by default we connect to localhost:9200
        self.es = Elasticsearch(timeout=30, max_retries=10, retry_on_timeout=True)

        self.ex = Extractor()

        # test if the elasticsearch is ok or not
        if not self.es.ping():
            raise ValueError("*** ElasticSearch connection failed ***")

        # only wait for 10 second, regardless of the client's default
        self.es.cluster.health(wait_for_status='yellow', request_timeout=10)

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
            Utility.print_event("Ignore indexing not supported file: " + abspath)
            return False
        else:
            pass

        try:
            root_tmp, ext_tmp = os.path.splitext(abspath)
            md5_digest = Utility.hash_md5(abspath)

            if self.check_db_md5_exist(abspath):
                Utility.print_event("Ignore indexing because md5 exist: " + abspath)
                return True

            ext_tmp = "".join(ext_tmp.split("."))

            if (text_content is None) or (soundex_list is None) or (img_json is None):
                text_content, soundex_list, img_json, _ = self.ex.process(abspath)
                del _
            else:
                pass

            self.disable_readonly_mode()

            # dynamic mapping
            # datetimes will be serialized
            self.es.index(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                    "md5_hash": md5_digest,
                    "content": text_content,
                    "soundex_keyword": soundex_list,
                    "tag": img_json,
                    "file_name": os.path.basename(abspath),
                    "path_name": abspath,
                    "file_type": ext_tmp,
                    "last_edit_date": datetime.now(),
                    "size_in_byte":os.path.getsize(abspath),
                }
            )
        except ElasticsearchException as e:
            print(str(e))
            return False
        return True

    def reindex(self, abspath):
        # delete the info first
        if not self.deindex(abspath):
            return False
        # then create new one 
        if not self.index(abspath):
            return False
        return True

    def deindex(self, abspath):
        if os.path.exists(abspath):
            md5_digest = Utility.hash_md5(abspath)
            try:
                self.es.delete_by_query(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                                "query": {
                                    "term": { "md5_hash.keyword": md5_digest }
                                    }
                                })
            except ElasticsearchException as e:
                print(str(e))
                return False
        else:
            pass

        try:
            self.es.delete_by_query(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                            "query": {
                                "term": { "path_name.keyword": abspath }
                                }
                            })
        except ElasticsearchException as e:
            print(str(e))
            return False
        return True

    def check_db_md5_exist(self, abspath):
        try:
            md5_digest = Utility.hash_md5(abspath)
            res = self.es.search(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                            "query": {
                                "term": { "md5_hash.keyword": md5_digest }
                                }
                            })
        except ElasticsearchException as e:
            print(str(e))
            return 0
        return res['hits']['total']

    def check_db_path_exist(self, abspath):
        try:
            res = self.es.search(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                            "query": {
                                "term": { "path_name.keyword": abspath }
                                }
                            })
        except ElasticsearchException as e:
            print(str(e))
            return 0
        return res['hits']['total']