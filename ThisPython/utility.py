from luminoth.tools.checkpoint import get_checkpoint_config
from luminoth.utils.predicting import PredictorNetwork
from PIL import Image as ImagePIL
import constants
import hashlib
import io
import os
import tesserocr
import subprocess

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

