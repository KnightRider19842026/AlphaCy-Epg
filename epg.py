import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import xml.etree.ElementTree as ET
import os

URL = "https://www.alphacyprus.com.cy/program"
XML_FILE = "epg.xml"

def clean_title(title):
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)
    title = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", title, flags=re.IGNORECASE)
    title = re.sub(r"copyright.*", "", title, flags=re.IGNORECASE)
    title = re.sub(
        r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ).*?\d{1,2}:\d{2}",
        "", title, flags=re.IGNORECASE
    )
    return re.sub(r"\s+", " ", title).strip()

def fetch_next_day_programmes():
    resp = requests.get(URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    lines = soup.get_text("\n").split("\n")
    programmes = []

    time_pattern = re.compile(r"^\s*(\d{1,2}:\d{2})\s*$")
    current_time = None

    for line in lines:
        line = line.strip()
        if time_pattern.match(line):
            current_time = line
            continue
        if current_time and line:
            title = clean_title(line)
            if title:
                programmes.append((current_time, title))
            current_time = None

    tomorrow = datetime.now() + timedelta(days=1)
    return programmes, tomorrow

def merge_programmes(new_programmes, target_date):
    existing = []

    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()

        for prog in root.findall("programme"):
            existing.append(prog)

    base_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    new_entries = []

    for i, (time_str, title) in enumerate(new_programmes):
        h, m = map(int, time_str.split(":"))
        start_dt = base_date + timedelta(hours=h, minutes=m)

        if i < len(new_programmes) - 1:
            nh, nm = map(int, new_programmes[i + 1][0].split(":"))
            stop_dt = base_date + timedelta(hours=nh, minutes=nm)
        else:
            stop_dt = start_dt + timedelta(minutes=60)

        start = start_dt.strftime("%Y%m%d%H%M%S +0300")
        stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")

        new_entries.append((start, stop, title))

    now = datetime.now()
    cutoff = now - timedelta(days=2)  # 🔥 3ήμερο

    filtered_existing = []
    for prog in existing:
        start_str = prog.attrib["start"]
        start_dt = datetime.strptime(start_str[:14], "%Y%m%d%H%M%S")
        if start_dt >= cutoff:
            filtered_existing.append((
                prog.attrib["start"],
                prog.attrib["stop"],
                prog.find("title").text
            ))

    all_programmes = filtered_existing + new_entries

    unique = {}
    for start, stop, title in all_programmes:
        unique[start] = (start, stop, title)

    final_programmes = sorted(unique.values(), key=lambda x: x[0])

    root = ET.Element("tv")

    channel = ET.SubElement(root, "channel", id="alpha.cy")
    display = ET.SubElement(channel, "display-name")
    display.text = "Alpha Cyprus"

    for start, stop, title in final_programmes:
        prog = ET.SubElement(root, "programme", channel="alpha.cy", start=start, stop=stop)
        t = ET.SubElement(prog, "title")
        t.text = title

    tree = ET.ElementTree(root)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)

def main():
    new_programmes, target_date = fetch_next_day_programmes()
    merge_programmes(new_programmes, target_date)
    print("✅ 3ήμερο EPG update OK")

if __name__ == "__main__":
    main()
