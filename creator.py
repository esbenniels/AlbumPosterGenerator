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
    "numSquares": 5,
    "coverDim" :1166,
    "codeDim" : 444,
    "cornerTextSize" : 30,
    "artistSize" : 57,
    "titleSize" : 79,
    "trackSize" : 26,
    "maxLabelLength" : 30,
    "maxArtistsLength" : 15,
    "maxTitleLength" : 11,
    "maxTrackLineWidth" : 15,
    "trackLineSpace" : 33
}


def handleURL(url: str, params: dict[str, int] = defaultParams, saveFolder: str = ""):
    if "album" in url:
        createAlbumPoster(url, params, saveFolder)
    elif "playlist" in url:
        createPlaylistPoster(url, params, saveFolder)
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
    # print("Artists: ", end="")
    build : str = ''
    for i in range(len(results['artists'])):
        # print(results['artists'][i]['name'], end="")
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
        'name': results['name'],
        'releaseDate': goodDate,
        'label': results['label'],
        'artists': build,
        'coverURL': results['images'][0]['url'],
        'fullLength': "01.15.03",
        'tracks': trackStruct
    }
    
    # https://open.spotify.com/album/5MS3MvWHJ3lOZPLiMxzOU6?si=6GDOWf7nSnaqsDa-BbIH5Q

def getPlaylistDetails(url: str) -> dict:
    # https://open.spotify.com/playlist/4wuGkZLDCgKVttJtfLmVmg?si=e1bc1231cf974eb6
    albumID = re.findall('playlist/(.*)\?', url)
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    results = spotify.playlist(albumID[0])
    print(results['name'])
    pass

def getTopColors() -> list[list[int]]:
    
    NUM_CLUSTERS = defaultParams['numSquares']

    bar = Bar("Finding dominant colors ", max=4)
    im = Image.open("album_cover.jpg")
    bar.next()
    ar = np.asarray(im)
    shape = ar.shape
    ar = ar.reshape(np.prod(shape[:2]), shape[2]).astype(float)
    bar.next()
    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)
    bar.next()
    hexes: list[str] = []
    for i in range(len(codes)):
        peak = codes[i]
        hexes.append("#"+binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii'))
    bar.next()
    sortedCodes = sorted(codes, key=lambda triple: sum(triple))
    print("\n{0:<7}{1:<7}{2:<7}{3:<7}{4:<7}".format("Color", "Red", "Green", "Blue", "Brightness"))
    for i in range(len(sortedCodes)):
        print("{0:<7}{1:<7.2f}{2:<7.2f}{3:<7.2f}{4:<7.2f}".format(i+1, sortedCodes[i][0], sortedCodes[i][1], sortedCodes[i][2], sum(sortedCodes[i])))
    return list(sortedCodes)

def getAlbumCover(url: str) -> Image:
    urllib.request.urlretrieve(url, "album_cover.jpg")
    im = cv2.imread("album_cover.jpg")
    im = cv2.resize(im, (defaultParams['coverDim'],defaultParams['coverDim']), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite("album_cover.jpg", im)
    resizedCover = Image.open('album_cover.jpg')
    return resizedCover

def getSpotifyCode(url: str, sType: str = 'album') -> Image:
    albumID = re.findall(f'{sType}/(.*)\?', url)
    targetURL = 'https://scannables.scdn.co/uri/plain/png/FFFFFF/black/640/spotify:{}:{}'.format(sType ,albumID[0])
    print("Spotify Code URL: ", targetURL) 
    urllib.request.urlretrieve(targetURL, 'spotify_code.png')
    code = cv2.imread('spotify_code.png')
    code = cv2.resize(code, (defaultParams['codeDim'],int(defaultParams['codeDim']/4)), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite('spotify_code.png', code)
    code = Image.open('spotify_code.png')
    return code

def getAlbumLength(trackStruct: list[dict]) -> str:
    totalMS = sum(song['duration'] for song in trackStruct)
    print("Total Album MS: ", totalMS)
    delta = timedelta(milliseconds=totalMS)
    min = ((delta.seconds // 60)-60) if (delta.seconds // 60) >= 60 else (delta.seconds // 60)
    sec = delta.seconds % 60
    hr = delta.seconds // 3600
    return f"{hr:02d}.{min:02d}.{sec:02d}"

def writeCorners(draw: ImageDraw, details: dict):
    boldText = ImageFont.truetype('SourceSans3-ExtraBold.ttf', defaultParams['cornerTextSize'])
    artistFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['artistSize'])
    titleFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['titleSize'])
    if len(details['label'].upper()) <= defaultParams['maxLabelLength']:
        draw.text((83,1858), f"LABEL: {details['label'].upper()}", (0,0,0), font=boldText, anchor='lt')
    else:
        draw.text((83,1858), f"LABEL: {details['label'].upper()[:defaultParams['maxLabelLength']]+'...'}", (0,0,0), font=boldText, anchor='lt')
    draw.text((83,1894), f"ALBUM LENGTH: {getAlbumLength(details['tracks'])}", (0,0,0), font=boldText, anchor='lt')

    # Release Date Text
    draw.text((1250, 1858), f"RELEASED ON", (0,0,0), font=boldText, anchor='rt')
    draw.text((1250,1894), f"{details['releaseDate'].upper()}", (0,0,0), font=boldText, anchor='rt')

    # Artist Font
    if len(details['artists'].upper()) <= defaultParams['maxArtistsLength']:
        draw.text((1250, 1370), f"{details['artists'].upper()}", (0,0,0), font=artistFont, anchor='rt')
    else:
        draw.text((1250, 1370), f"{details['artists'].upper()[:defaultParams['maxArtistsLength']] + '...'}", (0,0,0), font=artistFont, anchor='rt')

    if len(details['name']) <= 10:
        draw.text((1250, 1427), f"{details['name'].upper()}", (0,0,0), font=titleFont, anchor='rt')
    else:
        name = details['name'].upper()
        words : list = name.split(' ')
        parts : list[str] = []
        
        build = ""
        while len(words) > 0:
            # print("considering ", words[0], "-->", build)
            if len(build + " " + words[0]) <= defaultParams['maxTitleLength']+(len(parts)):
                if len(build) == 0:
                    build += words[0]
                else:
                    build += " " + words[0]
                words.pop(0)
            else:
                if build == "":
                    parts.append(words[0])
                    words.pop(0)
                else:
                    parts.append(build)
                    build = ""
        parts.append(build)
        # print(parts)

        for j in range(len(parts)):
            draw.text((1250, 1427 + (j*82)), f"{parts[j]}", (0,0,0), font=titleFont, anchor='rt')

def writeTracks(draw: ImageDraw, details: dict):
    trackFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['trackSize'])
    trackList: list[str] = [song['name'].upper() for song in details['tracks']]
    i = 1
    nextY = 1270
    NUMX1 = 83
    NUMX2 = 400
    TRACKX1 = 126
    TRACKX2 = 442
    column = 1
    for track in trackList:
        try:
            pIndex = track.index("(")
            track = track[:pIndex]
        except:
            pass

        # splitting track into parts to print
        parts : list[str] = []
        words = track.split()
        
        build = ""
        while len(words) > 0:
            if len(build + " " + words[0]) <= defaultParams['maxTrackLineWidth']:
                if len(build) == 0:
                    build += words[0]
                else:
                    build += " " + words[0]
                words.pop(0)
            else:
                if build == "":
                    parts.append(words[0])
                    words.pop(0)
                else:
                    parts.append(build)
                    build = ""
        parts.append(build)

        # column check
        if nextY+(len(parts)*defaultParams['trackLineSpace']) > 1798:
            column += 1
            nextY = 1270

        # writing track number
        if column == 1:
            draw.text((NUMX1, nextY), f"{i}", (0,0,0), font=trackFont, anchor='lt')
        else:
            draw.text((NUMX2, nextY), f"{i}", (0,0,0), font=trackFont, anchor='lt')

        
        # writing tracks to text boxes
        for j in range(len(parts)):
            if column == 1:
                draw.text((TRACKX1, nextY), f"{parts[j]}", (0,0,0), font=trackFont, anchor='lt')
            else:
                draw.text((TRACKX2, nextY), f"{parts[j]}", (0,0,0), font=trackFont, anchor='lt')
            nextY += defaultParams['trackLineSpace']
        
        i += 1

def createAlbumPoster(url: str, params: dict[str, int] = defaultParams, saveFolder: str = ""):
    details = getAlbumDetails(url)

    global defaultParams
    defaultParams = params

    # Full canvas
    canvas = Image.new('RGBA', (1333,2000), (255,255,255))
    # Getting album cover (640x640)
    albumCover = getAlbumCover(details['coverURL'])
    canvas.paste(albumCover, (83,83))
    # getting spotify code
    sCode = getSpotifyCode(url, 'album')
    canvas.paste(sCode, (805,1736))

    # handling color squares
    sortedRGB = getTopColors()
    coords = [(1167,1270), (1056,1270), (944,1270), (833,1270), (722,1270) ]
    for i in range(len(sortedRGB)):
        # make square, place at correct location
        block = Image.new("RGBA", (83,83), (int(sortedRGB[i][0]), int(sortedRGB[i][1]), int(sortedRGB[i][2])))
        canvas.paste(block, coords[i])

    # Handling Label & Album Length
    draw = ImageDraw.Draw(canvas)
    writeCorners(draw, details)

    # Handling tracks
    writeTracks(draw, details)

    canvas.save(f"static/PosterStorage{saveFolder}/poster.png")

def createPlaylistPoster(url: str, params: dict[str, int] = defaultParams, saveFolder: str = ""):
    global defaultParams
    defaultParams = params

    details = getPlaylistDetails(url)
    # Full canvas
    canvas = Image.new('RGBA', (1333,2000), (255,255,255))

# spotifyURL = input("Enter album or playlist URL: ")
# handleURL(spotifyURL)
# getAlbumDetails(spotifyURL)