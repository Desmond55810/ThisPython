import sys

# http://astrofrog.github.io/blog/2016/01/12/stop-writing-python-4-incompatible-code/
# Check python version before run
if sys.version_info[0] == 3:
    pass
elif sys.version_info[0] == 2:
    sys.exit(" * Sorry, requires Python 3.x, not Python 2.x\n")
else:
    sys.exit(" * Unknown Python version")

from crawler import Crawler, EventCrawler, DirectoryCrawler
from elasticsearch import Elasticsearch
from frontend import flaskThread
import json
import os
import platform
import shutil
import threading
import time

def load_json_config():
    file = 'config.json'
    key = 'monitor_path'
    if (not os.path.exists(file)) or (os.path.getsize(file) <= 0):
        # create a default config
        config = {key: ""}
        with open(file, 'w') as f:
            json.dump(config, f)
        sys.exit(" ! Please setup the config.json to specify the monitor directory")
    else:
        with open(file, 'r') as f:
            config = json.load(f, strict=False)
        if (key not in config) or (len(config[key]) == 0) or (config[key] == None):
            sys.exit(" ! config.json -> " + key +": No target in given data")
        else:
            pass
    return config

def check_programs():
    MY_OS_IS = platform.system()

    # pdf to image
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
            sys.exit(" ! Cannot find pdftoppm, please install Poppler");
    except shutil.Error as e:
        print(str(e))
        sys.exit()

    # elasticseach
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}]).ping()
    if es:
        print(' * Connected to Elasticsearch')
    else:
        sys.exit(' ! Not connected to Elasticsearch')

if __name__ == "__main__":
    
    check_programs()
    config = load_json_config()
    path = config["monitor_path"]
    if not os.path.exists(path):
        sys.exit(" ! The system cannot find the path: \"" + path + "\"")
    elif not os.path.isdir(path):
        sys.exit(" ! Expecting folder/directory path, but a file path is given as the argument: " + path)
    else:
        pass
    
    threading.Thread(target=flaskThread, args=[path]).start()

    time.sleep(2) # wait flask to start

    try:
        event_crawler = EventCrawler(path)
        directory_crawler = DirectoryCrawler(path)
        print(" * Crawler and ElasticSearch components are ready")
    except ValueError as e:
        print(str(e))
        sys.exit(" ! System total failure, quit")
    print(" * System is ready")

    event_crawler.start()
    directory_crawler.start()