#!/usr/bin/env python3

import os
import re
import time
import curses
import dbus
import argparse
from urllib.parse import unquote

# Default settings
DEFAULT_LYRICS_OFFSET = 0.3
DEFAULT_SCROLL_OFFSET = 3
DEFAULT_STATUS_FORMAT = "Song: {title} | Artist: {artist} | {position} / {duration}"

def parse_args():
    parser = argparse.ArgumentParser(description="Display lyrics for songs playing in MPRIS-compliant media players.")
    parser.add_argument("-l", "--lyrics-dir", help="Directory containing .lrc files")
    parser.add_argument("-p", "--player", help="Preferred MPRIS player (e.g., vlc, rhythmbox)")
    parser.add_argument("-c", "--cache-dir", help="Directory for cache files", default=os.path.join(os.path.expanduser("~"), ".cache"))
    parser.add_argument("-o", "--offset", type=float, default=DEFAULT_LYRICS_OFFSET, help="Lyrics offset in seconds (default: 0.3)")
    parser.add_argument("-w", "--wrap-width", type=int, help="Custom line wrap width")
    parser.add_argument("-s", "--scroll-offset", type=int, default=DEFAULT_SCROLL_OFFSET, help="Scroll offset in lines (default: 3)")
    parser.add_argument("-f", "--format", default=DEFAULT_STATUS_FORMAT, help="Status bar format (e.g., '{title} - {artist}') (default: Song: {title} | Artist: {artist} | {position} / {duration})")
    return parser.parse_args()

args = parse_args()

# Define paths
HOME_DIR = os.path.expanduser("~")
TMP_FILE = os.path.join(args.cache_dir, "lyrics.tmp")
TIMESTAMP_FILE = os.path.join(args.cache_dir, "lyrics_timestamps.txt")

# Additional lyrics offset (seconds)
LYRICS_OFFSET = args.offset

def get_mpris_players():
    try:
        bus = dbus.SessionBus()
        mpris_players = []
        for service in bus.list_names():
            if service.startswith('org.mpris.MediaPlayer2.'):
                mpris_players.append(service)
        return mpris_players
    except dbus.exceptions.DBusException:
        return []

def get_rhythmbox_property(prop, player_service=None):
    try:
        bus = dbus.SessionBus()
        if player_service is None:
            player_service = 'org.mpris.MediaPlayer2.rhythmbox'
        player = bus.get_object(player_service, '/org/mpris/MediaPlayer2')
        properties = dbus.Interface(player, 'org.freedesktop.DBus.Properties')
        return properties.Get('org.mpris.MediaPlayer2.Player', prop)
    except dbus.exceptions.DBusException:
        return None

def get_current_song_uri():
    if args.player:
        player_service = f'org.mpris.MediaPlayer2.{args.player.lower()}'
        metadata = get_rhythmbox_property('Metadata', player_service)
        if metadata and 'xesam:url' in metadata:
            return str(metadata['xesam:url']), player_service
    players = get_mpris_players()
    for player in players:
        metadata = get_rhythmbox_property('Metadata', player)
        if metadata and 'xesam:url' in metadata:
            return str(metadata['xesam:url']), player
    metadata = get_rhythmbox_property('Metadata')
    if metadata and 'xesam:url' in metadata:
        return str(metadata['xesam:url']), 'org.mpris.MediaPlayer2.rhythmbox'
    return None, None

def get_song_metadata(player_service):
    metadata = get_rhythmbox_property('Metadata', player_service)
    title = "Unknown Title"
    artist = "Unknown Artist"
    duration = 0
    if metadata:
        title = str(metadata.get('xesam:title', title))
        artist = str(metadata.get('xesam:artist', [artist])[0])
        duration = int(metadata.get('mpris:length', 0)) / 1000000
    return title, artist, duration

def get_song_position(player_service):
    position = get_rhythmbox_property('Position', player_service)
    if position is not None:
        return int(position) / 1000000
    return 0

def parse_lrc_file(lrc_path):
    if not os.path.isfile(lrc_path):
        return None, None, None

    offset = 0
    lyrics = []
    timestamps = []

    try:
        with open(lrc_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return None, None, None

    with open(TIMESTAMP_FILE, 'w', encoding='utf-8') as ts_file:
        for line in lines:
            line = line.strip()
            offset_match = re.match(r'^\[offset:([-+]?[0-9]+)\]', line)
            if offset_match:
                try:
                    offset = int(offset_match.group(1)) / 1000
                except ValueError:
                    offset = 0
                continue
            timestamp_match = re.match(r'^\[(\d{2}:\d{2}\.\d{2})\](.*)', line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                lyric = timestamp_match.group(2).strip()
                minutes, seconds = map(float, timestamp_str.split(':'))
                timestamp = minutes * 60 + seconds - offset - LYRICS_OFFSET
                lyrics.append(lyric)
                timestamps.append(timestamp)
                ts_file.write(f"{timestamp_str}\n")

    return lyrics, timestamps, offset

def uri_to_path(uri):
    if uri.startswith('file://'):
        path = unquote(uri[7:])
        return path.replace(os.path.expanduser('~'), HOME_DIR)
    return uri

def get_lrc_path(song_path):
    if args.lyrics_dir and os.path.isdir(args.lyrics_dir):
        base = os.path.splitext(os.path.basename(song_path))[0]
        return os.path.join(args.lyrics_dir, f"{base}.lrc")
    base, _ = os.path.splitext(song_path)
    return f"{base}.lrc"

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def wrap_line(text, max_width):
    if not text or max_width < 1:
        return [""]
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        if current_length + word_length + (1 if current_line else 0) <= max_width:
            current_line.append(word)
            current_length += word_length + (1 if current_line else 0)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            if word_length > max_width:
                while word:
                    lines.append(word[:max_width])
                    word = word[max_width:]
                    current_line = []
                    current_length = 0
            else:
                current_line = [word]
                current_length = word_length

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else [""]

def main(stdscr):
    curses.use_default_colors()
    curses.curs_set(0)
    stdscr.timeout(100)

    previous_uri = None
    lyrics = []
    timestamps = []
    current_line = -1
    start_line = 0
    last_displayed = []
    last_status = ""

    os.makedirs(os.path.dirname(TMP_FILE), exist_ok=True)

    try:
        while True:
            current_uri, player_service = get_current_song_uri()
            title, artist, duration = get_song_metadata(player_service)

            if not current_uri:
                if lyrics or current_uri != previous_uri:
                    lyrics = []
                    timestamps = []
                    current_line = -1
                    start_line = 0
                    last_displayed = []
                    stdscr.clear()
                    stdscr.refresh()
                previous_uri = None
                status = f"Song: {title}"[:curses.COLS-1]
                if status != last_status or not last_displayed:
                    stdscr.addstr(0, 0, "No song is currently playing.")
                    if curses.LINES > 1:
                        try:
                            stdscr.move(curses.LINES - 1, 0)
                            stdscr.clrtoeol()
                            stdscr.addstr(curses.LINES - 1, 0, status, curses.A_DIM)
                        except curses.error:
                            pass
                    stdscr.refresh()
                    last_status = status
                    last_displayed = ["No song is currently playing."]
                time.sleep(0.1)
                continue

            if current_uri != previous_uri:
                previous_uri = current_uri
                stdscr.clear()
                stdscr.refresh()
                song_path = uri_to_path(current_uri)
                lrc_path = get_lrc_path(song_path)
                lyrics, timestamps, offset = parse_lrc_file(lrc_path)

                if not lyrics:
                    lyrics = []
                    timestamps = []
                    current_line = -1
                    start_line = 0
                    last_displayed = []
                    status = f"Song: {title}"[:curses.COLS-1]
                    if status != last_status or not last_displayed:
                        stdscr.addstr(0, 0, f"No lyrics found at: {lrc_path}")
                        if curses.LINES > 1:
                            try:
                                stdscr.move(curses.LINES - 1, 0)
                                stdscr.clrtoeol()
                                stdscr.addstr(curses.LINES - 1, 0, status, curses.A_DIM)
                            except curses.error:
                                pass
                        stdscr.refresh()
                        last_status = status
                        last_displayed = [f"No lyrics found at: {lrc_path}"]
                    time.sleep(0.1)
                    continue

                with open(TMP_FILE, 'w', encoding='utf-8') as f:
                    for lyric in lyrics:
                        f.write(f"{lyric}\n")

                current_line = -1
                start_line = 0
                last_displayed = []

            position = get_song_position(player_service)

            new_line = 0
            for i, ts in enumerate(timestamps):
                if ts <= position:
                    new_line = i
                else:
                    break

            max_y, max_x = stdscr.getmaxyx()
            window_size = max_y - 2 if max_y > 2 else 1
            wrap_width = args.wrap_width if args.wrap_width and args.wrap_width > 0 else max_x - 1

            if new_line < start_line:
                start_line = max(0, new_line - (args.scroll_offset - 1))
            elif new_line >= start_line + window_size - (args.scroll_offset - 1):
                start_line = new_line - (args.scroll_offset - 1)

            status = args.format.format(
                title=title,
                artist=artist,
                position=format_time(position),
                duration=format_time(duration)
            )[:max_x-1]

            if new_line != current_line or start_line != (current_line - (current_line % window_size)) or status != last_status:
                current_line = new_line
                end_line = min(len(lyrics), start_line + window_size)
                new_displayed = []
                y_offset = 0

                for i in range(start_line, end_line):
                    wrapped_lines = wrap_line(lyrics[i], wrap_width)
                    for line in wrapped_lines:
                        if y_offset < window_size:
                            new_displayed.append((line, i == current_line and line == wrapped_lines[0]))
                            y_offset += 1
                        else:
                            break
                    if y_offset >= window_size:
                        break

                for y in range(window_size):
                    if y >= len(new_displayed):
                        stdscr.move(y, 0)
                        stdscr.clrtoeol()
                    elif y >= len(last_displayed) or new_displayed[y] != last_displayed[y]:
                        stdscr.move(y, 0)
                        stdscr.clrtoeol()
                        lyric, is_current = new_displayed[y]
                        if is_current:
                            stdscr.addstr(y, 0, lyric, curses.A_BOLD | curses.A_UNDERLINE)
                        else:
                            stdscr.addstr(y, 0, lyric)

                last_displayed = new_displayed

                if status != last_status and max_y > 1:
                    try:
                        stdscr.move(max_y - 1, 0)
                        stdscr.clrtoeol()
                        stdscr.addstr(max_y - 1, 0, status, curses.A_DIM)
                        last_status = status
                    except curses.error:
                        pass

                stdscr.refresh()

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Error: {str(e)}")
        if curses.LINES > 1:
            try:
                stdscr.addstr(curses.LINES - 1, 0, f"Song: {title}")
            except curses.error:
                pass
        stdscr.refresh()
        time.sleep(1)

if __name__ == "__main__":
    curses.wrapper(main)
