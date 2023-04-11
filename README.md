# CrossLooper

CrossLooper is a tool for automatically setting the `LOOPSTART`, `LOOPLENGTH`, `LOOP_START`, and `LOOP_END` metadata tags in audio files. These tags are used by various software (including RPG Maker) to seamlessly loop audio (e.g. for game BGM). CrossLooper uses statistical cross-correlation to guess the correct loop points. Among other use cases, CrossLooper may be useful for game developers who are given BGM assets that don't have loop points, or for game modders who want to add loop points to games whose BGM doesn't have them.

## Installation

First, you'll need to install [game-engine-finder](https://github.com/vetleledaal/game-engine-finder) according to its installation instructions.

Once you've done that, to install CrossLooper via pip, do this from the `crosslooper` repo directory:

```
pip install --user .
```

## Prerequisites

* The audio files must not be in a packed/encrypted format. If the game you're working with uses packed or encrypted audio files of some kind, you'll need to unpack them. You may find these tools helpful:
    * [RPG Maker XP / VX / VX Ace Decrypter](https://github.com/uuksu/RPGMakerDecrypter)
    * [RPG Maker MV / MZ File Decrypter](https://github.com/Petschko/Java-RPG-Maker-MV-Decrypter)
    * [Enigma Virtual Box Unpacker](https://github.com/mos9527/evbunpack)
* The audio files must be of a container format that supports Vorbis Comment metadata. In practice, this means that Ogg files and FLAC files will work. If your audio files are in some other container format (e.g. MP3), you'll need to convert them first, e.g. with [ffmpeg](https://ffmpeg.org/).

## Usage

### As a game developer

If you're a game developer, you can use CrossLooper to set loop points on your BGM files before distributing your game.

Typically (~76% of the time), you can run CrossLooper with no hints, and it will guess the loop points correctly:

```
crosslooper example.ogg
```

CrossLooper will edit the input file in-place to add loop tags. You can do this for each BGM file.

If it gets the loop points wrong, you can pass a variety of flags to help CrossLooper guess the correct loop points. See the help for details:

```
crosslooper --help
```

Usually, the `--looplenmin` hint is the only one you will need, but the others may be helpful too. If you're having trouble, you may wish to pass `--verbose` to see logs of which loop point candidates are being considered. If you've already set wrong loop points and want to overwrite them, pass the `--loopforce` flag.

### As a game mod developer

If you're a game mod developer, you can use CrossLooper to find the loop points of the BGM in an existing, already-released game.

Follow the instructions for "As a game developer", but keep track of which command-line flags you set for each file. Then, create a new `.conf` file in the `crosslooperpresets` folder that contains the flags you used for each file. The `.conf` file should be named with a substring of the game title, excluding any version numbers. If the game has multiple titles (e.g. for Japanese and English localized versions), name the `.conf` file after the English version, and add a symlink for any other languages. For each file that was unloopable, set `skip = true`. You can look at the existing `.conf` files in that folder for inspiration.

Once you've created the `.conf` file, follow the instructions for "As a game mod user" (starting with an unmodded game) to make sure everything works correctly. If so, please send in a PR so that I can add your `.conf` file to the repository.

### As a game mod user

If you're a gamer, you can use CrossLooper to apply loop point presets that game mod developers have submitted to this repository.

From the directory of a game, run the following:

```
crosslooperdir
```

CrossLooper will edit all of the game's BGM files in-place to add loop points.

For more details on the other command-line flags available, see the help:

```
crosslooperdir --help
```

## Testing Your Results

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

CrossLooper depends on [game-engine-finder](https://github.com/vetleledaal/game-engine-finder), Copyright (c) 2023 Vetle Ledaal, Faalagorn, Splendide Imaginarius.
