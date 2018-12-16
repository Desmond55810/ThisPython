from datetime import datetime
from elasticsearch import Elasticsearch, ElasticsearchException
from extractor import Extractor
from pathlib import Path
from utility import Utility
import constants
import os
import requests
from enum import Enum     # for enum34, or the stdlib version

class ProcessType(Enum):
    index = 1
    reindex = 2
    deindex = 3

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

    # process the file by index/reindex
    # if the caller need to deindex file, the caller must specify it.
    def process(self, path, process_type=ProcessType['reindex']):
        if (not os.path.exists(path)) and (process_type != ProcessType['deindex']):
            Utility.print_event("File does not exist: " + path)
            return

        if (not Utility.is_file_supported(path)) or (os.path.isdir(path)):
            Utility.print_event("File not supported: " + path)
            return

        if process_type == ProcessType['index'] or process_type == ProcessType['reindex']:
            hit_path_total = self.check_db_path_exist(path)
            hit_md5_total = self.check_db_md5_exist(path)

            if (hit_path_total >= 1) and (hit_md5_total >= 1):
                # deal with file timestamp changing
                Utility.print_event("File index exists in DB, skip: " + path)
                # what to do with duplicate files with different name?
            elif (hit_path_total >= 1) and (hit_md5_total <= 0):
                # deal with content change
                Utility.print_event("File content changed, attempt to reindex: " + path)
                if self.reindex(path, is_md5_changed=True):
                    Utility.print_event("File reindexed: " + path)
                else:
                    Utility.print_event("Fail to reindex file: " + path)
            elif (hit_path_total <= 0) and (hit_md5_total >= 1):
                # deal with path changes
                Utility.print_event("File path mismatch in DB, attempt to reindex: " + path)
                if self.reindex(path, is_md5_changed=False):
                    Utility.print_event("File reindexed: " + path)
                else:
                    Utility.print_event("Fail to reindex file: " + path)
            elif (hit_path_total <= 0) and (hit_md5_total <= 0):
                # deal with new file
                Utility.print_event("Indexing new file: " + path)
                if self.index(path):
                    Utility.print_event("File indexed: " + path)
                else:
                    Utility.print_event("Fail to index file: " + path)
            else:
                Utility.print_event("Error occur in on_modfied event: " + path)
        elif process_type == ProcessType['deindex']:
            hit_path_total = self.check_db_path_exist(path)
            if (hit_path_total >= 1):
                self.deindex(path)
                Utility.print_event("File deindexed: " + path)
            else:
                Utility.print_event("File deleted, but no record in DB to be removed: " + path)
        else:
            Utility.print_event("Error: unknown process type is used in indexer.py")

    def index(self, abspath):
        abspath = Path(abspath).as_posix()

        try:
            root_tmp, ext_tmp = os.path.splitext(abspath)
            md5_digest = Utility.hash_md5(abspath)

            ex = Extractor()

            try:
                text_content, img_json = ex.extract(abspath)
            except Exception as ex:
                Utility.print_event("Error occur when extract information: " + abspath)
                return False

            self.disable_readonly_mode()

            # dynamic mapping
            # datetimes will be serialized
            self.es.index(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, id=md5_digest, body={
                    "content": text_content,
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

    def reindex(self, abspath, is_md5_changed):
        abspath = Path(abspath).as_posix()
        if is_md5_changed:
            # delete the old info
            self.deindex(abspath)
            # then create new one 
            return self.index(abspath)
        else:
            # md5 unchanged but path changed
            try:
                root_tmp, ext_tmp = os.path.splitext(abspath)
                md5_digest = Utility.hash_md5(abspath)
                self.disable_readonly_mode()

                # partial update
                self.es.update(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, id=md5_digest, body={
                        "doc": {
                            "file_name": os.path.basename(abspath),
                            "path_name": Path(abspath).as_posix(),
                            "retrieve_path_uri": Path(abspath).as_uri(),
                            "file_type": ext_tmp,
                            "last_edit_date": datetime.now(),
                        }
                    }
                )
            except ElasticsearchException as e:
                print(str(e))
                return False
        return True

    def deindex(self, abspath):
        abspath = Path(abspath).as_posix()
        # first, remove by md5 if possible
        if os.path.exists(abspath):
            md5_digest = Utility.hash_md5(abspath)
            try:
                self.es.delete(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, ignore=[404], id=md5_digest)
            except ElasticsearchException as e:
                print(str(e))
                return False
        else:
            pass

        # then, remove by path if any
        try:
            self.es.delete_by_query(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                            "query": {
                                "match": { "path_name.keyword": abspath }
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
                                "match": { "_id": md5_digest }
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
                                "match": { "path_name.keyword": abspath }
                                }
                            })
        except ElasticsearchException as e:
            print(str(e))
            return 0
        return res['hits']['total']
