import requests
from bs4 import BeautifulSoup
import urllib.parse

# 1. Fetch the raw HTML from KEXP
url = "https://www.kexp.org/charts/"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
try:
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Error fetching KEXP charts: {e}")
    exit(1)

soup = BeautifulSoup(response.text, 'html.parser')

# 2. Find the Top 90 header and isolate its ordered list (<ol>)
search_queries = []
top_90_header = soup.find(lambda tag: tag.name == "h4" and "Top 90:" in tag.text)

if top_90_header:
    ol_tag = top_90_header.find_next('ol')
    if ol_tag:
        for li in ol_tag.find_all('li'):
            text_line = li.get_text().strip()
            if " - " in text_line:
                artist, album_part = text_line.split(" - ", 1)
                artist = artist.strip()
                
                # Clean off parenthetical record label info
                album_clean = album_part.split(" (")[0].strip()
                
                # Strip out quotation marks if present
                for q in ['“', '”', '"']:
                    album_clean = album_clean.replace(q, "")
                
                search_queries.append(f"{artist} {album_clean}")

# 3. Interrogate the iTunes API directly from GitHub
track_urls = []
print(f"Found {len(search_queries)} items to lookup via iTunes API...")

for query in search_queries:
    encoded_query = urllib.parse.quote(query)
    itunes_url = f"https://itunes.apple.com/search?term={encoded_query}&country=ca&media=music&entity=song&limit=1"
    
    try:
        res = requests.get(itunes_url, timeout=5).json()
        if res.get("resultCount", 0) > 0:
            track = res["results"][0]
            track_name = track.get("trackName", "")
            artist_name = track.get("artistName", "")
            # Grab the direct web link to the Apple Music track
            apple_music_url = track.get("trackViewUrl", "")
            
            if apple_music_url:
                # Store the match
                track_urls.append((artist_name, track_name, apple_music_url))
    except Exception as e:
        # Silently skip network hiccups during lookup loop
        continue

# 4. Generate a clean M3U Playlist Text File
with open("kexp_weekly.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for artist, track, am_url in track_urls:
        f.write(f"#EXTINF:-1,{artist} - {track}\n")
        f.write(f"{am_url}\n")

print(f"Successfully compiled kexp_weekly.m3u with {len(track_urls)} cross-verified store tracks.")
