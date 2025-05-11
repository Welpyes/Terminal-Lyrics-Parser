# Terminal Lyrics Parser

A Python script to display synchronized lyrics
<br>
I made this script in my free time and i was drunk so yeah :pepelaugh:

## Features
- Displays lyrics synchronized with song playback using `.lrc` files.
- Supports multiple MPRIS-compliant players (Rhythmbox, VLC, Spotify, etc.).
- Smart line wrapping at word boundaries to fit terminal width.
- Customizable scroll offset (default: current line 3rd from top).
- Status bar with song title, artist, and playback position/duration.
- Configurable via command-line flags (e.g., lyrics directory, player, offset).
- Cross-platform: Works on Termux and common Linux distributions (Ubuntu, Fedora, Arch).
- Clears screen between songs for clean transitions.
- Minimizes flickering with partial screen redraws.
- Handles missing lyrics gracefully without exiting.
- Saves timestamps and cleaned lyrics to cache files.

## Dependencies
- **Python 3+**: Required to run the script.
- **dbus-python**: For interacting with MPRIS media players.
- **MPRIS-compliant media player**: E.g., Rhythmbox, VLC, Clementine, Spotify.
- **Termux (optional)**: For Android usage, requires `termux-api` for D-Bus support. **You need to be in an X11 Desktop for this to work**

## Installation

### On Termux
1. Install dependencies:
```bash
pkg install python
pkg install dbus-python
pkg install dbus
```
3. Ensure a media player is installed (e.g., Rhythmbox via `pkg install rhythmbox` if available).
4. Installation
```bash
git clone https://github.com/Welpyes/Terminal-Lyrics-Parser
cd Terminal-Lyrics-Parser
./lrc.py
```

### On Linux Distributions (Ubuntu, Fedora, Arch, etc.)
1. Install dependencies:
<br>
</br>

   - Ubuntu:
```bash
sudo apt update
sudo apt install python3 python3-pip
pip3 install dbus-python
```
   - Fedora:
```bash
sudo dnf install python3 python3-pip
pip3 install dbus-python
```
   - Arch:
```bash
sudo pacman -S python python-pip
pip3 install dbus-python
```
2. Install an MPRIS-compliant media player (e.g., Rhythmbox, VLC):
   - Ubuntu: `sudo apt install rhythmbox vlc`
   - Fedora: `sudo dnf install rhythmbox vlc`
   - Arch: `sudo pacman -S rhythmbox vlc`
3. Clone this repository and `cd Terminal-Lyrics-Parser` then run the script.

## Usage
1. Place `.lrc` files in the same directory as your music files or specify a custom lyrics directory with the `-l` flag.
2. Run the script:
```bash
./lrc.py
```
3. Play a song in an MPRIS-compliant player. The script displays lyrics synchronized with playback, with a status bar at the bottom.
4. Press `Ctrl+C` to exit.

### Command-Line Flags
The script supports the following flags for customization. Run `./lrc.py -h` to see the help dialogue:

```bash
usage: lrc.py [-h] [-l LYRICS_DIR] [-p PLAYER] [-c CACHE_DIR] [-o OFFSET]
              [-w WRAP_WIDTH] [-s SCROLL_OFFSET] [-f FORMAT]

Display lyrics for songs playing in MPRIS-compliant media players.

options:
  -h, --help            show this help message and exit
  -l LYRICS_DIR, --lyrics-dir LYRICS_DIR
                        Directory containing .lrc files
  -p PLAYER, --player PLAYER
                        Preferred MPRIS player (e.g., vlc, rhythmbox)
  -c CACHE_DIR, --cache-dir CACHE_DIR
                        Directory for cache files (default: ~/.cache)
  -o OFFSET, --offset OFFSET
                        Lyrics offset in seconds (default: 0.3)
  -w WRAP_WIDTH, --wrap-width WRAP_WIDTH
                        Custom line wrap width
  -s SCROLL_OFFSET, --scroll-offset SCROLL_OFFSET
                        Scroll offset in lines (default: 3)
  -f FORMAT, --format FORMAT
                        Status bar format (e.g., '{title} - {artist}') (default: Song: {title} | Artist: {artist} | {position} / {duration})
```

### Examples
- Use a custom lyrics directory:
```bash
./lrc.py -l /home/user/Lyrics
```
- Specify VLC as the player and a 0.5s offset:
```bash
./lrc.py -p vlc -o 0.5
```
- Custom cache directory and status bar format:
```bash
./lrc.py -c /tmp/lyrics_cache -f "{title} - {artist}"
```
- Fixed wrap width and 5-line scroll offset:
```bash
./lrc.py -w 50 -s 5
```

## Notes
- **Lyrics Files**: `.lrc` files must have the same base name as the song file (e.g., `song.mp3` → `song.lrc`). Supports `[offset:±ms]` for timing adjustments.
- **Cache Files**: Timestamps are saved to `lyrics_timestamps.txt` and cleaned lyrics to `lyrics.tmp` in the cache directory (default: `~/.cache`).
- **Termux**: Ensure `termux-api` is installed for D-Bus support. Lyrics can be stored on `/sdcard` with `-l /sdcard/Lyrics`.

- **Troubleshooting**:
  - Check terminal size: `tput lines; tput cols`.
  - Verify D-Bus: `dbus-send --print-reply --dest=org.mpris.MediaPlayer2.rhythmbox /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:'org.mpris.MediaPlayer2.Player' string:'Metadata'`.
  - Ensure `.lrc` files are accessible: `ls /path/to/song.lrc`.

## Contributing
Feel free to submit issues or pull requests for additional features (e.g., new flags, player support) or bug fixes.

## License
MIT License
