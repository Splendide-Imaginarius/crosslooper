#!/usr/bin/env python3

import matplotlib
from matplotlib import pyplot as plt
import numpy as np
from scipy import fft
from scipy.io import wavfile
import tempfile
import math
import pathlib
import subprocess
import mutagen
from mutagen import ogg, flac
from tqdm import tqdm

matplotlib.use('TkAgg')

__version__ = "1.0.1"
__author__ = """Splendide Imaginarius"""

# Globals
ax = None
take = None
normalize = False
denoise = False
lowpass = 0
samples = False
loop = True
loopstart = 5
loopstartmax = None
loopendmin = 20.0
looplenmin = 0.0
loopsearchstep = 1.0
loopsearchlen = 5.0
loopforce = False
skip = False
verbose = False

ffmpegwav = 'ffmpeg -i "{}" %s -c:a pcm_s16le -map 0:a "{}"'
ffmpegnormalize = ('ffmpeg -y -nostdin -i "{}" -filter_complex ' +
                   "'[0:0]loudnorm=i=-23.0:lra=7.0:tp=-2.0:offset=4.45:" +
                   "linear=true:print_format=json[norm0]' " +
                   "-map_metadata 0 -map_metadata:s:a:0 0:s:a:0 " +
                   "-map_chapters 0 -c:v copy -map '[norm0]' " +
                   '-c:a:0 pcm_s16le -c:s copy "{}"')
ffmpegdenoise = 'ffmpeg -i "{}" -af'+" 'afftdn=nf=-25' "+'"{}"'
ffmpeglow = 'ffmpeg -i "{}" -af'+" 'lowpass=f=%s' "+'"{}"'


def o(x):
    return '%s%s' % (x, '.wav')


def print_maybe(*s, **ka):
    if verbose:
        print(*s, **ka)


def in_out(command, infile, outfile):
    hdr = '-'*len(command)
    print_maybe("%s\n%s\n%s" % (hdr, command, hdr))
    subprocess.check_call(command.format(infile, outfile),
                          stdout=(None if verbose else subprocess.DEVNULL),
                          stderr=(None if verbose else subprocess.DEVNULL))


def normalize_denoise(infile, outname):
    with tempfile.TemporaryDirectory() as tempdir:
        outfile = o(pathlib.Path(tempdir)/outname)
        ffmpegwav_take = (ffmpegwav % ('-t %s' % take) if take is not None
                          else ffmpegwav % (''))
        in_out(ffmpegwav_take, infile, outfile)
        if normalize:
            infile, outfile = outfile, o(outfile)
            in_out(ffmpegnormalize, infile, outfile)
        if denoise:
            infile, outfile = outfile, o(outfile)
            in_out(ffmpegdenoise, infile, outfile)
            infile, outfile = outfile, o(outfile)
            in_out(ffmpegdenoise, infile, outfile)
        if int(lowpass):
            infile, outfile = outfile, o(outfile)
            in_out(ffmpeglow % lowpass, infile, outfile)
        r, s = wavfile.read(outfile)
        # Check if stereo
        if len(s.shape) > 1:
            s = s[:, 0]
        return r, s


def fig1(title=None):
    fig = plt.figure(1)
    plt.margins(0, 0.1)
    plt.grid(True, color='0.7', linestyle='-', which='major', axis='both')
    plt.grid(True, color='0.9', linestyle='-', which='minor', axis='both')
    plt.title(title or 'Signal')
    plt.xlabel('Time [seconds]')
    plt.ylabel('Amplitude')
    axs = fig.get_axes()
    global ax
    ax = axs[0]


def show1(fs, s, color=None, title=None, v=None):
    if not color:
        fig1(title)
    if ax and v:
        ax.axvline(x=v, color='green')
    plt.plot(np.arange(len(s))/fs, s, color or 'black')
    if not color:
        plt.show()


def show2(fs, s1, s2, title=None):
    fig1(title)
    show1(fs, s1, 'blue')
    show1(fs, s2, 'red')
    plt.show()


def read_normalized(in1, in2):
    global normalize
    r1, s1 = normalize_denoise(in1, 'out1')
    if in1 == in2:
        r2, s2 = r1, s1
    else:
        r2, s2 = normalize_denoise(in2, 'out2')
    if r1 != r2:
        old, normalize = normalize, True
        r1, s1 = normalize_denoise(in1, 'out1')
        r2, s2 = normalize_denoise(in2, 'out2')
        normalize = old
    assert r1 == r2, "not same sample rate"
    fs = r1
    return fs, s1, s2


def corrabs(s1, s2):
    ls1 = len(s1)
    ls2 = len(s2)
    padsize = ls1+ls2+1
    padsize = 2**(int(np.log(padsize)/np.log(2))+1)
    s1pad = np.zeros(padsize)
    s1pad[:ls1] = s1
    s2pad = np.zeros(padsize)
    s2pad[:ls2] = s2
    corr = fft.ifft(fft.fft(s1pad)*np.conj(fft.fft(s2pad)))
    ca = np.absolute(corr)
    xmax = np.argmax(ca)
    return ls1, ls2, padsize, xmax, ca


def cli_parser(**ka):
    from argparse import ArgumentParser, RawDescriptionHelpFormatter
    parser = ArgumentParser(description=file_offset.__doc__,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--version', action='version', version=__version__)

    if 'in1' not in ka:
        parser.add_argument(
            'in1',
            help='Media file to loop.')
    if 'in2' not in ka:
        parser.add_argument(
            'in2',
            default=None,
            nargs='?',
            help='Second media file to loop; you probably don\'t want this. ' +
                 '(default: use first file)')
    if 'take' not in ka:
        parser.add_argument(
            '-t', '--take',
            dest='take',
            action='store',
            default=None,
            help='Take X seconds of the inputs to look at. ' +
                 '(default: entire input)')
    if 'show' not in ka:
        parser.add_argument(
            '-s', '--show',
            dest='show',
            action='store_true',
            default=False,
            help='Turn off "show diagrams", in case you are confident.')
    if 'normalize' not in ka:
        parser.add_argument(
            '-n', '--normalize',
            dest='normalize',
            action='store_true',
            default=False,
            help='Turn on normalize. It turns on by itself in a second ' +
                 'pass, if sampling rates differ.')
    if 'denoise' not in ka:
        parser.add_argument(
            '-d', '--denoise',
            dest='denoise',
            action='store_true',
            default=False,
            help='Turns on denoise, as experiment in case of failure.')
    if 'lowpass' not in ka:
        parser.add_argument(
            '-l', '--lowpass',
            dest='lowpass',
            action='store',
            default=0,
            help="lowpass, just in case, because like with manual sync'ing,\
            the low frequencies matter more. 0 == off. (default: 0)")
    if 'samples' not in ka:
        parser.add_argument(
            '--samples',
            dest='samples',
            action='store_true',
            default=False,
            help='Show offset in samples instead of seconds.')
    if 'loop' not in ka:
        parser.add_argument(
            '--loop',
            dest='loop',
            action='store_true',
            default=True,
            help='Calculate loop tags.')
    if 'loop-start-min' not in ka:
        parser.add_argument(
            '--loop-start-min',
            dest='loop-start-min',
            action='store',
            default=5.0,
            type=float,
            help="Minimum loop start position (seconds). (default: 5)")
    if 'loop-start-max' not in ka:
        parser.add_argument(
            '--loop-start-max',
            dest='loop-start-max',
            action='store',
            default=None,
            type=float,
            help="Maximum loop start position (seconds). (default: None)")
    if 'loop-end-min' not in ka:
        parser.add_argument(
            '--loop-end-min',
            dest='loop-end-min',
            action='store',
            default=20.0,
            type=float,
            help="Minimum loop end position (seconds). (default: 30)")
    if 'loop-len-min' not in ka:
        parser.add_argument(
            '--loop-len-min',
            dest='loop-len-min',
            action='store',
            default=0.0,
            type=float,
            help="Minimum loop length (seconds). (default: 0)")
    if 'loop-search-step' not in ka:
        parser.add_argument(
            '--loop-search-step',
            dest='loop-search-step',
            action='store',
            default=1.0,
            type=float,
            help="Resolution for loop search (seconds). (default: 1)")
    if 'loop-search-len' not in ka:
        parser.add_argument(
            '--loop-search-len',
            dest='loop-search-len',
            action='store',
            default=5.0,
            type=float,
            help="Snippet length for loop search (seconds). (default: 5)")
    if 'loop-force' not in ka:
        parser.add_argument(
            '--loop-force',
            dest='loop-force',
            action='store_true',
            default=False,
            help='Overwrite existing loop tags. ' +
                 '(default: skip files with existing loop tags)')
    if 'skip' not in ka:
        parser.add_argument(
            '--skip',
            dest='skip',
            action='store_true',
            default=False,
            help='Skip this audio file. (default: process file)')
    if 'verbose' not in ka:
        parser.add_argument(
            '-v', '--verbose',
            dest='verbose',
            action='store_true',
            default=False,
            help='Verbose output. (default: only show progress indicator)')
    return parser


def file_offset(use_argparse=True, **ka):
    """CLI interface to calculate loop metadata of an audio file.
    ffmpeg needs to be available.
    """

    if use_argparse:
        parser = cli_parser(**ka)
        args = parser.parse_args().__dict__
        ka.update(args)

    global take, normalize, denoise, lowpass, samples, loop
    global loopstart, loopstartmax, loopendmin, looplenmin
    global loopsearchstep, loopsearchlen
    global loopforce, skip, verbose
    in1, in2, take, show = ka['in1'], ka['in2'], ka['take'], ka['show']
    if in2 is None:
        in2 = in1
    in1, in2 = pathlib.Path(in1), pathlib.Path(in2)
    normalize, denoise, lowpass = ka['normalize'], ka['denoise'], ka['lowpass']
    samples = ka['samples']
    loop = ka['loop']
    loopstart, loopstartmax = ka['loop-start-min'], ka['loop-start-max']
    loopendmin, looplenmin = ka['loop-end-min'], ka['loop-len-min']
    loopsearchstep, loopsearchlen = ka['loop-search-step'], ka['loop-search-len']
    loopforce, skip, verbose = ka['loop-force'], ka['skip'], ka['verbose']

    if loop:
        mf = mutagen.File(in1)
        if not isinstance(mf, (ogg.OggFileType, flac.FLAC)):
            print_maybe('Not a Vorbis Comment file, skipping')
            return in1, None

    if loop and not loopforce:
        # Check for samples-denominated tags.
        if 'LOOPSTART' in mf and 'LOOPLENGTH' in mf:
            # Check for seconds-denominated tags.
            if 'LOOP_START' in mf and 'LOOP_END' in mf:
                print_maybe('Loop tags already present, skipping')
                return in1, None

    if skip:
        print_maybe('Skipping')
        return in1, None

    sample_rate, s1, s2 = read_normalized(in1, in2)

    if loop and not loopforce:
        if 'LOOPSTART' in mf and 'LOOPLENGTH' in mf:
            if 'LOOP_START' not in mf or 'LOOP_END' not in mf:
                print_maybe('Converting samples loop tags to ' +
                            'seconds loop tags, skipping')
                best_start = float(mf['LOOPSTART'][0])
                best_start_seconds = best_start / sample_rate
                best_length = float(mf['LOOPLENGTH'][0])
                best_end = best_start + best_length
                best_end_seconds = best_end / sample_rate
                mf['LOOP_START'] = [str(best_start_seconds)]
                mf['LOOP_END'] = [str(best_end_seconds)]
                mf.save()
                return in1, None
        if 'LOOP_START' in mf and 'LOOP_END' in mf:
            if 'LOOPSTART' not in mf or 'LOOPLENGTH' not in mf:
                print_maybe('Converting seconds loop tags to ' +
                            'samples loop tags, skipping')
                best_start_seconds = float(mf['LOOP_START'][0])
                best_start = int(best_start_seconds * sample_rate)
                best_end_seconds = float(mf['LOOP_END'][0])
                best_length_seconds = best_end_seconds - best_start_seconds
                best_length = int(best_length_seconds * sample_rate)
                mf['LOOPSTART'] = [str(best_start)]
                mf['LOOPLENGTH'] = [str(best_length)]
                mf.save()
                return in1, None

    if loop:
        best_ca = 0
        best_normalized_ca = 0
        best_start = 0
        best_start_seconds = 0.0
        best_end = 0
        best_end_seconds = 0.0
        searchlen_samples = int(loopsearchlen*sample_rate)
        init_start = int(loopstart*sample_rate)
        init_end_min = int(loopendmin*sample_rate)

        # We don't want to only loop a tiny piece at the end of the file.
        loopstartmax_samples = math.inf
        if loopstartmax is not None:
            loopstartmax_samples = loopstartmax*sample_rate
        loopstartmax_samples = int(min(loopstartmax_samples, len(s1) * 0.47))

        search_offset_max = len(s1) - searchlen_samples
        search_offset_max = min(search_offset_max,
                                loopstartmax_samples - init_start)
        search_offset_max_seconds = search_offset_max / sample_rate
        loopsearchstep_samples = int(loopsearchstep * sample_rate)

        pbar = ka['pbar'] if 'pbar' in ka else tqdm(unit='audio_sec')
        pbar.set_description(in1.name)
        pbar.reset(total=search_offset_max_seconds)

        for search_offset in range(0,
                                   search_offset_max,
                                   loopsearchstep_samples):
            this_start = init_start + search_offset
            this_end_min = init_end_min + search_offset
            candidate = corrabs(s1[this_start:][:searchlen_samples],
                                s2[this_end_min:])
            ls1, ls2, padsize, xmax, ca = candidate
            this_ca = max(ca)
            this_norm_magnitude = searchlen_samples * (len(s2) - this_end_min)
            this_normalized_ca = this_ca / this_norm_magnitude
            this_end = this_end_min + (padsize - xmax)
            this_length = this_end - this_start
            if this_end > len(s1):
                pbar.update(loopsearchstep)
                continue
            if this_length < looplenmin*sample_rate:
                pbar.update(loopsearchstep)
                continue
            if this_normalized_ca > best_normalized_ca:
                best_ca = this_ca
                best_normalized_ca = this_normalized_ca
                best_start = this_start
                best_start_seconds = best_start / sample_rate
                best_end = this_end
                best_end_seconds = best_end / sample_rate
                best_length = this_length
            print_maybe("offset", search_offset, "start", this_start,
                        "end", this_end, "length", this_length,
                        "confidence", this_ca,
                        "normalized_confidence", this_normalized_ca)
            pbar.update(loopsearchstep)
        print_maybe("best", "start", best_start,
                    "end", best_end, "length", best_length,
                    "confidence", best_ca,
                    "normalized_confidence", best_normalized_ca)
    else:
        ls1, ls2, padsize, xmax, ca = corrabs(s1, s2)
    if show:
        show1(sample_rate, ca, title='Correlation', v=xmax/sample_rate)
    if loop:
        sync_text = f"""
==============================================================================
{in1} needs tags 'LOOPSTART={int(best_start)} LOOPLENGTH={int(best_length)}'
==============================================================================
"""
    elif samples:
        sync_text = """
==============================================================================
%s needs 'ffmpeg -af atrim=start_sample=%s' cut to get in sync
==============================================================================
"""
    else:
        sync_text = """
==============================================================================
%s needs 'ffmpeg -ss %s' cut to get in sync
==============================================================================
"""
    if xmax > padsize // 2:
        if show:
            show2(sample_rate, s1, s2[padsize-xmax:],
                  title='1st=blue;2nd=red=cut(%s;%s)' % (in1, in2))
        file, offset = in2, (padsize-xmax)
    else:
        if show:
            show2(sample_rate, s1[xmax:], s2,
                  title='1st=blue=cut;2nd=red (%s;%s)' % (in1, in2))
        file, offset = in1, xmax
    if not samples:
        offset = offset / sample_rate
    if loop:
        print_maybe(sync_text)
        mf['LOOPSTART'] = [str(best_start)]
        mf['LOOPLENGTH'] = [str(best_length)]
        mf['LOOP_START'] = [str(best_start_seconds)]
        mf['LOOP_END'] = [str(best_end_seconds)]
        mf.save()
    else:
        print_maybe(sync_text % (file, offset))
    return file, offset


main = file_offset
if __name__ == '__main__':
    main()
