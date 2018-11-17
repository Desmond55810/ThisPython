import sys

# http://astrofrog.github.io/blog/2016/01/12/stop-writing-python-4-incompatible-code/
# Check python version before run
if sys.version_info[0] == 3:
    pass
elif sys.version_info[0] == 2:
    sys.exit("Sorry, requires Python 3.x, not Python 2.x\n")
else:
    sys.exit("Unknown Python version")


import argparse
import os
import threading
from crawler import Crawler
from frontend import flaskThread

if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description='Description of your program')
    #parser.add_argument('-d','--directory', help='Description for directory argument', required=True)
    #args = parser.parse_args()
    #scan_dir = args.d

    #if not os.path.exists(path):
    #    sys.exit("The system cannot find the path: \"" + path + "\"")

    #if not os.path.isdir(path):
    #    sys.exit("Expecting folder/directory path to index the files, but a file is given as the argument")

    
    threading.Thread(target=flaskThread).start()

    #path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scandoc")

    try:
        crawler = Crawler()
        crawler.start_watchdog()
        print("Crawler and ElasticSearch components are ready")
    except ValueError as e:
        print(str(e))
        sys.exit("System total failure, quit")
    print("System is ready")

    #crawler.walk_dir()