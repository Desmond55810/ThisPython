from flask import Flask, render_template, request, url_for
import requests
import threading
from crawler import *

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search_result():
    if 'q' in request.values:
        search = str(request.values.get('q', 0))
        return search
    else:
        return render_template('index.html')

import asyncio

def flaskThread():
    # app.run(debug=True)
    app.run()

if __name__ == "__main__":
    threading.Thread(target=flaskThread).start()
    scandoc = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scandoc")
    start_watchdog(scandoc)
