# CrossLooper

CrossLooper is a tool for automatically setting the `LOOPSTART`, `LOOPLENGTH`, `LOOP_START`, and `LOOP_END` metadata tags in audio files. These tags are used by various software (including RPG Maker) to seamlessly loop audio (e.g. for game BGM). CrossLooper uses statistical cross-correlation to guess the correct loop points. Among other use cases, CrossLooper may be useful for game developers who are given BGM assets that don't have loop points, or for game modders who want to add loop points to games whose BGM doesn't have them.

## Installation

To install via pip, do this from the `crosslooper` repo directory:

~~~
pip install --user .
~~~

## How to use

The audio files must be of a container format that supports Vorbis Comment metadata. In practice, this means that Ogg files and FLAC files will work. If your audio files are in some other container format (e.g. MP3), you'll need to convert them first.

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

## Testing Results

To play a tagged `.ogg` audio file, you can do one of the following:

* Replace the title screen `.ogg` file of an RPG Maker game with the tagged audio file you created; then launch the RPG Maker game.
* Play the `.ogg` file with [loop-ogg](https://github.com/SolraBizna/loop-ogg).

I am not currently aware of any `.flac` players that support loop points; please let me know if there exist any.

## Standards

CrossLooper sets both seconds-denominated loop points and samples-denominated loop points. [Further explanation is here.](https://github.com/SolraBizna/loop-ogg#what) RPG Maker only uses samples-denominated loop points and will ignore seconds-denominated loop points.

## Credits

Copyright 2023 Splendide Imaginarius.

This is not a license requirement, but if you use CrossLooper for a project such as a game or a game mod, it would be greatly appreciated if you credit me. Example credits: "BGM was looped with CrossLooper by Splendide Imaginarius." Linking back to this Git repository would also be greatly appreciated.

CrossLooper is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

CrossLooper is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with CrossLooper. If not, see [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/).

CrossLooper is a heavily modified fork of [syncstart](https://github.com/rpuntaie/syncstart), Copyright (C) 2021 Roland Puntaier.
