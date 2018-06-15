# Youtube Music Playlist Downloader
A CLI python program to download youtube videos, convert them into mp3 and add metadata to create a music playlist.

### Requirements
- Python 3 with pip
- FFMPEG installed (Make sure you can run the command ffmpeg from the command line, if you're on Windows check your PATH)

Just as a heads up, the downloader keeps a temp folder of mp4 videos, which will **only be deleted once all mp3s have been finished.** If your computer has **very** little storage then you should be careful downloading large playlists or videos.

### Install
```
git clone https://github.com/Gavin-Song/Youtube-Music-Playlist-Downloader
cd Youtube-Music-Playlist-Downloader
pip install -r requirements.txt
```

You might also want to modify config.py
```python
TEMP_MP4_FOLDER = "/mp4"  # Relative to cwd
TEMP_THUMBNAIL_FOLDER = "/thumb"  # Relative to cwd
DEFAULT_OUTPUT_FOLDER = "/mp3"  # Relative to cwd

MUSIX_MATCH_API_KEY = None # Set to None to disable, should be a string
```

### Usage
(Assuming inside the Youtube-Music-Playlist-Downloader folder)
```
python __init__.py https://www.youtube.com/playlist?list=<YOUR PLAYLIST ID HERE>
```

In theory you could also import this module, as the code is divided into several potentially useful functions. Just look into `__init__.py`, everything you need is there.

### Future TODO
- Use youtube API to extract channel name as Artist
- Make interface more user friendly
- Threading or async downloading
- Customize output directory
- Delete videos and thumbnails as you go along to save storage

### LICENSE
Licensed under MIT (See LICENSE)

### Disclaimer
This program was created for educational purposes only. Please respect the copyright of any videos you download. The creator of this program will not be held liable for any copyright violations caused by the usage of this program.