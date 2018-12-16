import hashlib
import time
import constants
import platform
import os

class Utility(object):
    @staticmethod
    def hash_md5(abspath):
        # BUF_SIZE is totally arbitrary, change for your app!
        BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

        md5_tool = hashlib.md5()
        
        with open(file=abspath, mode='rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                md5_tool.update(data)

        return md5_tool.hexdigest()

    @staticmethod
    def print_event(event):
        print(str(time.strftime("%Y-%m-%d %H:%M")) + " " + str(event))

    @staticmethod
    def is_file_supported(path):
        return (path.endswith(tuple(constants.IMAGE_FORMATS)) or path.endswith(tuple(constants.DOC_FORMATS)))

    @staticmethod
    def wait_until_finish_transfer(path):
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
            pass
