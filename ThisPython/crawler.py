from abc import ABCMeta, abstractmethod
from extractor import Extractor
from indexer import Indexer
from pathlib import Path
from utility import Utility
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import concurrent.futures
import constants
import os
import platform
import sys
import time

class Crawler(metaclass=ABCMeta):
    indexer = Indexer()

    @abstractmethod
    def start():
        raise NotImplementedError('This is an "abstract" method!')

class FileCrawler(Crawler):
    processor_count = 1

    def __init__(self, path):
        self.extractor = Extractor()
        self.path = path

    # Walk through each files in a directory
    def walk_dir(self):
        for dirpath, dirs, files in os.walk(self.path, topdown=True):
            for filename in files:
                yield os.path.abspath(os.path.join(dirpath, filename))

    def start(self):
        Utility.print_event("Index files in the directory: \"" + self.path + "\"")
        file_list = []
        for item in self.walk_dir():
            item = Path(item).as_posix()
            if Crawler.indexer.check_db_md5_exist(item):
                if Crawler.indexer.check_db_path_exist(item):
                    Utility.print_event("File exists in DB, skip: \"" + item + "\"")
                else:
                    Utility.print_event("File path mismatch in DB, reindex: \"" + item + "\"")
                    Crawler.indexer.deindex(item)
                    file_list.append(item) 
            elif(item.endswith(tuple(constants.IMAGE_FORMATS)) or item.endswith(tuple(constants.DOC_FORMATS))):
                # supported file
                file_list.append(item)
            else:
                Utility.print_event("File not supported: \"" + item + "\"")

        if len(file_list) != 0:

            with concurrent.futures.ProcessPoolExecutor(self.processor_count) as executor:
                # throw all the path list into the executor
                future_results = {executor.submit(Crawler.indexer.index, item): item for item in file_list}

                successCount = 0
                failCount = 0

                for future in concurrent.futures.as_completed(future_results):
                    if future.result():
                        successCount += 1
                    else:
                        failCount += 1
                Utility.print_event("Finish indexing " + str(successCount) + " files, fail to index " + str(failCount) + " files")
        else:
            Utility.print_event("All files index are up to date")
                

class EventCrawler(Crawler):
    def __init__(self, path):
        self.event_handler = EventHandler(Crawler.indexer, patterns=["*"])
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=path, recursive=True)

    # Call watchdog in main thread only. 
    # If call in seperate thread/process,
    # the watchdog may duplicate itself.
    def start(self):
        # creates a new thread
        self.observer.start()

class EventHandler(PatternMatchingEventHandler):
    def __init__(self, indexer, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)

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
        path = Path(event.src_path).as_posix()
        evmsg = str(event)

        if os.path.isdir(path):
            Utility.print_event("Path is directory, skip: \"" + path + "\"")
            self.last_file_modified = None
            return
        else:
            pass

        if not os.path.exists(path):
            self.last_file_modified = None
            Utility.print_event("File no longer exists: \"" + path + "\"")
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
                Utility.print_event(evmsg)
                Utility.print_event("File exists in DB: \"" + path + "\"")
            elif (hit_path_total >= 1) and (hit_md5_total <= 0):
                # deal with content change
                Utility.print_event(evmsg)
                if self.indexer.reindex(path):
                    Utility.print_event("File reindexed: \"" + path + "\"")
            elif (hit_path_total <= 0) and (hit_md5_total <= 0):
                # deal with new file
                Utility.print_event(evmsg)
                if self.indexer.index(path):
                    Utility.print_event("File indexed: \"" + path + "\"")
            else:
                pass
        else:
            pass
        self.last_file_modified = None

    def on_deleted(self, event):
        path = Path(event.src_path).as_posix()
        evmsg = str(event)
        if os.path.isdir(path):
            Utility.print_event("Path is directory, skip: \"" + path + "\"")
            self.last_file_deleted = None
            return
        else:
            pass
        
        if path != self.last_file_deleted:
            hit_path_total = self.indexer.check_db_path_exist(path)
            Utility.print_event(evmsg)
            if (hit_path_total >= 1):
                self.indexer.deindex(path)
                Utility.print_event("File deindexed: \"" + path + "\"")
            else:
                Utility.print_event("File deleted, but no record in DB to be removed: \"" + path + "\"")
        else:
            pass
        self.last_file_deleted = None

    def on_moved(self, event):
        src_path = Path(event.src_path).as_posix()
        dest_path = Path(event.dest_path).as_posix()
        evmsg = str(event)

        # renamed / moved
        if src_path != dest_path:
            Utility.print_event(evmsg)
            if os.path.isdir(dest_path):
                directory_crawler = FileCrawler(dest_path)
                directory_crawler.start()
            else:
                self.indexer.deindex(src_path)
                self.indexer.index(dest_path)
        else:
            pass
