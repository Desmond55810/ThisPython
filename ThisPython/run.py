import sys

# http://astrofrog.github.io/blog/2016/01/12/stop-writing-python-4-incompatible-code/
# Check python version before run
if sys.version_info[0] == 3:
    pass
elif sys.version_info[0] == 2:
    sys.exit(" * Sorry, requires Python 3.x, not Python 2.x\n")
else:
    sys.exit(" * Unknown Python version")

from crawler import Crawler, EventCrawler, FileCrawler
from elasticsearch import Elasticsearch
from indexer import Indexer
from pathlib import Path
import frontend
import json
import os
import platform
import shutil
import threading
import time

def load_json_config():
    file = 'config.json'
    path_key = 'monitor_path'
    processor_key = "processor_count"
    if (not os.path.exists(file)) or (os.path.getsize(file) <= 0):
        # create a default config if not exist
        config = {path_key: "C:/ThisIsExamplePath/UsePosixPathForwardSlash/YourDocumentsDirectory", processor_key: "2"}
        with open(file, 'w') as f:
            json.dump(config, f)
        sys.exit(" ! Please configurate the config.json")
    else:
        with open(file, 'r') as f:
            config = json.load(f, strict=False)
        if (path_key not in config) or (len(config[path_key]) == 0) or (config[path_key] == None):
            sys.exit(" ! config.json -> " + path_key +": No target in given data")
        elif (processor_key not in config) or (len(config[processor_key]) == 0) or (config[processor_key] == None):
            sys.exit(" ! config.json -> " + processor_key +": No target in given data")
        else:
            pass
    return config

# check if dependency programs are working
def check_programs():
    MY_OS_IS = platform.system()

    # check poppler program
    try:
        if (MY_OS_IS == "Linux"):
            has_file = shutil.which("pdftoppm")
        elif (MY_OS_IS == "Windows"):
            has_file = shutil.which("poppler/pdftoppm.exe")
        else:
            sys.exit(" ! Unsupported operating system platform, expecting Windows or Linux")

        if has_file:
            print(' * Found pdftoppm')
        else:
            sys.exit(" ! Cannot find pdftoppm, please install Poppler (In ubuntu, sudo apt install poppler-utils)");
    except shutil.Error as e:
        print(str(e))
        sys.exit()

    # TODO: check tesseract-ocr program
    # sudo apt install tesseract-ocr libtesseract-dev libleptonica-dev

    # check elasticseach program
    es = Indexer.es.ping()

    if es:
        print(' * Connected to Elasticsearch')
    else:
        sys.exit(' ! Not connected to Elasticsearch')
        

if __name__ == "__main__":
    check_programs()

    config = load_json_config()

    path = config["monitor_path"]
    path = Path(path).as_posix()

    processor_count = int(config["processor_count"])

    if not os.path.exists(path):
        sys.exit(" ! The system cannot find the path: " + path)
    elif not os.path.isdir(path):
        sys.exit(" ! Expecting folder/directory path, but a file path is given in the config.json: " + path)

    try:
        file_crawler = FileCrawler(path, processor_count)
        event_crawler = EventCrawler(path)
        print(" * Crawler and ElasticSearch components are ready")
    except ValueError as e:
        print(str(e))
        sys.exit(" ! System total failure, quit")

    file_crawler.start() # wait for file crawler crawl all files and process them
    event_crawler.start() # then start the event crawler, so this avoid conflict

    threading.Thread(target=frontend.startFlask).start() # go live
    # frontend.startFlask(debug=True) # risk of multiple file watchdogs are running when in debug mode

    print(" * System is ready")

    # keep main thread alive?
    while True:
        time.sleep(1)