from watchdog.observers import Observer
from multiprocessing import Pool
import concurrent.futures
import os
import time
import sys
from extractor import Extractor
from indexer import Indexer
from utility import Utility
from datetime import datetime

from watchdog.events import PatternMatchingEventHandler
import constants
import os
import platform
import sys
import time
from abc import ABCMeta, abstractmethod

class Crawler(metaclass=ABCMeta):
    idx = Indexer()

    @abstractmethod
    def start():
        raise NotImplementedError('This is an "abstract" method!')

class FileCrawler(Crawler):
    def __init__(self, path):
        self.extractor = Extractor()
        self.path = path

    # Walk through each files in a directory
    def walk_dir(self):
        for dirpath, dirs, files in os.walk(self.path, topdown=True):
            for filename in files:
                yield os.path.abspath(os.path.join(dirpath, filename))

    def start(self):
        Utility.print_event("Make a quick scan and index files in the path \"" + self.path + "\"")
        file_list = []

        for item in self.walk_dir():
            if Crawler.idx.check_db_md5_exist(item):
                Utility.print_event("File \"" + item + "\" exists in DB, skip.")
            elif(item.endswith(tuple(constants.IMAGE_FORMATS)) or item.endswith(tuple(constants.DOC_FORMATS))):
                file_list.append(item)
            else:
                Utility.print_event("File \"" + item + "\" not supported, skip.")

        with concurrent.futures.ProcessPoolExecutor(4) as executor: #use all available cores
            future_results = {executor.submit(self.extractor.process, item): item for item in file_list}
            for future in concurrent.futures.as_completed(future_results):
                text, soundex, tag, abspath = future.result()
                Crawler.idx.index(abspath, text, soundex, tag)
                Utility.print_event("File \"" + abspath + "\" indexed.")
                

class EventCrawler(Crawler):
    def __init__(self, path):
        self.event_handler = FileEventHandler(Crawler.idx, patterns=["*"])
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=path, recursive=True)

    # Call watchdog in main thread only. 
    # If call in seperate thread/process,
    # the watchdog may duplicate itself.
    def start(self):
        # creates a new thread
        self.observer.start()

class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, indexer, *args, **kwargs):
        super(FileEventHandler, self).__init__(*args, **kwargs)

        # event.event_type
        #     'created' | 'moved' | 'deleted'
        # event.is_directory
        #     True | False
        # event.src_path
        #     path/to/observed/file

        self.indexer = indexer

        # dont let same event(refer to same file) fire mutiple time
        self.last_file_modified = None
        self.last_file_deleted = None

    def on_modified(self, event):
        if event.is_directory:
            return
        else:
            pass

        path = event.src_path

        if not os.path.exists(path):
            self.last_file_modified = None
            Utility.print_event("File \"" + path + "\" no longer exists, probably deleted or moved.")
            return
        else:
            pass

        if path != self.last_file_modified:
            MY_OS_IS = platform.system()
            if MY_OS_IS == "Windows":
                # wait longer and hopefully the file has finish copy
                time.sleep(2)
            elif MY_OS_IS == "Linux":
                # https://stackoverflow.com/questions/32092645/python-watchdog-windows-wait-till-copy-finishes
                # just wait until the file is finished being copied, via watching the filesize.
                historicalSize = -1
                while (historicalSize != os.path.getsize(path)):
                    historicalSize = os.path.getsize(path)
                    time.sleep(1)
            else:
                sys.exit("Unsupported operating system platform, expecting Windows or Linux")

            hit_path_total = self.indexer.check_db_path_exist(path)
            hit_md5_total = self.indexer.check_db_md5_exist(path)
            if (hit_path_total >= 1) and (hit_md5_total >= 1):
                # deal with file timestamp changing
                Utility.print_event(event)
                Utility.print_event("File \"" + path + "\" exists in database, skip.")
            elif (hit_path_total >= 1) and (hit_md5_total <= 0):
                # deal with content change
                Utility.print_event(event)
                self.indexer.reindex(path)
                Utility.print_event("File \"" + path + "\" reindexed.")
            elif (hit_path_total <= 0) and (hit_md5_total <= 0):
                # deal with new file
                Utility.print_event(event)
                self.indexer.index(path)
                Utility.print_event("File \"" + path + "\" indexed.")
            else:
                # deal with moved file
                # do trigger delete event and then modified event
                pass
        else:
            pass
        self.last_file_modified = None

    def on_deleted(self, event):
        if event.is_directory:
            return
        else:
            pass

        path = event.src_path   
        
        if path != self.last_file_deleted:
            hit_path_total = self.indexer.check_db_path_exist(path)

            if (hit_path_total >= 1):
                self.print_event(event)
                self.indexer.unindex(path)
                Utility.print_event("File \"" + path + "\" deindexed.")
            else:
                Utility.print_event("File \"" + path + "\" deleted, but there is no record in database to be removed")
        else:
            pass
        self.last_file_deleted = None
