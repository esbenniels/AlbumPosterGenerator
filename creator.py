import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import re
import matplotlib.image as img
from datetime import datetime, timedelta
import cv2
from cv2 import dnn_superres
import binascii
from PIL import Image, ImageFont, ImageDraw
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
        createAlbumPoster(url)
    elif "playlist" in url:
        createPlaylistPoster(url)
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
        # print(results['artists'][i]['name'], end="")
        build += results['artists'][i]['name']
        if not i == len(results['artists'])-1:
            build += ", "
    print("Artists:", build)
    print()
    print("Cover Art:", results['images'][0]['url'])
    # getTopColors(results['images'][0]['url'])

    # firstSong = results['tracks']['items'][0]
    # print(firstSong['href'])
    # print(firstSong['name'])
    # print(firstSong['id'])
    # print(firstSong['duration_ms'])

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
        'name': results['name'],
        'releaseDate': goodDate,
        'label': results['label'],
        'artists': build,
        'coverURL': results['images'][0]['url'],
        'fullLength': "01.15.03",
        'tracks': trackStruct
    }
    
    # https://open.spotify.com/album/5MS3MvWHJ3lOZPLiMxzOU6?si=6GDOWf7nSnaqsDa-BbIH5Q
    # https://open.spotify.com/playlist/4wuGkZLDCgKVttJtfLmVmg?si=e1bc1231cf974eb6

def getTopColors(online_url:str) -> list[list[int]]:
    

    NUM_CLUSTERS = 5

    bar = Bar("Finding dominant colors ", max=4)
    # urllib.request.urlretrieve(online_url, "album_cover.jpg")
    # bar.next()
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
    bar.next()
    hexes: list[str] = []
    for i in range(5):
        peak = codes[i]
        hexes.append("#"+binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii'))
    bar.next()
    sortedCodes = sorted(codes, key=lambda triple: sum(triple), reverse=True)
    print("\n{0:<7}{1:<7}{2:<7}{3:<7}{4:<7}".format("Color", "Red", "Green", "Blue", "Brightness"))
    for i in range(len(sortedCodes)):
        print("{0:<7}{1:<7.2f}{2:<7.2f}{3:<7.2f}{4:<7.2f}".format(i+1, sortedCodes[i][0], sortedCodes[i][1], sortedCodes[i][2], sum(sortedCodes[i])))
    return list(sortedCodes)

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

def getAlbumCover(url: str) -> Image:
    # coverURL = getAlbumDetails(url)['coverURL']
    urllib.request.urlretrieve(url, "album_cover.jpg")
    im = cv2.imread("album_cover.jpg")
    im = cv2.resize(im, (1166,1166), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite("album_cover.jpg", im)
    resizedCover = Image.open('album_cover.jpg')
    return resizedCover

def getSpotifyCode(url: str, sType: str = 'album') -> Image:
    albumID = re.findall(f'{sType}/(.*)\?', url)
    targetURL = 'https://scannables.scdn.co/uri/plain/png/FFFFFF/black/640/spotify:{}:{}'.format(sType ,albumID[0])
    print("Spotify Code URL: ", targetURL) 
    urllib.request.urlretrieve(targetURL, 'spotify_code.png')
    code = cv2.imread('spotify_code.png')
    code = cv2.resize(code, (444,111), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite('spotify_code.png', code)
    code = Image.open('spotify_code.png')
    return code

def getAlbumLength(trackStruct: list[dict]) -> str:
    totalMS = sum(song['duration'] for song in trackStruct)
    print("Total Album MS: ", totalMS)
    delta = timedelta(milliseconds=totalMS)
    min = delta.seconds // 60
    sec = delta.seconds % 60
    hr = delta.seconds // 3600
    return f"{hr:02d}.{min:02d}.{sec:01d}"

def createAlbumPoster(url):
    details = getAlbumDetails(url)

    # Full canvas
    canvas = Image.new('RGBA', (1333,2000), (255,255,255))
    # Getting album cover (640x640)
    albumCover = getAlbumCover(details['coverURL'])
    canvas.paste(albumCover, (83,83))
    # getting spotify code
    sCode = getSpotifyCode(url, 'album')
    canvas.paste(sCode, (805,1736))

    # handling color squares
    sortedRGB = getTopColors(url)
    coords = [(722,1270), (833,1270), (944,1270), (1056,1270), (1167,1270)]
    for i in range(5):
        # make square, place at correct location
        block = Image.new("RGBA", (83,83), (int(sortedRGB[i][0]), int(sortedRGB[i][1]), int(sortedRGB[i][2])))
        canvas.paste(block, coords[i])

    # Handling Label & Album Length
    draw = ImageDraw.Draw(canvas)
    boldText = ImageFont.truetype('SourceSans3-ExtraBold.ttf', 30)
    draw.text((83,1858), f"LABEL: {details['label'].upper()}", (0,0,0), font=boldText, anchor='lt')
    draw.text((83,1894), f"ALBUM LENGTH: {getAlbumLength(details['tracks'])}", (0,0,0), font=boldText, anchor='lt')

    draw.text((1250, 1858), f"RELEASED ON", (0,0,0), font=boldText, anchor='rt')
    draw.text((1250,1894), f"{details['releaseDate'].upper()}", (0,0,0), font=boldText, anchor='rt')

    canvas.save("firstTrial.png")


def createPlaylistPoster(url):
    pass

spotifyURL = input("Enter album or playlist URL: ")
handleURL(spotifyURL)
# getAlbumDetails(spotifyURL)