import os, time, sys
from datetime import datetime
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from indexer import indexing
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
        self.last_created = None
        self.last_modified = None
        self.last_deleted = None

        #use all available cores
        self.crawler_pool = Pool()

    def on_created(self, event):
        path = event.src_path        
        if path != self.last_created:
            print(str(datetime.now()) + " " + str(event))
            time.sleep(2) # wait file finish copy
            self.crawler_pool.apply_async(func=indexing, args=(path,)) # submit task to pool
            self.last_created = None

    def on_modified(self, event):
        path = event.src_path
        print(str(datetime.now()) + " " + str(event))
        if path != self.last_modified:
            # file not found in database?
            # probably new file, ignore it
            # let on_created event handler it


            # file has been index before
            # reindex the file
            self.last_modified = None

    def on_deleted(self, event):
        path = event.src_path        
        if path != self.last_deleted:
            time.sleep(2)
            print(str(datetime.now()) + " " + str(event))
            self.last_deleted = None

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
