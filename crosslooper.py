#!/usr/bin/env python3

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import numpy as np
from scipy import fft
from scipy.io import wavfile
import tempfile
import os
import pathlib
import sys
import statistics
import mutagen

__version__ = "1.0.1"
__author__ = """Splendide Imaginarius"""

#global
ax = None
take = None
normalize = False
denoise = False
lowpass = 0
samples = False
loop = False
loopstart = 5
loopstartmax = None
loopendmin = 30.0
looplenmin = 0.0
loopsearchstep = 1.0
loopsearchlen = 30.0

ffmpegwav = 'ffmpeg -i "{}" %s -c:a pcm_s16le -map 0:a "{}"'
ffmpegnormalize = ('ffmpeg -y -nostdin -i "{}" -filter_complex ' +
"'[0:0]loudnorm=i=-23.0:lra=7.0:tp=-2.0:offset=4.45:linear=true:print_format=json[norm0]' " +
"-map_metadata 0 -map_metadata:s:a:0 0:s:a:0 -map_chapters 0 -c:v copy -map '[norm0]' " +
'-c:a:0 pcm_s16le -c:s copy "{}"')
ffmpegdenoise = 'ffmpeg -i "{}" -af'+" 'afftdn=nf=-25' "+'"{}"'
ffmpeglow = 'ffmpeg -i "{}" -af'+" 'lowpass=f=%s' "+'"{}"'
o = lambda x: '%s%s'%(x,'.wav')

def in_out(command,infile,outfile):
    hdr = '-'*len(command)
    print("%s\n%s\n%s"%(hdr,command,hdr))
    ret = os.system(command.format(infile,outfile))
    if 0 != ret:
      sys.exit(ret)

def normalize_denoise(infile,outname):
  with tempfile.TemporaryDirectory() as tempdir:
    outfile = o(pathlib.Path(tempdir)/outname)
    ffmpegwav_take = ffmpegwav%('-t %s'%take) if take is not None else ffmpegwav%('')
    in_out(ffmpegwav_take,infile,outfile)
    if normalize:
      infile, outfile = outfile,o(outfile)
      in_out(ffmpegnormalize,infile,outfile)
    if denoise:
      infile, outfile = outfile,o(outfile)
      in_out(ffmpegdenoise,infile,outfile)
      infile, outfile = outfile,o(outfile)
      in_out(ffmpegdenoise,infile,outfile)
    if int(lowpass):
      infile, outfile = outfile,o(outfile)
      in_out(ffmpeglow%lowpass,infile,outfile)
    r,s = wavfile.read(outfile)
    if len(s.shape)>1: #stereo
      s = s[:,0]
    return r,s

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
  if not color: fig1(title)
  if ax and v: ax.axvline(x=v,color='green')
  plt.plot(np.arange(len(s))/fs, s, color or 'black')
  if not color: plt.show()

def show2(fs,s1,s2,title=None):
  fig1(title)
  show1(fs,s1,'blue')
  show1(fs,s2,'red')
  plt.show()

def read_normalized(in1,in2):
  global normalize
  r1,s1 = normalize_denoise(in1,'out1')
  r2,s2 = normalize_denoise(in2,'out2')
  if r1 != r2:
    old,normalize = normalize,True
    r1,s1 = normalize_denoise(in1,'out1')
    r2,s2 = normalize_denoise(in2,'out2')
    normalize = old
  assert r1 == r2, "not same sample rate"
  fs = r1
  return fs,s1,s2

def corrabs(s1,s2):
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
  return ls1,ls2,padsize,xmax,ca

def cli_parser(**ka):
  import argparse
  parser = argparse.ArgumentParser(description=file_offset.__doc__,
                      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--version', action='version', version = __version__)

  if 'in1' not in ka:
    parser.add_argument(
      'in1',
      help='Media file to loop.')
  if 'in2' not in ka:
    parser.add_argument(
      'in2',
      default=None,
      nargs='?',
      help='Second media file to loop; you probably don\'t want this. (default: use first file)')
  if 'take' not in ka:
    parser.add_argument(
      '-t','--take',
      dest='take',
      action='store',
      default=None,
      help='Take X seconds of the inputs to look at. (default: entire input)')
  if 'show' not in ka:
    parser.add_argument(
      '-s','--show',
      dest='show',
      action='store_true',
      default=False,
      help='Turn off "show diagrams", in case you are confident.')
  if 'normalize' not in ka:
    parser.add_argument(
      '-n','--normalize',
      dest='normalize',
      action='store_true',
      default=False,
      help='Turn on normalize. It turns on by itself in a second pass, if sampling rates differ.')
  if 'denoise' not in ka:
    parser.add_argument(
      '-d','--denoise',
      dest='denoise',
      action='store_true',
      default=False,
      help='Turns on denoise, as experiment in case of failure.')
  if 'lowpass' not in ka:
    parser.add_argument(
      '-l','--lowpass',
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
  if 'loopstart' not in ka:
    parser.add_argument(
      '--loopstart',
      dest='loopstart',
      action='store',
      default=5.0,
      type=float,
      help="Loop start position (seconds). (default: 5)")
  if 'loopstartmax' not in ka:
    parser.add_argument(
      '--loopstartmax',
      dest='loopstartmax',
      action='store',
      default=None,
      type=float,
      help="Maximum loop start position (seconds). (default: None)")
  if 'loopendmin' not in ka:
    parser.add_argument(
      '--loopendmin',
      dest='loopendmin',
      action='store',
      default=20.0,
      type=float,
      help="Minimum loop end position (seconds). (default: 30)")
  if 'looplenmin' not in ka:
    parser.add_argument(
      '--looplenmin',
      dest='looplenmin',
      action='store',
      default=0.0,
      type=float,
      help="Minimum loop length (seconds). (default: 0)")
  if 'loopsearchstep' not in ka:
    parser.add_argument(
      '--loopsearchstep',
      dest='loopsearchstep',
      action='store',
      default=1.0,
      type=float,
      help="Resolution for loop search (seconds). (default: 1)")
  if 'loopsearchlen' not in ka:
    parser.add_argument(
      '--loopsearchlen',
      dest='loopsearchlen',
      action='store',
      default=5.0,
      type=float,
      help="Snippet length for loop search (seconds). (default: 5)")
  return parser

def file_offset(**ka):
  """CLI interface to calculate loop metadata of an audio file.
  ffmpeg needs to be available.
  """

  parser = cli_parser(**ka)
  args = parser.parse_args().__dict__
  ka.update(args)

  global take,normalize,denoise,lowpass,samples,loop,loopstart,loopstartmax,loopendmin,looplenmin,loopsearchstep,loopsearchlen
  in1,in2,take,show = ka['in1'],ka['in2'],ka['take'],ka['show']
  if in2 is None:
    in2 = in1
  normalize,denoise,lowpass,samples = ka['normalize'],ka['denoise'],ka['lowpass'],ka['samples']
  loop,loopstart,loopstartmax,loopendmin,looplenmin = ka['loop'],ka['loopstart'],ka['loopstartmax'],ka['loopendmin'],ka['looplenmin']
  loopsearchstep,loopsearchlen = ka['loopsearchstep'],ka['loopsearchlen']
  sample_rate,s1,s2 = read_normalized(in1,in2)
  if loop:
    best_ca = 0
    best_normalized_ca = 0
    best_start = 0
    best_end = 0
    all_ends = []
    searchlen_samples = int(loopsearchlen*sample_rate)
    init_start = int(loopstart*sample_rate)
    init_end_min = int(loopendmin*sample_rate)
    for search_offset in range(0, len(s1) - searchlen_samples, int(loopsearchstep * sample_rate)):
      this_start = init_start + search_offset
      # We don't want to only loop a tiny piece at the end of the file.
      if loopstartmax is not None and this_start > int(loopstartmax*sample_rate):
          break
      if this_start > len(s1) * 0.47:
          break
      this_end_min = init_end_min + search_offset
      candidate = corrabs(s1[this_start:][:searchlen_samples], s2[this_end_min:])
      ls1,ls2,padsize,xmax,ca = candidate
      this_ca = max(ca)
      this_normalized_ca = this_ca / (searchlen_samples * (len(s2) - this_end_min))
      this_end = this_end_min + (padsize - xmax)
      this_length = this_end - this_start
      if this_end > len(s1):
        continue
      if this_length < looplenmin*sample_rate:
        continue
      if this_normalized_ca > best_normalized_ca:
        best_ca = this_ca
        best_normalized_ca = this_normalized_ca
        best_start = this_start
        best_end = this_end
        best_length = this_length
      print("offset", search_offset, "start", this_start, "end", this_end, "length", this_length, "confidence", this_ca, "normalized_confidence", this_normalized_ca)
    print("best", "start", best_start, "end", best_end, "length", best_length, "confidence", best_ca, "normalized_confidence", best_normalized_ca)
  else:
    ls1,ls2,padsize,xmax,ca = corrabs(s1,s2)
  if show: show1(sample_rate,ca,title='Correlation',v=xmax/sample_rate)
  if loop:
    sync_text = f"""
==============================================================================
{in1} needs ogg tags 'LOOPSTART={int(best_start)} LOOPLENGTH={int(best_length)}' to loop
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
    if show: show2(sample_rate,s1,s2[padsize-xmax:],title='1st=blue;2nd=red=cut(%s;%s)'%(in1,in2))
    file,offset = in2,(padsize-xmax)
  else:
    if show: show2(sample_rate,s1[xmax:],s2,title='1st=blue=cut;2nd=red (%s;%s)'%(in1,in2))
    file,offset = in1,xmax
  if not samples:
    offset = offset / sample_rate
  if loop:
    print(sync_text)
    mf = mutagen.File(in1)
    mf['LOOPSTART'] = [str(best_start)]
    mf['LOOPLENGTH'] = [str(best_length)]
    mf.save()
  else:
    print(sync_text%(file,offset))
  return file,offset

main = file_offset
if __name__ == '__main__':
    main()

