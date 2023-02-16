#!/usr/bin/env python3

from pathlib import Path

import crosslooper

__version__ = crosslooper.__version__
__author__ = crosslooper.__author__

def get_preset(game_title):
  p = Path(__file__)
  p = p.parent
  candidates = p.glob("*.conf")

  for candidate in candidates:
    if candidate.stem.lower() in game_title.lower():
      return candidate

  return None
