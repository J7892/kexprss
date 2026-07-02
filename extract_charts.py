import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

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
top_90_list = []
top_90_header = soup.find(lambda tag: tag.name == "h4" and "Top 90:" in tag.text)

if top_90_header:
    ol_tag = top_90_header.find_next('ol')
    if ol_tag:
        for li in ol_tag.find_all('li'):
            text_line = li.get_text().strip()
            
            # Split by the standard short keyboard hyphen used in the HTML source code
            if " - " in text_line:
                artist, album_part = text_line.split(" - ", 1)
                artist = artist.strip()
                album_part = album_part.strip()
                
                # Clean off the record label parenthetical block if it exists (e.g., "(Loma Vista)")
                album_clean = album_part
                if " (" in album_part:
                    album_clean = album_part.split(" (")[0].strip()
                
                # Check if there is an explicit track highlighted in quotes inside the text
                track_title = None
                for quote_open, quote_close in [('“', '”'), ('"', '"')]:
                    if quote_open in album_clean and quote_close in album_clean:
                        start = album_clean.find(quote_open) + 1
                        end = album_clean.find(quote_close)
                        track_title = album_clean[start:end].strip()
                        break
                
                # Strategy: If a track single is inside quotes, use that specific song title.
                # If it's a clean album/EP name, use the album title.
                search_target = track_title if track_title else album_clean
                
                # Build the ultimate storefront search string
                search_string = f"{artist} {search_target}"
                
                top_90_list.append((artist, album_clean, search_string))

if not top_90_list:
    print("Error: Could not find or parse any items from the Top 90 chart layout.")
    exit(1)

# 3. Construct a valid RSS XML structure
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "KEXP Isolated Top 90 Chart"
ET.SubElement(channel, "link").text = url
ET.SubElement(channel, "description").text = "Cleaned line-by-line feed for Apple Shortcuts integration"

for artist, album, search_string in top_90_list:
    item = ET.SubElement(channel, "item")
    # Store the exact concatenated search payload directly into the title tag
    ET.SubElement(item, "title").text = search_string
    ET.SubElement(item, "description").text = f"Artist: {artist} | Release: {album}"
    ET.SubElement(item, "guid", isPermaLink="false").text = f"{artist}-{album}"

# 4. Save to a file
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("kexp_top90.xml", encoding="utf-8", xml_declaration=True)
print(f"Successfully generated kexp_top90.xml with {len(top_90_list)} clean tracks.")
