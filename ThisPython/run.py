import argparse
import os
import threading
from crawler import start_watchdog
from frontend import flaskThread

if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description='Description of your program')
    #parser.add_argument('-d','--directory', help='Description for directory argument', required=True)
    #args = parser.parse_args()
    #scan_dir = args.d

    threading.Thread(target=flaskThread).start()
    scandoc = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scandoc")
    start_watchdog(scandoc)
