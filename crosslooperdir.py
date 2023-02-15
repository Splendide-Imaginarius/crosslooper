#!/usr/bin/env python3

from copy import deepcopy
from multiprocessing import Process, Queue, Lock
import os
from pathlib import Path
# tomllib is Python 3.11+ only; import a compat shim for older Pythons.
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from tqdm import tqdm

import crosslooper

__version__ = crosslooper.__version__
__author__ = crosslooper.__author__

def cli_parser(**ka):
  parser = crosslooper.cli_parser(**ka)

  if 'indir' not in ka:
    parser.add_argument(
      '--indir',
      dest='indir',
      action='store',
      default='Audio/BGM',
      type=str,
      help="Directory containing audio files to loop. (default: 'Audio/BGM')")
  if 'presetconf' not in ka:
    parser.add_argument(
      '--presetconf',
      dest='presetconf',
      action='store',
      default=None,
      type=str,
      help="TOML file containing presets for looping audio files. (default: no presets)")
  if 'threads' not in ka:
    parser.add_argument(
      '--threads',
      dest='threads',
      action='store',
      default=None,
      type=int,
      help="Number of threads to use. (default: use all hardware threads)")

  return parser

def loop_process_run(input_file_queue, progress_queue, pbar_lock, process_num, ka, presets):
  tqdm.set_lock(pbar_lock)
  single_pbar = tqdm(unit='audio_sec', position=process_num+1)

  while(True):
    finished, f = input_file_queue.get()
    if finished:
      break

    this_ka = deepcopy(ka)
    this_ka['in1'] = f

    for preset_name in presets:
      if preset_name in f.stem.lower():
        this_ka.update(presets[preset_name])
        break

    crosslooper.file_offset(use_argparse=False, pbar=single_pbar, **this_ka)

    progress_queue.put(1)

def file_offset_dir(**ka):
  """CLI interface to save loop metadata of a directory of audio files.
  ffmpeg needs to be available.
  """

  ka['in1'] = None
  ka['in2'] = None

  parser = cli_parser(**ka)
  args = parser.parse_args().__dict__
  ka.update(args)

  path = ka['indir']
  path = Path(path)
  path = path.resolve()
  if not path.exists():
    raise Exception(f'Folder "{path}" does not exist.')
  if path.is_file():
    raise Exception(f'Folder "{path}" is a file.')

  files = list(path.glob(f"**/*"))

  pbar_lock = Lock()
  tqdm.set_lock(pbar_lock)

  total_pbar = tqdm(unit='track', position=0)
  total_pbar.set_description('folder')
  total_pbar.reset(total=len(files))

  presets = {}
  presetconf = ka['presetconf']
  presets_tmp = {}
  if presetconf is not None:
    with open(presetconf, "rb") as f:
      presets_tmp = tomllib.load(f)
  for trackname in presets_tmp:
    presets[trackname.lower()] = {}
    for option in presets_tmp[trackname]:
      if not option.lower() in ['normalize', 'denoise', 'lowpass', 'loopstart', 'loopstartmax', 'loopendmin', 'looplenmin', 'loopsearchstep', 'loopsearchlen', 'loopforce', 'skip']:
        raise Exception(f'Unknown TOML option: {option}')
      presets[trackname.lower()][option.lower()] = presets_tmp[trackname][option]

  input_file_queue = Queue()

  process_num = ka['threads']
  if process_num is None:
    process_num = os.cpu_count()

  progress_queue = Queue()

  loop_processes = []
  for p in range(process_num):
    loop_processes.append(Process(target=loop_process_run, args=(input_file_queue, progress_queue, pbar_lock, p, ka, presets)))

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
    main()

