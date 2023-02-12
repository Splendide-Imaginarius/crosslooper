#!/usr/bin/env python3

from pathlib import Path

from tqdm import tqdm

import crosslooper

__version__ = crosslooper.__version__
__author__ = crosslooper.__author__

def file_offset_dir(path, **ka):
  """CLI interface to save loop metadata of a directory of audio files.
  ffmpeg needs to be available.
  """

  path = Path(path)

  files = list(path.glob(f"**/*"))

  total_pbar = tqdm(unit='track')
  total_pbar.set_description('folder')
  total_pbar.reset(total=len(files))

  single_pbar = tqdm(unit='audio_sec')

  for f in files:
    crosslooper.file_offset(in1=f, pbar=single_pbar, **ka)
    total_pbar.update(1)

main = file_offset_dir
if __name__ == '__main__':
    main('./Audio/BGM')

