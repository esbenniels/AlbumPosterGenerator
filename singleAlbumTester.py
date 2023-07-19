import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import re
import matplotlib.image as img
from datetime import datetime, timedelta
import cv2
import binascii
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import scipy
import scipy.misc
import scipy.cluster
import urllib.request
from progress.bar import Bar

os.environ['SPOTIPY_CLIENT_ID'] = '56c47550643e42b9a6ab2aa821fe394c'
os.environ['SPOTIPY_CLIENT_SECRET'] = '0f26f4b32912427ca59b7c62d8c36b5a'

global defaultParams

defaultParams = {
    "coverDim" :1166,
    "codeDim" : 444,
    "cornerTextSize" : 30,
    "artistSize" : 57,
    "titleSize" : 79,
    "trackSize" : 26,
    "maxLabelLength" : 40,
    "maxArtistsLength" : 15,
    "maxTitleLength" : 11,
    "maxTrackLineWidth" : 15,
    "trackLineSpace" : 33,
    "maxTracks": 30
}


def handleURL(url: str, params: dict[str, int] = defaultParams, saveFolder: str = "", colors: list[tuple[int, int, int]] = None):
    if "album" in url:
        return getAlbumDetails(url)
    else:
        return "Not a Spotify playlist or poster URL"

def getAlbumDetails(url: str) -> dict:
    # fullURL = input("Enter spotify album url: ")
    albumID = re.findall('album/(.*)\?', url)
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    results = spotify.album(albumID[0])
    print(results['name'])
    release = datetime.strptime(results['release_date'], "%Y-%m-%d")
    print(results['release_date'])
    print(release.strftime("%d-%m-%Y"))
    newDay = release.strftime("%d")
    if newDay[0] == "0":
        newDay = newDay[1]
    goodDate = release.strftime("%B")+" "+newDay+", "+release.strftime("%Y")
    print(goodDate)
    print(results['label'])
    print("Artists: ", end="")
    build : str = ''
    for i in range(len(results['artists'])):
        print(results['artists'][i]['name'], end="")
        build += results['artists'][i]['name']
        if not i == len(results['artists'])-1:
            build += ", "
    print("Artists:", build)
    print("Cover Art:", results['images'][0]['url'])

    trackStruct: list[dict] = [
        {
            "href": song['href'],
            "name": song['name'],
            "id": song['id'],
            "duration": song['duration_ms']
        }
        for song in results['tracks']['items']
    ]

    return {
        'id': albumID,
        'name': results['name'],
        'releaseDate': goodDate,
        'label': results['label'],
        'artists': build,
        'coverURL': results['images'][0]['url'],
        'fullLength': "01.15.03",
        'tracks': trackStruct
    }

handleURL(input("URL: "))