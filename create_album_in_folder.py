# pip install eyeD3
# pip install python-magic-bin

# to download a youtube video as mp3:
# download https://github.com/yt-dlp/yt-dlp
# install or configure ffmpeg in the PATH
# yt-dlp.exe --extract-audio --audio-format mp3 "link to video or playlist"

import eyed3
import typing as t
from os import listdir
from os.path import join, splitext
import argparse


def remove_quotes(string: str):
    return "".join(filter(lambda x: x not in ['"', "'"], string))


def main(parsed_args: argparse.Namespace, print_help: t.Callable):
    author = parsed_args.author
    album = parsed_args.album
    base_dir = remove_quotes(parsed_args.dir)
    if not all((author, album, base_dir)):
        print_help()
        return
    songs_names = list(filter(lambda x: ".mp3" in x, listdir(base_dir)))
    for number, song_name in enumerate(songs_names):
        audiofile = eyed3.load(join(base_dir, song_name))
        if audiofile is None:
            print(f"can't load file {song_name}")
            continue
        audiofile.tag.artist = author
        audiofile.tag.album = album
        title, _ = splitext(song_name)
        audiofile.tag.title = title
        audiofile.tag.track_num = number + 1
        audiofile.tag.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create an album from a directory of songs"
    )
    parser.add_argument(
        "--author",
        "-A",
        type=str,
        help="add album author",
    )
    parser.add_argument(
        "--album",
        "-a",
        type=str,
        help="add album name",
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=".",
        help="add album directory location",
    )
    parsed_args = parser.parse_args()
    main(parsed_args, parser.print_help)
