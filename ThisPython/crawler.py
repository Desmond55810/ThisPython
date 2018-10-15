from watchdog import *
from watchdog.events import *
import os
import sys
import time
import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

from ocrutility import *

def craw_dir(pathname):
    abs_path_list = []
    for root, dirs, files in os.walk(pathname, topdown=True):
        for file in files:
            abs_path = os.path.join(root, file) # combine path and filename
            abs_path_list.append(abs_path)
    return abs_path_list


def walkdir(folder):
    """Walk through each files in a directory"""
    for dirpath, dirs, files in os.walk(folder):
        for filename in files:
            yield os.path.abspath(os.path.join(dirpath, filename))

class TestEventHandler(PatternMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(TestEventHandler, self).__init__(*args, **kwargs)
        self.last_created = None
        self.last_deleted = None

    def on_created(self, event):
        path = event.src_path        
        if path != self.last_created:
            print("str(datetime.datetime.now())" + " " + str(event))
            time.sleep(2)
            import ocrutility

            ocrutilityX(path)

            self.last_created = None

    def on_deleted(self, event):
        path = event.src_path        
        if path != self.last_deleted:
            time.sleep(2)
            print("str(datetime.datetime.now())" + " " + str(event))
            self.last_deleted = None

def start_watchdog(path):
    event_handler = TestEventHandler(patterns=["*"])
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()