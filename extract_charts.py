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
                artist, album = text_line.split(" - ", 1)
                top_90_list.append((artist.strip(), album.strip()))

if not top_90_list:
    print("Error: Could not find or parse any items from the Top 90 chart layout.")
    exit(1)

# 3. Construct a valid RSS XML structure
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "KEXP Isolated Top 90 Chart"
ET.SubElement(channel, "link").text = url
ET.SubElement(channel, "description").text = "Cleaned line-by-line feed for Apple Shortcuts integration"

for artist, album in top_90_list:
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = artist
    ET.SubElement(item, "description").text = album
    ET.SubElement(item, "guid", isPermaLink="false").text = f"{artist}-{album}"

# 4. Save to a file
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("kexp_top90.xml", encoding="utf-8", xml_declaration=True)
print(f"Successfully generated kexp_top90.xml with {len(top_90_list)} clean tracks.")
