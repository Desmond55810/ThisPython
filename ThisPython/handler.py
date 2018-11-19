from datetime import datetime
from indexer import Indexer
from watchdog.events import PatternMatchingEventHandler
import constants
import os
import platform
import sys
import time

class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(FileEventHandler, self).__init__(*args, **kwargs)

        # event.event_type
        #     'created' | 'moved' | 'deleted'
        # event.is_directory
        #     True | False
        # event.src_path
        #     path/to/observed/file

        self.indexer = Indexer()

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
            self.print_event("File \"" + path + "\" no longer exists, probably deleted or moved")
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

            if (hit_path_total >= 1) and (hit_md5_total <= 0):
                # deal with content change
                self.print_event(event)
                self.indexer.reindex(path)
                self.print_event("File \"" + path + "\" reindexed.")
            elif (hit_path_total <= 0) and (hit_md5_total <= 0):
                # deal with new file
                self.print_event(event)
                self.indexer.index(path)
                self.print_event("File \"" + path + "\" indexed.")
            else:
                # deal with file timestamp changing
                # do nothing

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
                self.print_event("File \"" + path + "\" deindexed.")
            else:
                self.print_event("File \"" + path + "\" deleted, but there is no record in database to be removed")
        else:
            pass
        self.last_file_deleted = None

    def print_event(self, event):
        print(str(datetime.now()) + " " + str(event))

    def scan_through(self, path):
        pass