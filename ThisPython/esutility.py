import requests
from datetime import datetime
from elasticsearch import Elasticsearch

def disable_readonly_mode():
    url = 'http://localhost:9200/_all/_settings'
    headers = {'Content-type': 'application/json'}
    data = '''{"index.blocks.read_only_allow_delete": false}'''
    r = requests.put(url, headers=headers, data=data)
    print(r)

def create_data(md5, content, file_name, path_name, file_type):
    if not (isinstance(md5, str) and isinstance(file_name, str) and isinstance(path_name, str) and isinstance(file_type, str)):
        raise Exception()

    # by default we connect to localhost:9200
    es = Elasticsearch()

    disable_readonly_mode()

    # create an index in elasticsearch, ignore status code 400 (index already exists)
    print(es.indices.create(index='documents', ignore=400))

    # datetimes will be serialized
    es.index(index="documents", doc_type="_doc", body={
            "md5_hash": md5,
            "content": content,
            "file_name": file_name,
            "path_name": path_name,
            "file_type": file_type,
            "last_edit_date": datetime.now()
        }
    )