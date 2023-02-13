#!/usr/bin/env python3

from multiprocessing import Process, Queue, Lock
import os
from pathlib import Path

from tqdm import tqdm

import crosslooper

__version__ = crosslooper.__version__
__author__ = crosslooper.__author__

def loop_process_run(input_file_queue, progress_queue, pbar_lock, process_num, ka):
  tqdm.set_lock(pbar_lock)
  single_pbar = tqdm(unit='audio_sec', position=process_num+1)

  while(True):
    finished, f = input_file_queue.get()
    if finished:
      break

    crosslooper.file_offset(in1=f, pbar=single_pbar, **ka)

    progress_queue.put(1)

def file_offset_dir(path, **ka):
  """CLI interface to save loop metadata of a directory of audio files.
  ffmpeg needs to be available.
  """

  path = Path(path)

  files = list(path.glob(f"**/*"))

  pbar_lock = Lock()
  tqdm.set_lock(pbar_lock)

  total_pbar = tqdm(unit='track', position=0)
  total_pbar.set_description('folder')
  total_pbar.reset(total=len(files))

  input_file_queue = Queue()

  process_num = os.cpu_count()

  progress_queue = Queue()

  loop_processes = []
  for p in range(process_num):
    loop_processes.append(Process(target=loop_process_run, args=(input_file_queue, progress_queue, pbar_lock, p, ka)))

  for p in loop_processes:
    p.start()

  for f in files:
    input_file_queue.put((False, f))

  for f in files:
    progress_queue.get()
    total_pbar.update(1)

  for p in loop_processes:
    input_file_queue.put((True, None))

main = file_offset_dir
if __name__ == '__main__':
    main('./Audio/BGM')

