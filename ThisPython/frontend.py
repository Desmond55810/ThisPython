from flask import Flask, render_template, request
from elasticsearch import Elasticsearch
from indexer import Indexer
import constants
import json
import math
import time
from datetime import datetime

app = Flask(__name__)

# start the python flask web
# permenant blocking call, never return to caller
def startFlask(debug=False):
    if debug:
        app.run(debug=True) # use debug mode only when flask is started in the main thread
    else:
        app.run(host='0.0.0.0') # bind flask to all available network

# custom datetime filter for flask
def format_datetime(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d')

app.jinja_env.filters['datetime'] = format_datetime

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search_result():
    if 'q' in request.values:
        keywords = str(request.values.get('q', 0))

        if 'pageno' in request.values:
            pageno = int(request.values.get('pageno', 0))

            # prevent underflow of page no
            if pageno <= 0:
                pageno = 1
        else:
            pageno = 1

        size_per_page = 10
        start_from = (pageno - 1) * size_per_page

        start_time = time.time()
        result = Indexer.es.search(index=constants.ES_URL_INDEX, doc_type=constants.ES_DOC_TYPE, body={
                    "from" : start_from, "size" : size_per_page,
                    "_source": ["tag", "file_name", "retrieve_path_uri", "file_type", "size_in_byte", "last_edit_date"],
                    "query" : {
                            "multi_match" : {
                            "query":    keywords, 
                            "fields": [ "content", "tag.label" ] 
                        }
                    },
                    "highlight" : {
                        "fields" : {
                            "content" : {}
                        }
                    }
            })
        elapsed_time = time.time() - start_time # calculate time taken to query

        result = json.dumps(result)
        result = result.replace('<em>', '<strong>') # bold
        result = result.replace('</em>', '</strong>')
        result = result.replace('\n', '<br\>') # HTML break line
        result = json.loads(result)

        total_page = math.ceil(int(result['hits']['total']) / size_per_page)

        # limit the pagination
        if total_page >= 10:
            total_page = 10

        img_format = constants.IMAGE_FORMATS
        doc_format = constants.DOC_FORMATS

        return render_template('search.html', q=keywords, result=result, total_page=total_page, pageno=pageno, elapsed_time="{0:.3f}".format(elapsed_time), img_format=img_format, doc_format=doc_format)
    else:
        return render_template('index.html')