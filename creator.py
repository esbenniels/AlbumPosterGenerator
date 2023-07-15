import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import re
import matplotlib.image as img
from datetime import datetime
import cv2
from cv2 import dnn_superres
import binascii
from PIL import Image
import numpy as np
import scipy
import scipy.misc
import scipy.cluster
import urllib.request
from progress.bar import Bar
from progress.spinner import MoonSpinner

os.environ['SPOTIPY_CLIENT_ID'] = '56c47550643e42b9a6ab2aa821fe394c'
os.environ['SPOTIPY_CLIENT_SECRET'] = '0f26f4b32912427ca59b7c62d8c36b5a'

# def getAllArtistAlbums():
#     artist_uri = 'spotify:artist:3TVXtAsR1Inumwj472S9r4'
#     spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

#     results = spotify.artist_albums(artist_uri, album_type='album')
#     albums = results['items']
#     while results['next']:
#         results = spotify.next(results)
#         albums.extend(results['items'])

#     for album in albums:
#         print(album['name'])

def handleURL(url: str):
    if "album" in url:
        createAlbumPoster()
    elif "playlist" in url:
        createPlaylistPoster()
    else:
        return "Not a Spotify playlist or poster URL"

def getAlbumDetails():
    fullURL = input("Enter spotify album url: ")
    albumID = re.findall('album/(.*)\?', fullURL)
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
    for i in range(len(results['artists'])):
        print(results['artists'][i]['name'], end="")
        if not i == len(results['artists'])-1:
            print(", ", end="")
    print()
    print("Cover Art:", results['images'][0]['url'])
    getTopColors(results['images'][0]['url'])
    
    # https://open.spotify.com/album/5MS3MvWHJ3lOZPLiMxzOU6?si=6GDOWf7nSnaqsDa-BbIH5Q
    # https://open.spotify.com/playlist/4wuGkZLDCgKVttJtfLmVmg?si=e1bc1231cf974eb6

def getTopColors(online_url:str):
    

    NUM_CLUSTERS = 5

    bar = Bar("Finding dominant colors ", max=5)
    urllib.request.urlretrieve(online_url, "album_cover.jpg")
    bar.next()
    # print('reading image')
    im = Image.open("album_cover.jpg")
    bar.next()
    # im = im.resize((150, 150))      # optional, to reduce time
    ar = np.asarray(im)
    shape = ar.shape
    ar = ar.reshape(np.prod(shape[:2]), shape[2]).astype(float)
    bar.next()
    # print('finding clusters')
    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)
    # print('cluster centres:\n', codes)
    bar.next()
    hexes: list[str] = []
    for i in range(5):
        peak = codes[i]
        hexes.append("#"+binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii'))
    bar.next()
    print("\nMost common colors: ", hexes)

def upscaleAlbumCover():
    print("Upscaling Image ... ")
    print("Creating dnn_superres object ... ")
    sr = dnn_superres.DnnSuperResImpl.create()
    image = cv2.imread('album_cover.jpg')
    path = "EDSR_x4.pb"
    print("Reading model ... ")
    sr.readModel(path)
    sr.setModel("edsr", 2)
    print("Upsampling ... ")
    result = sr.upsample(image)
    print("Saving image ... ")
    cv2.imwrite("album_cover_upscaled.png", result)

def generateImage():
    pass

# getAlbumDetails()
# upscaleAlbumCover()

def createAlbumPoster():
    pass
def createPlaylistPoster():
    pass