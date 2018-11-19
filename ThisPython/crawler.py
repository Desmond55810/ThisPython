from watchdog.observers import Observer
#from fileeventhandler import FileEventHandler
# from fileeventhandler import FileEventHandler
from multiprocessing import Pool
from FileEventHandler import FileEventHandler
import os
import time
import sys

class Crawler(object):
    def __init__(self, path):
        self.path = path
        self.event_handler = FileEventHandler(patterns=["*"])
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=self.path, recursive=True)

    # Walk through each files in a directory
    def walk_dir(self):

        #print("Make a quick scan and index files in the path \"" + self.path + "\"")
        #for dirpath, dirs, files in os.walk(self.path, topdown=True):
        #    for filename in files:
        #        os.path.abspath(os.path.join(dirpath, filename))
        pass

    # Call watchdog in main thread only. 
    # If call in seperate thread/process,
    # the watchdog may duplicate itself.
    def start_watchdog(self):
        # creates a new thread
        self.observer.start()
