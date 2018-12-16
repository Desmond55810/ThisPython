from abc import ABCMeta, abstractmethod
from extractor import Extractor
from indexer import Indexer, ProcessType
from pathlib import Path
from utility import Utility
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import concurrent.futures
import constants
import os
import sys
import time

# Abstract class crawler
class Crawler(metaclass=ABCMeta):
    indexer = Indexer()

    @abstractmethod
    def start():
        raise NotImplementedError('This is an "abstract" method!')

class FileCrawler(Crawler):
    def __init__(self, path, processor_count=1):
        self.extractor = Extractor()
        self.path = path
        self.processor_count = processor_count

    # Walk through each files in a directory
    def walk_dir(self):
        for dirpath, dirs, files in os.walk(self.path, topdown=True):
            for filename in files:
                yield os.path.abspath(os.path.join(dirpath, filename))
    
    # Start crawl all files in a specific directory
    # Process files on process pool
    # Caller is blocked until all files are processed
    def start(self):
        Utility.print_event("Crawl files in the directory: " + self.path)
        file_list = []

        # get only the supported file format
        for item in self.walk_dir():
            item = Path(item).as_posix()
            if Utility.is_file_supported(item):
                file_list.append(item)
            else:
                Utility.print_event("File not supported: " + item)

        if len(file_list) != 0:
            Utility.print_event("Using " + str(self.processor_count) + " processors to process files")
            counter = 0
            with concurrent.futures.ProcessPoolExecutor(self.processor_count) as executor:
                # throw all the file path list into the executor
                future_results = {executor.submit(Crawler.indexer.process, item): item for item in file_list}
                for future in concurrent.futures.as_completed(future_results):
                    counter += 1
                    percentage = counter / len(file_list)
                    Utility.print_event("Progress: " + str(counter) + "/" + str(len(file_list)) + ", " + "{0:.2f}".format(percentage*100.0) + "%")   
            Utility.print_event("All file indexes are up to date")
        else:
            Utility.print_event("The directory is empty")
                
class EventCrawler(Crawler):
    def __init__(self, path):
        self.path = path
        self.event_handler = EventHandler(Crawler.indexer, patterns=["*"])
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=path, recursive=True)

    # Call watchdog in main thread only. 
    # If call in seperate thread/process,
    # the watchdog may duplicate itself.
    def start(self):
        Utility.print_event("Event crawler is monitoring the path: " + self.path)

        # creates a new thread
        self.observer.start()

class EventHandler(PatternMatchingEventHandler):
    def __init__(self, indexer, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)
        self.indexer = indexer

    def on_modified(self, event):
        Utility.print_event(str(event))
        path = Path(event.src_path).as_posix()
        Utility.wait_until_finish_transfer(path)
        self.indexer.process(path, process_type=ProcessType['reindex'])

    def on_deleted(self, event):
        Utility.print_event(str(event))
        path = Path(event.src_path).as_posix()
        self.indexer.process(path, process_type=ProcessType['deindex'])


    def on_moved(self, event):
        Utility.print_event(str(event))
        dest_path = Path(event.dest_path).as_posix()
        # rename / move file
        self.indexer.process(dest_path, process_type=ProcessType['reindex'])
