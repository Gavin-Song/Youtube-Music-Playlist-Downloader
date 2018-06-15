"""
__init__.py
Gavin Song (c) 2018

Download a youtube music playlist. Properly formats
metadata for the songs.
"""

import os
import subprocess
import urllib.parse
import requests
import random
import shutil
import re
import sys

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from pytube import YouTube
import youtube_title_parse

import config

cwd = os.getcwd()


def create_dir_if_not_exist(path):
    """
    Creates a directory if it doesn't
    already exist

    :param path: Path to dir
    """
    os.makedirs(path, exist_ok=True)


def get_videos_in_playlist(playlist_url):
    """
    Returns a list of youtube video ids given
    a direct url to the playlist
    (Format https://www.youtube.com/playlist?list=<PLAYLIST ID>)

    :param playlist_url: Url to playlist
    :return: Array of youtube video ids
    """
    data = requests.get(playlist_url).text

    urls = re.findall("/watch\?v=(.*?)amp;", data)
    urls = list(set(urls))
    urls = [url.replace("&", "") for url in urls]
    return urls


def download_video(vid_id, dest):
    """
    Downloads a given youtube video ID to a directory

    :param vid_id: Video id
    :param dest: Destination dir
    :return: Download stream object
    """
    stream = YouTube("http://youtube.com/watch?v={}".format(vid_id)).streams\
        .filter(subtype="mp4")\
        .first()
    stream.download(dest)
    return stream


def convert_mp4_to_mp3(mp4_dir, mp3_dir):
    """
    Uses FFMPEG to convert a mp4 to an mp3
    FFMPEG must be accessible from the command line

    :param mp4_dir: Dir of mp4
    :param mp3_dir: Dir of output mp3
    """
    subprocess.call(
        [
            "ffmpeg",
            "-loglevel",
            "panic",
            "-i",
            mp4_dir.replace("\\", "/"),
            mp3_dir,
            "-hide_banner"
        ], cwd=cwd)


def get_youtube_thumbnail_url(v_id):
    """
    Given a youtube id, returns the url to the
    thumbnail image

    :param v_id: Id of the youtube video
    :return: Url to the thumbnail
    """
    return "https://img.youtube.com/vi/{}/0.jpg".format(v_id)


def download_thumbnail(thumb_url):
    """
    Download a thumbnail from a url. Downloaded
    thumbnails are assigned a random name

    :param thumn_url: Url of the thumbnail
    :return: Filepath, including name, of saved thumbnail
    """
    result = requests.get(thumb_url)
    filepath = cwd + config.TEMP_THUMBNAIL_FOLDER + "/{}".format(random.random())

    create_dir_if_not_exist(cwd + config.TEMP_THUMBNAIL_FOLDER)

    f = open(filepath, "wb")
    f.write(result.content)
    f.close()
    return filepath


def get_metadata_from_youtube(video_id, artist_title_data):
    """
    Given a youtube video_id, attempts to extract metadata
    (Thumbnail, artist, name)

    :param video_id: Video id
    :param artist_title_data:
        A dictionary formatted like this:
        {
            "artist": Name of artist, extracted from title
            "title": Title of the song
        }
    :return: Dictionary containing metadata information
    """
    metadata = {
        "thumbnail": download_thumbnail(get_youtube_thumbnail_url(video_id)),
        "title": artist_title_data["title"],
        "artist": artist_title_data["artist"],
        "album": ""
    }
    return metadata


def get_metadata_obj(song_name, video_id):
    """
    Returns a metadata dictionary. Uses MUSIXMATCH API
    if an API key is provided

    :param song_name: Name of the song
    :param video_id: Video id
    :return: Dictionary containing metadata information
    """
    if " - " not in song_name:
        artist = "Unknown"
        title = song_name
    else:
        artist = song_name.split(" - ")[0]
        title = song_name.split(" - ")[1].replace(".mp3", "")
    artist_title_data = {
        "artist": artist,
        "title": title
    }

    if config.MUSIX_MATCH_API_KEY is None:
        return get_metadata_from_youtube(video_id, artist_title_data)

    # Attempt to obtain metadata from musixmatch
    url = "http://api.musixmatch.com/ws/1.1/track.search?q_track={}&apikey={}" \
        .format(urllib.parse.quote(song_name), config.MUSIX_MATCH_API_KEY)
    data = requests.get(url).json()

    if data["message"]["header"]["status_code"] == 200 or \
            len(data["message"]["body"]["track_list"]) == 0:
        return get_metadata_from_youtube(video_id, artist_title_data)

    res_data = data["message"]["body"]["track_list"][0]["track"]
    metadata = {
        "thumbnail":
            download_thumbnail(
                res_data["album_coverart_100x100"] or
                get_youtube_thumbnail_url(video_id)
            ),
        "title": artist_title_data["title"],
        "artist":
            res_data["artist_name"] if artist_title_data["artist"] == "Unknown"
            else artist_title_data["artist"],
        "album": res_data["album_name"]
    }
    return metadata


def add_metadata(mp3_dir, mp3_file_name, video_id):
    """
    Adds metadata to an mp3 file
    :param mp3_dir: Directory of the mp3 file (Including filename)
    :param mp3_file_name: Just the filename of the mp3 file
    :param video_id: Youtube video id mp3 was extracted from
    """

    metadata = get_metadata_obj(mp3_file_name, video_id)
    audio = MP3(mp3_dir, ID3=ID3)

    try:
        audio.add_tags()
    except:
        # Presumably would happen if the mp3
        # already had tags, but that shouldn't
        # be possible with our setup
        pass

    audio.tags.add(APIC(
        encoding=3,
        mime="image/jpeg",
        type=3,
        desc="Thumbnail",
        data=open(metadata["thumbnail"], "rb").read()
    ))
    audio.tags.add(TIT2(encoding=3, text=metadata["title"]))
    audio.tags.add(TALB(encoding=3, text=metadata["album"]))
    audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))

    audio.save()


def download_videos_and_convert_to_mp3(vid_ids):
    """
    Downloads an array of youtube video ids and converts
    to mp3

    :param vid_ids: Array of youtube video ids
    """

    count = 1
    total = len(vid_ids)
    dest = cwd + config.TEMP_MP4_FOLDER

    create_dir_if_not_exist(dest)

    for video in vid_ids:
        print("Downloading video ({} / {}) ({}%)".format(count, total, round(count / total * 100, 2)))

        stream = download_video(video, dest)
        clean_file_name = youtube_title_parse.get_artist_title(stream.default_filename) + ".mp4"
        file_path = dest + "/" + stream.default_filename

        # Sometimes youtube will download with ext already attached
        clean_file_name = clean_file_name.replace(".mp4.mp4", ".mp4")
        mp3_path = cwd + config.DEFAULT_OUTPUT_FOLDER + "/" + clean_file_name.replace(".mp4", ".mp3")

        # Fix for windows paths
        file_path = file_path.replace("\\", "/")
        mp3_path = mp3_path.replace("\\", "/")

        print("Converting file {} to mp3...".format(stream.default_filename))
        convert_mp4_to_mp3(
            file_path,
            mp3_path)

        print("Cleaning up metadata...")
        add_metadata(mp3_path, clean_file_name.replace(".mp4", ".mp3"), video)
        print("")

        count += 1

    # Clean up the folders (Get rid of temp files)
    print("Deleting temp folders...")
    shutil.rmtree(cwd + config.TEMP_THUMBNAIL_FOLDER)
    shutil.rmtree(cwd + config.TEMP_MP4_FOLDER)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("No arguments specified. Use -help to get help")
        sys.exit(1)
    elif sys.argv[1] == "-help":
        print(config.HELP_TEXT)
        sys.exit(0)
    else:
        url = sys.argv[1]
        ids = get_videos_in_playlist(url)

        if len(ids) == 0:
            print("Unknown or empty playlist. Check that your playlist url looks something like "
                + "https://www.youtube.com/playlist?list=<ID HERE>")
            sys.exit(1)

        choice = input("{} videos will be downloaded. Proceed? (Y/N)".format(len(ids)))
        if choice.lower() != "y":
            print("Quitting program...")
            sys.exit(1)

        print("Downloading! Your mp3 output will be available at {}".format(
            cwd + config.DEFAULT_OUTPUT_FOLDER
        ))
        print("This might take a while, leave it running.")
        print("")

        download_videos_and_convert_to_mp3(ids)
