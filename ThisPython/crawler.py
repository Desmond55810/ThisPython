import os, time, sys
from datetime import datetime
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from indexer import index, unindex, check_path_exist, check_md5_exist, reindex
from multiprocessing import Pool

def walkdir(folder):
    """Walk through each files in a directory"""
    for dirpath, dirs, files in os.walk(folder, topdown=True):
        for filename in files:
            yield os.path.abspath(os.path.join(dirpath, filename))

class TestEventHandler(PatternMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(TestEventHandler, self).__init__(*args, **kwargs)

        # dont let same event(refer to same file) fire mutiple time
        # no longer used because failure in implement multiprocessing
        self.last_modified = None
        self.last_deleted = None

    def on_modified(self, event):
        path = event.src_path
        if path != self.last_modified:
            time.sleep(2)
            print(str(datetime.now()) + " " + str(event))
            hit_path_total = check_path_exist(path)
            hit_md5_total = check_md5_exist(path)

            if hit_path_total >= 1 and hit_md5_total <= 0:
                # deal with content change
                reindex(path)
            elif (hit_path_total <= 0 and hit_md5_total <= 0):
                # deal with new file
                index(path)
            else:
                # deal with file timestamp changing
                # do nothing

                # deal with moved file
                # do nothing
                # trigger delete event and modified event
                pass

            self.last_modified = None
        else:
            pass

    def on_deleted(self, event):
        path = event.src_path        
        if path != self.last_deleted:
            time.sleep(2)
            print(str(datetime.now()) + " " + str(event))
            unindex(path)
            self.last_deleted = None
        else:
            pass

# Call watchdog in main thread only. 
# If call in seperate thread/process,
# the watchdog may duplicate itself.
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

    print("Stop monitoring folder")

    try:   
        sys.exit(0)
    except SystemExit as e:
        print("Please quit Python manually."+"\n")
