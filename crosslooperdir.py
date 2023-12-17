#!/usr/bin/env python3

import configparser
from copy import deepcopy
import json
from multiprocessing import Process, Queue, Lock
import os
from pathlib import Path
import re
# tomllib is Python 3.11+ only; import a compat shim for older Pythons.
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from tqdm import tqdm
import find_engine

import crosslooper
import crosslooperpresets

__version__ = crosslooper.__version__
__author__ = crosslooper.__author__


def cli_parser(**ka):
    parser = crosslooper.cli_parser(**ka)

    if 'in-dir' not in ka:
        parser.add_argument(
            '--in-dir',
            dest='in-dir',
            action='store',
            default=None,
            type=str,
            help='Directory containing audio files to loop. ' +
                 '(default: detect based on game engine)')
    if 'preset-conf' not in ka:
        parser.add_argument(
            '--preset-conf',
            dest='preset-conf',
            action='store',
            default=None,
            type=str,
            help='TOML file containing presets for looping audio files. ' +
                 '(default: use game title)')
    if 'game-title' not in ka:
        parser.add_argument(
            '--game-title',
            dest='game-title',
            action='store',
            default=None,
            type=str,
            help='Title of game, used to find presets. ' +
                 '(default: detect based on game engine)')
    if 'game-dir' not in ka:
        parser.add_argument(
            '--game-dir',
            dest='game-dir',
            action='store',
            default='.',
            type=str,
            help='Directory containing game files. ' +
                 '(default: current working directory)')
    if 'game-engine' not in ka:
        parser.add_argument(
            '--game-engine',
            dest='game-engine',
            action='store',
            default=None,
            type=str,
            help='Game engine family, e.g. "RPG Maker". ' +
                 '(default: auto-detect)')
    if 'game-engine-ver' not in ka:
        parser.add_argument(
            '--game-engine-ver',
            dest='game-engine-ver',
            action='store',
            default=None,
            type=str,
            help='Game engine version, e.g. "VX Ace". ' +
                 '(default: auto-detect)')
    if 'threads' not in ka:
        parser.add_argument(
            '--threads',
            dest='threads',
            action='store',
            default=None,
            type=int,
            help='Number of threads to use. ' +
                 '(default: use all hardware threads)')

    return parser


def loop_process_run(input_file_queue, progress_queue, pbar_lock, process_num,
                     ka, presets):
    tqdm.set_lock(pbar_lock)
    single_pbar = tqdm(unit='audio_sec', position=process_num+1)

    while True:
        finished, f = input_file_queue.get()
        if finished:
            break

        this_ka = deepcopy(ka)
        this_ka['in1'] = f

        for preset_name in presets:
            if preset_name in f.stem.lower():
                this_ka.update(presets[preset_name])
                break

        crosslooper.file_offset(use_argparse=False, pbar=single_pbar,
                                **this_ka)

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

    # Validate game dir
    gamedir = ka['game-dir']
    gamedir = Path(gamedir)
    gamedir = gamedir.resolve()
    if not gamedir.exists():
        raise Exception(f'Folder "{gamedir}" does not exist.')
    if gamedir.is_file():
        raise Exception(f'Folder "{gamedir}" is a file.')

    # Validate game engine if doing so is needed
    indir = ka['in-dir']
    gametitle = ka['game-title']
    if indir is None or gametitle is None:
        gameengine = ka['game-engine']
        gameenginever = ka['game-engine-ver']
        detected_gameengine = None
        detected_gameenginever = None
        if gameengine is None:
            gameengine, detected_gameenginever = find_engine.detect(gamedir)
            if gameengine is None:
                raise Exception('Unrecognized engine')
            if gameenginever is None:
                gameenginever = detected_gameenginever
        if gameengine.lower() == 'RPG Maker'.lower():
            if gameenginever is None:
                detected_gameengine, gameenginever = find_engine.detect(gamedir)
                if gameenginever is None:
                    raise Exception('Unrecognized RPG Maker version')
            if gameenginever.lower() in ['VX Ace'.lower(),
                                         'VX'.lower(),
                                         'XP'.lower()]:
                gameengine, gameenginever = 'RPG Maker', 'VX Ace'
            elif gameenginever.lower().startswith(('MV'.lower(),
                                                   'MZ'.lower())):
                gameengine, gameenginever = 'RPG Maker', 'MV'
            else:
                raise Exception(f'Unsupported RPG Maker version "{gameenginever}"')
        elif gameengine.lower() == 'mkxp'.lower():
            gameengine, gameenginever = 'RPG Maker', 'VX Ace'
        else:
            raise Exception(f'Unsupported engine "{gameengine}"')

    # Validate BGM dir
    if indir is None:
        if gameenginever == 'VX Ace':
            # RGSS
            indir = gamedir / 'Audio' / 'BGM'
        elif gameenginever == 'MV':
            # NW.js
            packagejson = gamedir / 'package.json'
            with open(packagejson, 'r') as packagejsonfile:
                packagejsondata = json.load(packagejsonfile)
            indexhtml = gamedir / packagejsondata['main']
            indir = indexhtml.parent / 'audio' / 'bgm'
        else:
            raise Exception(f'Failed to guess BGM dir for {gameenginever}')
    else:
        indir = Path(indir)
    indir = indir.resolve()
    if not indir.exists():
        raise Exception(f'Folder "{indir}" does not exist.')
    if indir.is_file():
        raise Exception(f'Folder "{indir}" is a file.')

    files = list(indir.glob("**/*"))

    pbar_lock = Lock()
    tqdm.set_lock(pbar_lock)

    presets = {}
    presetconf = ka['preset-conf']
    presets_tmp = {}

    # Detect game title
    if gametitle is None:
        if gameenginever == 'VX Ace':
            # RGSS
            inipaths = gamedir.glob('*.ini')

            for i in inipaths:
                gameini = configparser.ConfigParser()
                try:
                    gameini.read(i)
                except UnicodeDecodeError:
                    # Workaround for Japanese games
                    gameini.read(i, encoding='shift_jis')
                if 'Game' in gameini and 'Title' in gameini['Game']:
                    gametitle = gameini['Game']['Title']
                    break
        elif gameenginever == 'MV':
            # NW.js
            with open(indexhtml, 'r') as htmlfile:
                htmldata = htmlfile.read()
                htmlmatch = re.search(r'<title>(.*)</title>', htmldata)
                if htmlmatch is not None:
                    gametitle = htmlmatch.group(1)
    if gametitle is None:
        raise Exception('Failed to detect game title')

    total_pbar = tqdm(unit='track', position=0)
    total_pbar.set_description('folder' if gametitle is None else gametitle)
    total_pbar.reset(total=len(files))

    # Find preset file for game title
    if presetconf is None and gametitle is not None:
        presetconf = crosslooperpresets.get_preset(gametitle)
        if presetconf is None:
            raise Exception(f'Preset not found for "{gametitle}"')

    # Open preset file
    if presetconf is not None:
        with open(presetconf, "rb") as f:
            presets_tmp = tomllib.load(f)

    # Validate preset file
    for trackname in presets_tmp:
        trackname_l = trackname.lower()
        presets[trackname_l] = {}
        for option in presets_tmp[trackname]:
            option_l = option.lower()
            if option_l not in ['normalize', 'denoise', 'lowpass',
                                'loop-start-min', 'loop-start-max',
                                'loop-end-min', 'loop-len-min',
                                'loop-search-step', 'loop-search-len',
                                'loop-force', 'skip']:
                raise Exception(f'Unknown TOML option: {option}')
            presets[trackname_l][option_l] = presets_tmp[trackname][option]

    input_file_queue = Queue()

    process_num = ka['threads']
    if process_num is None:
        process_num = os.cpu_count()
    process_num = min([process_num, len(files)])

    progress_queue = Queue()

    loop_processes = []
    for p in range(process_num):
        loop_processes.append(Process(target=loop_process_run,
                                      args=(input_file_queue,
                                            progress_queue,
                                            pbar_lock,
                                            p,
                                            ka,
                                            presets)))

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
