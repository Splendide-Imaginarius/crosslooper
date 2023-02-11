#!/usr/bin/env python3

from pathlib import Path

import crosslooper

__version__ = crosslooper.__version__
__author__ = crosslooper.__author__

def file_offset_dir(path, **ka):
  """CLI interface to save loop metadata of a directory of audio files.
  ffmpeg needs to be available.
  """

  path = Path(path)

  files = path.glob(f"**/*")

  for f in files:
    crosslooper.file_offset(in1=f, **ka)

main = file_offset_dir
if __name__ == '__main__':
    main('./Audio/BGM')

