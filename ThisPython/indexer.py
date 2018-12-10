from datetime import datetime
from elasticsearch import Elasticsearch, ElasticsearchException
from extractor import Extractor
from pathlib import Path
from utility import Utility
import constants
import os
import requests

class Indexer(object):
    # by default we connect to localhost:9200
    es = Elasticsearch(timeout=30, max_retries=10, retry_on_timeout=True)
    
    def __init__(self):
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

    def index(self, abspath):
        abspath = Path(abspath).as_posix()
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

            ex = Extractor()
            text_content, soundex_list, img_json, _ = ex.extract(abspath)

            self.disable_readonly_mode()

            # dynamic mapping
            # datetimes will be serialized
            self.es.index(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                    "md5_hash": md5_digest,
                    "content": text_content,
                    "soundex_keyword": soundex_list,
                    "tag": img_json,
                    "file_name": os.path.basename(abspath),
                    "path_name": Path(abspath).as_posix(),
                    "retrieve_path_uri": Path(abspath).as_uri(),
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
        abspath = Path(abspath).as_posix()

        # delete the info first
        if not self.deindex(abspath):
            return False
        # then create new one 
        if not self.index(abspath):
            return False
        return True

    def deindex(self, abspath):
        abspath = Path(abspath).as_posix()
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
        abspath = Path(abspath).as_posix()
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
        abspath = Path(abspath).as_posix()
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
