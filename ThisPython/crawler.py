import os, time
from datetime import datetime
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from indexer import indexing

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
            print(str(datetime.now()) + " " + str(event))
            time.sleep(2)

            indexing(path)

            self.last_created = None

    def on_deleted(self, event):
        path = event.src_path        
        if path != self.last_deleted:
            time.sleep(2)
            print(str(datetime.now()) + " " + str(event))
            self.last_deleted = None

def start_watchdog(path):
    event_handler = TestEventHandler(patterns=["*"])
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=True)
    
    # creates a new thread
    observer.start()

    # keeps main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # does some work before the thread terminate.
        observer.stop()

    # needed to proper end a thread for "it blocks the 
    # thread in which you're making the call, until 
    # (self.observer) is finished.
    observer.join()