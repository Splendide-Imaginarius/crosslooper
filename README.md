# CrossLooper

CrossLooper is a tool for automatically setting the `LOOPSTART` and `LOOPLENGTH` metadata tags in audio files. These tags are used by various software (including RPG Maker) to seamlessly loop audio (e.g. for game BGM). CrossLooper uses statistical cross-correlation to guess the correct loop points. Among other use cases, CrossLooper may be useful for game developers who are given BGM assets that don't have loop points, or for game modders who want to add loop points to games whose BGM doesn't have them.

## How to use

Typically (~76% of the time), you can run CrossLooper with no hints, and it will guess the loop points correctly:

```
crosslooper.py example.ogg
```

CrossLooper will edit the input file in-place to add loop tags.

If it gets the loop points wrong, you can pass a variety of flags to help CrossLooper guess the correct loop points. See the help for details:

```
crosslooper.py --help
```

Usually, the `--looplenmin` hint is the only one you will need, but the others may be helpful too.

## Credits

Copyright 2023 Splendide Imaginarius.

CrossLooper is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

CrossLooper is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with CrossLooper. If not, see [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/).

CrossLooper is a heavily modified fork of [syncstart](https://github.com/rpuntaie/syncstart), Copyright (C) 2021 Roland Puntaier.
