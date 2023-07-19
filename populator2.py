import requests
from bs4 import BeautifulSoup

def scrape_spotify_links():
    with open("spotifycharts.html", 'r') as chartsScrape:
        soup = BeautifulSoup(chartsScrape, 'html.parser')
    spotify_links = []

    albums = soup.find_all("tr")
    # print(len(albums))
    for album in albums:
        spotify_link = album.find("a")
        if spotify_link:
            spotify_links.append(spotify_link["href"])

    return spotify_links

# Example usage
albums = scrape_spotify_links()
print(albums)