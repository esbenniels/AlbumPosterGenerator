import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os, re, json
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
    "maxTracks": 30,
    "sCodePos": 1736,
    "includeFullTitle": 0
}

class ProgressBar(Bar):
    message = "Generating Album Poster ... "
    fill = "#"
    suffix = "%(index)d/%(max)d --> %(current_status)s"
    def setStatus(self, name:str):
        self.status = name
    @property
    def current_status(self):
        return self.status


def handleURL(url: str, params: dict[str, int] = defaultParams, saveFolder: str = "", 
              colors: list[tuple[int, int, int]] = None) -> None | list[list[int]] | str:
    global bar, startTime
    bar = ProgressBar(max=9)
    if "album" in url:
        return createAlbumPoster(url, params, saveFolder, colors)
    elif "playlist" in url:
        return createPlaylistPoster(url, params, saveFolder, colors)
    else:
        return "Not a Spotify playlist or poster URL"

def getAlbumDetails(url: str) -> dict:
    # fullURL = input("Enter spotify album url: ")
    albumID = re.findall('album/(.*)\?', url)
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    results = spotify.album(albumID[0])
    # print(results['name'])
    release = datetime.strptime(results['release_date'], "%Y-%m-%d")
    # print(results['release_date'])
    # print(release.strftime("%d-%m-%Y"))
    newDay = release.strftime("%d")
    if newDay[0] == "0":
        newDay = newDay[1]
    goodDate = release.strftime("%B")+" "+newDay+", "+release.strftime("%Y")
    # print(goodDate)
    # print(results['label'])
    # print("Artists: ", end="")
    build : str = ''
    for i in range(len(results['artists'])):
        # print(results['artists'][i]['name'], end="")
        build += results['artists'][i]['name']
        if not i == len(results['artists'])-1:
            build += ", "
    # print("Artists:", build)
    # print("Cover Art:", results['images'][0]['url'])

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
        'id': albumID[0],
        'name': results['name'],
        'releaseDate': goodDate,
        'label': results['label'],
        'artists': build,
        'coverURL': results['images'][0]['url'],
        'fullLength': "01.15.03",
        'tracks': trackStruct
    }
    
    # https://open.spotify.com/album/5MS3MvWHJ3lOZPLiMxzOU6?si=6GDOWf7nSnaqsDa-BbIH5Q

def getPlaylistDetails(url:str) -> dict:
    playlistID = re.findall('playlist/(.*)\?', url)
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    results = spotify.playlist(playlistID[0])
    tracks: list = spotify.playlist_tracks(playlistID[0], fields = None, limit=100, offset=0)['items']
    # print("Number of tracks from playlist_tracks: ", len(tracks['items']))
    # print(tracks)
    i = 1
    while len(tracks) % 100 == 0:
        newTracks = spotify.playlist_tracks(playlistID[0], fields = None, limit=100, offset=i*100)['items']
        tracks += newTracks
        i += 1


    totalDuration = sum([song['track']['duration_ms'] for song in tracks])

    artistDict: dict=  {}

    trackStruct : list[dict] = [
        {
            "href": song['track']['href'],
            "name": song['track']['name'],
            "id": song['track']['id'],
            "duration": song['track']['duration_ms'],
            "artists": [artist['name'] for artist in song['track']['artists']]
        }
        for song in tracks
    ]

    for song in trackStruct:
        for artist in song['artists']:
            if artist in artistDict:
                artistDict[artist] += 1
            else:
                artistDict[artist] = 1

    sortArtists = sorted(artistDict.items(), key=lambda pair: pair[1], reverse=True)
    print("Total Tracks: ", len(trackStruct))
    print("Top Artists: ", sortArtists[:min(3, len(sortArtists))])

    return {
        "id": playlistID[0],
        'name': results['name'],
        'owner': results['owner']['display_name'],
        'description': results['description'],
        'length': totalDuration,
        'coverURL': results['images'][0]['url'],
        'tracks': trackStruct,
        'topArtists': sortArtists[:min(3, len(sortArtists))]
    }

def getTopColors(sType: str = "album") -> list[list[int]]:
    
    NUM_CLUSTERS = 5

    # bar = Bar("Finding dominant colors ", max=4)
    im = Image.open(f"{sType}_cover.jpg")
    # bar.next()
    ar = np.asarray(im)
    shape = ar.shape
    ar = ar.reshape(np.prod(shape[:2]), shape[2]).astype(float)
    # bar.next()
    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)
    # bar.next()
    hexes: list[str] = []
    for i in range(len(codes)):
        peak = codes[i]
        hexes.append("#"+binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii'))
    # bar.next()
    sortedCodes = sorted(codes, key=lambda triple: sum(triple))
    for i in range(len(sortedCodes)):
        for j in range(3):
            sortedCodes[i][j] = int(round(sortedCodes[i][j],0))

    # print("\n{0:<7}{1:<7}{2:<7}{3:<7}{4:<7}".format("Color", "Red", "Green", "Blue", "Brightness"))
    # for i in range(len(sortedCodes)):
        # print("{0:<7}{1:<7.2f}{2:<7.2f}{3:<7.2f}{4:<7.2f}".format(i+1, sortedCodes[i][0], sortedCodes[i][1], sortedCodes[i][2], sum(sortedCodes[i])))
    return list(sortedCodes)

def getTopColorsAlone(url: str) -> list[list[int]]:
    NUM_CLUSTERS = 5

    # bar = Bar("Finding dominant colors ", max=4)
    albumID = re.findall('album/(.*)\?', url)
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    results = spotify.album(albumID[0])
    coverURL = results['images'][0]['url']
    urllib.request.urlretrieve(coverURL, "album_cover.jpg")
    im = Image.open("album_cover.jpg")
    # bar.next()
    ar = np.asarray(im)
    shape = ar.shape
    ar = ar.reshape(np.prod(shape[:2]), shape[2]).astype(float)
    # bar.next()
    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)
    # bar.next()
    hexes: list[str] = []
    for i in range(len(codes)):
        peak = codes[i]
        hexes.append("#"+binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii'))
    # bar.next()
    sortedCodes = sorted(codes, key=lambda triple: sum(triple))
    for i in range(len(sortedCodes)):
        for j in range(3):
            sortedCodes[i][j] = int(round(sortedCodes[i][j],0))

    # print("\n{0:<7}{1:<7}{2:<7}{3:<7}{4:<7}".format("Color", "Red", "Green", "Blue", "Brightness"))
    # for i in range(len(sortedCodes)):
        # print("{0:<7}{1:<7.2f}{2:<7.2f}{3:<7.2f}{4:<7.2f}".format(i+1, sortedCodes[i][0], sortedCodes[i][1], sortedCodes[i][2], sum(sortedCodes[i])))
    return list(sortedCodes)

def getCover(url: str, sType: str = 'album') -> Image:
    urllib.request.urlretrieve(url, f"{sType}_cover.jpg")
    im = cv2.imread(f"{sType}_cover.jpg")
    im = cv2.resize(im, (defaultParams['coverDim'],defaultParams['coverDim']), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(f"{sType}_cover.jpg", im)
    resizedCover = Image.open(f"{sType}_cover.jpg")
    return resizedCover

def getSpotifyCode(url: str, sType: str = 'album') -> Image:
    albumID = re.findall(f'{sType}/(.*)\?', url)
    targetURL = 'https://scannables.scdn.co/uri/plain/png/FFFFFF/black/640/spotify:{}:{}'.format(sType ,albumID[0])
    # print("Spotify Code URL: ", targetURL) 
    urllib.request.urlretrieve(targetURL, 'spotify_code.png')
    code = cv2.imread('spotify_code.png')
    code = cv2.resize(code, (defaultParams['codeDim'],int(defaultParams['codeDim']/4)), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite('spotify_code.png', code)
    code = Image.open('spotify_code.png')
    return code

def getLength(trackStruct: list[dict]) -> str:
    totalMS = sum(song['duration'] for song in trackStruct)
    # print("Total Album MS: ", totalMS)
    delta = timedelta(milliseconds=totalMS)
    min = (delta.seconds // 60)-((delta.seconds // 3600)*60) if (delta.seconds // 60) >= 60 else (delta.seconds // 60)
    sec = delta.seconds % 60
    hr = delta.seconds // 3600
    return f"{hr:02d}.{min:02d}.{sec:02d}"

def writeText(draw: ImageDraw, details: dict) -> None:
    boldText = ImageFont.truetype('SourceSans3-ExtraBold.ttf', defaultParams['cornerTextSize'])
    artistFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['artistSize'])
    titleFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['titleSize'])
    if len(details['label'].upper()) <= defaultParams['maxLabelLength']:
        draw.text((83,1858), f"LABEL: {details['label'].upper()}", (0,0,0), font=boldText, anchor='lt')
    else:
        draw.text((83,1858), f"LABEL: {details['label'].upper()[:defaultParams['maxLabelLength']]+'...'}", (0,0,0), font=boldText, anchor='lt')
    draw.text((83,1894), f"ALBUM LENGTH: {getLength(details['tracks'])}", (0,0,0), font=boldText, anchor='lt')

    # Release Date Text
    draw.text((1250, 1858), f"RELEASED ON", (0,0,0), font=boldText, anchor='rt')
    draw.text((1250,1894), f"{details['releaseDate'].upper()}", (0,0,0), font=boldText, anchor='rt')

    # Artist Font
    if len(details['artists'].upper()) <= defaultParams['maxArtistsLength']:
        draw.text((1250, 1370), f"{details['artists'].upper()}", (0,0,0), font=artistFont, anchor='rt')
    else:
        draw.text((1250, 1370), f"{details['artists'].upper()[:defaultParams['maxArtistsLength']] + '...'}", (0,0,0), font=artistFont, anchor='rt')

    if defaultParams['includeFullTitle'] == 0:
        try:
            pIndex = details['name'].index("(")
            details['name'] = details['name'][:pIndex]
        except:
            pass

    if len(details['name']) <= 10:
        draw.text((1250, 1435), f"{details['name'].upper()}", (0,0,0), font=titleFont, anchor='rt')
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
            draw.text((1250, 1435 + (j*82)), f"{parts[j]}", (0,0,0), font=titleFont, anchor='rt')

def writePlaylistText(draw: ImageDraw, details: dict) -> None:
    boldText = ImageFont.truetype('SourceSans3-ExtraBold.ttf', defaultParams['cornerTextSize'])
    artistFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['artistSize'])
    titleFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['titleSize'])

    topArtistsString = details['topArtists'][0][0]
    for i in range(1, len(details['topArtists'])):
        topArtistsString += ", "+details['topArtists'][i][0].upper()

    if len(topArtistsString.upper()) <= defaultParams['maxLabelLength']:
        draw.text((83,1858), f"TOP ARTISTS: {topArtistsString.upper()}", (0,0,0), font=boldText, anchor='lt')
    else:
        draw.text((83,1858), f"TOP ARTISTS: {topArtistsString.upper()[:defaultParams['maxLabelLength']]+'...'}", (0,0,0), font=boldText, anchor='lt')
    draw.text((83,1894), f"PLAYLIST LENGTH: {getLength(details['tracks'])}", (0,0,0), font=boldText, anchor='lt')

    # Writing description

    if len(details['description']) <= 40:
        draw.text((1250, 1858), f"{details['description'].upper()}", (0,0,0), font=ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", 20), anchor='rt')
    else:
        name = details['description'].upper()
        words : list = name.split(' ')
        parts : list[str] = []
        
        build = ""
        while len(words) > 0:
            # print("considering ", words[0], "-->", build)
            if len(build + " " + words[0]) <= 40:
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
            draw.text((1250, 1858 + (j*24)), f"{parts[j]}", (0,0,0), font=ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", 20), anchor='rt')

    # draw.text((1250, 1858), details['description'], (0,0,0), font=ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", 18), anchor='rt')
    # draw.text((1250,1894), f"{details['releaseDate'].upper()}", (0,0,0), font=boldText, anchor='rt')

    # Artist Font
    if len(details['owner'].upper()) <= defaultParams['maxArtistsLength']:
        draw.text((1250, 1370), f"{details['owner'].upper()}", (0,0,0), font=artistFont, anchor='rt')
    else:
        draw.text((1250, 1370), f"{details['owner'].upper()[:defaultParams['maxArtistsLength']] + '...'}", (0,0,0), font=artistFont, anchor='rt')

    if defaultParams['includeFullTitle'] == 0:
        try:
            pIndex = details['name'].index("(")
            details['name'] = details['name'][:pIndex]
        except:
            pass

    if len(details['name']) <= 10:
        draw.text((1250, 1435), f"{details['name'].upper()}", (0,0,0), font=titleFont, anchor='rt')
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
            draw.text((1250, 1435 + (j*82)), f"{parts[j]}", (0,0,0), font=titleFont, anchor='rt')
    
def writeTracks(draw: ImageDraw, details: dict) -> None:
    trackFont = ImageFont.truetype("AtkinsonHyperlegible-Bold.ttf", defaultParams['trackSize'])
    trackList: list[str] = [song['name'].upper() for song in details['tracks']]
    i = 1
    nextY = 1270
    NUMX1 = 83
    NUMX2 = 400
    TRACKX1 = 126
    TRACKX2 = 442
    column = 1
    notEnough = False
    for track in trackList:
        if i > defaultParams['maxTracks']:
            notEnough = True
            break
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
            # next word is too long to fully include
            else:
                # if this is the first word in a line, it will therefore take up the whole line
                if build == "":
                    # print("Entered special case for ", words[0])
                    build = words[0]
                    while len(build) > defaultParams['maxTrackLineWidth']:
                        parts.append(build[:defaultParams['maxTrackLineWidth']])
                        build = build[defaultParams['maxTrackLineWidth']:]
                    parts.append(build)
                    words.pop(0)
                    build = ""
                else:
                    parts.append(build)
                    build = ""
        if build != "":
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

    if notEnough:
        if column == 1:
            draw.text((TRACKX1, nextY), ". . .", (0,0,0), font=trackFont, anchor = 'lt')
        else:
            draw.text((TRACKX2, nextY), ". . .", (0,0,0), font=trackFont, anchor = 'lt')


def createAlbumPoster(url: str, params: dict[str, int] = defaultParams, 
                      saveFolder: str = "", 
                      colors: list[list[int]] = None) -> None | list[list[int]]:
    details = getAlbumDetails(url)

    global defaultParams, bar
    defaultParams = params

    # Full canvas
    bar.setStatus("Creating canvas ... ")
    bar.update()
    canvas = Image.new('RGBA', (1333,2000), (255,255,255))
    bar.next()
    # Getting album cover (640x640)
    bar.setStatus("Getting album cover ... ")
    bar.update()
    albumCover = getCover(details['coverURL'], 'album')
    canvas.paste(albumCover, (83,83))
    bar.next()
    # getting spotify code
    bar.setStatus("Getting spotify code ... ")
    bar.update()
    sCode = getSpotifyCode(url, 'album')
    canvas.paste(sCode, (805,defaultParams['sCodePos']))
    bar.next()

    returning = None

    # handling color squares
    bar.setStatus("Generating colors squares ... ")
    bar.update()
    if colors:
        # print("Colors passed in from database")
        sortedRGB = sorted(colors, key=lambda triple: sum(triple))
        # print("\n{0:<7}{1:<7}{2:<7}{3:<7}{4:<7}".format("Color", "Red", "Green", "Blue", "Brightness"))
        # for i in range(len(sortedRGB)):
            # print("{0:<7}{1:<7.2f}{2:<7.2f}{3:<7.2f}{4:<7.2f}".format(i+1, sortedRGB[i][0], sortedRGB[i][1], sortedRGB[i][2], sum(sortedRGB[i])))
    else:
        # print("No colors passed from database")
        sortedRGB = getTopColors()
        returning = sortedRGB
    coords = [(1167,1270), (1056,1270), (944,1270), (833,1270), (722,1270) ]
    for i in range(len(sortedRGB)):
        # make square, place at correct location
        block = Image.new("RGBA", (83,83), (int(sortedRGB[i][0]), int(sortedRGB[i][1]), int(sortedRGB[i][2])))
        canvas.paste(block, coords[i])
    bar.next()

    # Handling Label & Album Length
    bar.setStatus("Writing album info ... ")
    bar.update()
    draw = ImageDraw.Draw(canvas)
    writeText(draw, details)
    bar.next()

    # Handling tracks
    bar.setStatus("Writing album tracks ... ")
    bar.update()
    writeTracks(draw, details)
    bar.next()

    # save temporary full-size copy
    bar.setStatus("Saving album poster ... ")
    bar.update()
    canvas.save(f"static/PosterStorage{saveFolder}/poster.png")
    bar.next()
    # saving permanent thumbnail copy for lesser storage use
    bar.setStatus("Saving thumbnail copy ... ")
    bar.update()
    thumbnail = cv2.imread(f"static/PosterStorage{saveFolder}/poster.png")
    thumbnail = cv2.resize(thumbnail, (500, 750), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(f"static/PosterStorage{saveFolder}/{details['id']}.png", thumbnail)
    bar.next()

    # print("Returning from handleURL: ", returning)
    bar.setStatus("Writing to data.json ... ")
    bar.update()
    with open(f"static/PosterStorage{saveFolder}/data.json", 'r+') as handle:
        data: dict = json.load(handle)
        data[details['id']] = params
        data[details['id']]['lastModified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data[details['id']]['type'] = "album"
        data[details['id']]['name'] = details['name']
        id=re.findall('album/(.*)\?', url)[0]
        data[details['id']]['url'] = f"album/{id}?"
        handle.close()
    with open(f"static/PosterStorage{saveFolder}/data.json", 'w+') as handle:
        handle.write(json.dumps(data, indent=4))
        handle.close()
    bar.next()
    bar.finish()
    return returning

def createPlaylistPoster(url: str, params: dict[str, int] = defaultParams, 
                         saveFolder: str = "", 
                         colors: list[list[int]] = None) -> None | list[list[int]]:
    details = getPlaylistDetails(url)

    global defaultParams, bar
    defaultParams = params

    # Full canvas
    bar.setStatus("Creating canvas ... ")
    bar.update()
    canvas = Image.new('RGBA', (1333,2000), (255,255,255))
    bar.next()
    # Getting album cover (640x640)
    bar.setStatus("Getting playlist cover ... ")
    bar.update()
    playCover = getCover(details['coverURL'], 'playlist')
    canvas.paste(playCover, (83,83))
    bar.next()
    # getting spotify code
    bar.setStatus("Getting spotify code ... ")
    bar.update()
    sCode = getSpotifyCode(url, 'playlist')
    canvas.paste(sCode, (805,defaultParams['sCodePos']))
    bar.next()

    returning = None

    # handling color squares
    bar.setStatus("Generating colors squares ... ")
    bar.update()
    if colors:
        # print("Colors passed in from database")
        sortedRGB = sorted(colors, key=lambda triple: sum(triple))
        # print("\n{0:<7}{1:<7}{2:<7}{3:<7}{4:<7}".format("Color", "Red", "Green", "Blue", "Brightness"))
        # for i in range(len(sortedRGB)):
            # print("{0:<7}{1:<7.2f}{2:<7.2f}{3:<7.2f}{4:<7.2f}".format(i+1, sortedRGB[i][0], sortedRGB[i][1], sortedRGB[i][2], sum(sortedRGB[i])))
    else:
        # print("No colors passed from database")
        sortedRGB = getTopColors('playlist')
        returning = sortedRGB
    coords = [(1167,1270), (1056,1270), (944,1270), (833,1270), (722,1270) ]
    for i in range(len(sortedRGB)):
        # make square, place at correct location
        block = Image.new("RGBA", (83,83), (int(sortedRGB[i][0]), int(sortedRGB[i][1]), int(sortedRGB[i][2])))
        canvas.paste(block, coords[i])
    bar.next()

    # Handling Label & Album Length
    bar.setStatus("Writing playlist info ... ")
    bar.update()
    draw = ImageDraw.Draw(canvas)
    writePlaylistText(draw, details)
    bar.next()

    # Handling tracks
    bar.setStatus("Writing playlist tracks ... ")
    bar.update()
    writeTracks(draw, details)
    bar.next()

    # save temporary full-size copy
    bar.setStatus("Saving playlist poster ... ")
    bar.update()
    canvas.save(f"static/PosterStorage{saveFolder}/poster.png")
    bar.next()
    # saving permanent thumbnail copy for lesser storage use
    bar.setStatus("Saving thumbnail copy ... ")
    bar.update()
    thumbnail = cv2.imread(f"static/PosterStorage{saveFolder}/poster.png")
    thumbnail = cv2.resize(thumbnail, (500, 750), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(f"static/PosterStorage{saveFolder}/{details['id']}.png", thumbnail)
    bar.next()

    # print("Returning from handleURL: ", returning)
    bar.setStatus("Writing to data.json ... ")
    bar.update()
    with open(f"static/PosterStorage{saveFolder}/data.json", 'r+') as handle:
        data: dict = json.load(handle)
        data[details['id']] = params
        data[details['id']]['lastModified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data[details['id']]['type'] = "playlist"
        data[details['id']]['name'] = details['name']
        id=re.findall('playlist/(.*)\?', url)[0]
        data[details['id']]['url'] = f"playlist/{id}?"
        handle.close()
    with open(f"static/PosterStorage{saveFolder}/data.json", 'w+') as handle:
        handle.write(json.dumps(data, indent=4))
        handle.close()
    bar.next()
    bar.finish()
    return returning

    # https://open.spotify.com/playlist/37i9dQZF1DXdyjMX5o2vCq?si=eeb678ba212b4b71


def create16x20(im1: Image, im2: Image, im3: Image, saveFolder: str = "") -> None:
    canvas = Image.new('RGBA', (2666,3333), (255,255,255))
    canvas.paste(Image.fromarray(np.asarray(im1)), (0,0))
    canvas.paste(Image.fromarray(np.asarray(im2)), (1333, 0))
    canvas.paste(Image.fromarray(np.asarray(im3)).rotate(90, expand=True), (333, 2000))
    canvas.save(f"static/PosterStorage{saveFolder}/16x20.png")