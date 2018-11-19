import sys

# http://astrofrog.github.io/blog/2016/01/12/stop-writing-python-4-incompatible-code/
# Check python version before run
if sys.version_info[0] == 3:
    pass
elif sys.version_info[0] == 2:
    sys.exit(" * Sorry, requires Python 3.x, not Python 2.x\n")
else:
    sys.exit(" * Unknown Python version")

import argparse
import os
import threading
from crawler import Crawler
from frontend import flaskThread
import json
import os.path

def load_json_config():
    file = 'config.json'
    key = 'monitor_path'
    if (not os.path.exists(file)) or (os.path.getsize(file) <= 0):
        # create a default config
        config = {key: ""}
        with open(file, 'w') as f:
            json.dump(config, f)
        sys.exit(" * Please setup the configuration file \"" + file +"\" to specify the monitor path")
    else:
        with open(file, 'r') as f:
            config = json.load(f, strict=False)
        if (key not in config) or (len(config[key]) == 0) or (config[key] == None):
            sys.exit(" * Configuration file \"" + file + "\" -> " + key +": No target in given data")
        else:
            pass
    return config

if __name__ == "__main__":
    config = load_json_config()
    path = config["monitor_path"]
    if not os.path.exists(path):
        sys.exit(" * The system cannot find the path: \"" + path + "\"")
    elif not os.path.isdir(path):
        sys.exit(" * Expecting folder/directory path to index the files, but a file is given as the argument")
    else:
        pass
    
    #threading.Thread(target=Crawler.walk_dir).start()
    threading.Thread(target=flaskThread, args=[path]).start()


    try:
        crawler = Crawler(path)
        crawler.start_watchdog()
        print(" * Crawler and ElasticSearch components are ready")
    except ValueError as e:
        print(str(e))
        sys.exit(" * System total failure, quit")
    print(" * System is ready")
