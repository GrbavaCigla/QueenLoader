"""
Python project to download all songs from one artist
"""
import os
import sys
from bs4 import BeautifulSoup, element
import requests
import pafy
import eyed3
from pydub import AudioSegment

def video_search(text_to_search, video_id=0):
    """Searches for videos on youtube

    :param text_to_search: keywords for searching
    :param video_id: id of video to return (default=0)
    :returns: url of video or None if status_code is not 200

    """

    response = requests.get(
        "https://www.youtube.com/results?search_query=" +
        text_to_search
    )

    if not response.status_code == 200:
        return None

    soap = BeautifulSoup(response.text, 'html.parser')
    videos = soap.findAll("a", attrs={"class": "yt-uix-tile-link"})
    return "https://www.youtube.com" + videos[video_id]["href"]

def check_song_table(tag):
    """BeautifulSoup function that checks the right table
    :param tag: HTML tag to be checked
    :return: bool
    """

    classes = \
    [
        "wikitable",
        "sortable",
        "plainrowheaders"
    ]
    return tag.name == "table" and tag.get("class") == classes




if len(sys.argv) != 3:
    print("Usage: ./queen.py (ARTIST) (WIKI URL \"https://.../Songs recorded by ...\")")
    sys.exit(1)

WIKI_URL = sys.argv[2]
ARTIST = sys.argv[1]

wiki_response = requests.get(WIKI_URL)
if not wiki_response.status_code == 200:
    print("Wiki URL is not valid!")
    sys.exit(1)

soup = BeautifulSoup(wiki_response.text, features="lxml")
tables = soup.find_all(check_song_table)

rows = [row for table in tables for row in table.tbody]

columns = {}
title_column = 0
song_num = 0
failed = []

try:
    os.mkdir("./songs")
except:
    pass

for row in rows:
    if isinstance(row, element.Tag):
        if row.th.get("scope") == "col":
            columns.clear()
            columns_temp = row.text.split("\n")
            columns_temp = list(filter(bool, columns_temp))

            for i, j in enumerate(columns_temp):
                if "title" in j.lower() or "song" in j.lower():
                    columns[i] = ["title"]
                    title_column = i
                elif "album" in j.lower() or "original release" == j.lower():
                    columns[i] = ["album"]
                elif "year" in j.lower():
                    columns[i] = [
                        "release_date", 
                        "original_release_date",
                        "recording_date"
                    ]
                elif "writer" in j.lower() or "composer" in j.lower():
                    columns[i] = ["composer"]
        else:
            columns_temp = row.text.split("\n")
            columns_temp = list(filter(bool, columns_temp))

            song_name = columns_temp[title_column].replace("\"","").strip()
            try:
                youtube_url = video_search(song_name + " " + ARTIST +" lyrics")
            except:
                failed.append(song_name)
                continue


            if youtube_url:
                try:
                    audio = pafy.new(youtube_url).getbestaudio()

                    path = "./songs/{}.{}".format(song_name, audio.extension)
                    new_path = "./songs/{}.mp3".format(song_name)

                    audio.download(
                        filepath=path,
                        quiet=True
                    )

                    webm_audio = AudioSegment.from_file(path, format=audio.extension)
                    webm_audio.export(new_path, format="mp3")

                    audiofile = eyed3.load(new_path)
                    for k, v in columns.items():
                        for i in v:
                            setattr(audiofile.tag, i, columns_temp[k].replace("\"","").strip())
                    audiofile.tag.artist = ARTIST
                    audiofile.tag.album_artist = ARTIST 

                    audiofile.tag.save()
                except:
                    failed.append(song_name)
            else:
                failed.append(song_name)

print(*failed, sep="\n")
