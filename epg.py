import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

URL = "https://www.alphacyprus.com.cy/program"

def clean_and_split(text):
    if not text:
        return "", ""
    
    # 1. Βασικός καθαρισμός από ανεπιθύμητες λέξεις
    text = re.sub(r"microsite", "", text, flags=re.IGNORECASE)
    text = re.sub(r"live now", "", text, flags=re.IGNORECASE)
    text = re.sub(r"καθημερινά στις", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", text, flags=re.IGNORECASE)
    
    # 2. Λίστα με παρουσιαστές για να τους ξεχωρίζουμε στην περιγραφή
    hosts = [
        "ΚΑΤΕΡΙΝΑ ΑΓΑΠΗΤΟΥ", "ΚΑΤΙΑ ΣΑΒΒΑ", "ΓΙΩΡΓΟΣ ΘΑΝΑΗΛΑΚΗΣ", 
        "ΛΟΥΗΣ ΠΑΤΣΑΛΙΔΗΣ", "ΧΡΙΣΤΙΑΝΑ ΑΡΙΣΤΟΤΕΛΟΥΣ"
    ]
    
    title = text
    desc = "Πρόγραμμα του Alpha Cyprus"
    
    # Έλεγχος αν κάποιος παρουσιαστής είναι μέσα στο κείμενο
    for host in hosts:
        if host in text.upper():
            # Χωρίζουμε το όνομα της εκπομπής από τον παρουσιαστή
            # Π.Χ. "ALPHA ΚΑΛΗΜΕΡΑ ΜΕ ΤΗΝ ΚΑΤΕΡΙΝΑ ΑΓΑΠΗΤΟΥ"
            parts = re.split(f"με την|με τον|με", text, flags=re.IGNORECASE)
            if len(parts) > 1:
                title = parts[0].strip()
                desc = f"Με την {host}" if "ΚΑΤΕΡΙΝΑ" in host or "ΚΑΤΙΑ" in host or "ΧΡΙΣΤΙΑΝΑ" in host else f"Με τον {host}"
            break

    # Τελικό συμμάζεμα
    title = re.sub(r"\s+", " ", title).strip().strip('- ')
    return title, desc

def fetch_programmes():
    try:
        resp = requests.get(URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except:
        return []

    programmes = []
    time_pattern = re.compile(r"(\d{1,2}:\d{2})")
    lines = [line.strip() for line in soup.get_text(separator="\n").split("\n") if line.strip()]

    current_time = None
    for line in lines:
        match = time_pattern.search(line)
        if match and len(line) <= 5:
            current_time = match.group(1)
            continue
        
        if current_time:
            title, desc = clean_and_split(line)
            if title and len(title) > 2 and "Designed" not in title:
                programmes.append((current_time, title, desc))
                current_time = None
    return programmes

def build_xml(programmes, target_days):
    xml = '<?xml version="1.0" encoding="utf-8"?>\n<tv>\n'
    xml += '<channel id="alpha.cy">\n  <display-name>Alpha Cyprus</display-name>\n</channel>\n'

    for base_date in target_days:
        is_thursday = base_date.strftime('%A') == 'Thursday'
        
        for i, (time_str, title, desc) in enumerate(programmes):
            try:
                h, m = map(int, time_str.split(":"))
                start_dt = base_date.replace(hour=h, minute=m, second=0, microsecond=0)

                # Stop Time
                if i < len(programmes) - 1:
                    nh, nm = map(int, programmes[i + 1][0].split(":"))
                    stop_dt = base_date.replace(hour=nh, minute=nm, second=0, microsecond=0)
                    if nh < h or (nh == h and nm < m): stop_dt += timedelta(days=1)
                else:
                    stop_dt = start_dt + timedelta(hours=1)

                if h < 5:
                    start_dt += timedelta(days=1)
                    stop_dt += timedelta(days=1)

                # Ειδική περίπτωση Deal Πέμπτης
                if is_thursday and h == 19 and m == 0:
                    title_final, desc_final = "DEAL", "Με τον Γιώργο Θαναηλάκη"
                else:
                    title_final, desc_final = title, desc

                start_str = start_dt.strftime("%Y%m%d%H%M%S +0300")
                stop_str  = stop_dt.strftime("%Y%m%d%H%M%S +0300")

                xml += f'<programme channel="alpha.cy" start="{start_str}" stop="{stop_str}">\n'
                xml += f"  <title>{title_final}</title>\n"
                xml += f"  <desc>{desc_final}</desc>\n"
                xml += "</programme>\n"
            except:
                continue

    xml += "</tv>"
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)

def main():
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    progs = fetch_programmes()
    if progs:
        build_xml(progs, [today, tomorrow])
        print("✅ Το EPG ενημερώθηκε με διαχωρισμό τίτλου/περιγραφής!")

if __name__ == "__main__":
    main()
