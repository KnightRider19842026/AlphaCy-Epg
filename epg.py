import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

URL = "https://www.alphacyprus.com.cy/program"

def clean_text(text):
    if not text:
        return ""
    # Αφαίρεση συγκεκριμένων λέξεων/φράσεων
    text = re.sub(r"microsite", "", text, flags=re.IGNORECASE)
    text = re.sub(r"live now", "", text, flags=re.IGNORECASE)
    text = re.sub(r"καθημερινά στις", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", text, flags=re.IGNORECASE)
    text = re.sub(r"copyright.*", "", text, flags=re.IGNORECASE)
    # Αφαίρεση παρενθέσεων και πολλαπλών κενών
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().strip('- ')

def fetch_programmes():
    try:
        resp = requests.get(URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

    programmes = []
    time_pattern = re.compile(r"(\d{1,2}:\d{2})")
    
    # Παίρνουμε τα blocks των εκπομπών (συνήθως σε containers με συγκεκριμένη κλάση)
    # Αν το site αλλάξει δομή, το BeautifulSoup θα διαβάσει το κείμενο με σειρά.
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    current_time = None
    for line in lines:
        match = time_pattern.search(line)
        if match:
            # Αν η γραμμή είναι μόνο ώρα (π.χ. "19:00")
            if len(line) <= 5:
                current_time = match.group(1)
                continue
        
        if current_time:
            full_title = clean_text(line)
            if full_title and len(full_title) > 2 and "Designed" not in full_title:
                programmes.append((current_time, full_title))
                current_time = None

    # Αφαίρεση διπλότυπων
    final_prog = []
    seen = set()
    for t, title in programmes:
        entry = (t, title)
        if entry not in seen:
            final_prog.append(entry)
            seen.add(entry)
            
    return final_prog

def build_xml(programmes, target_days):
    xml = '<?xml version="1.0" encoding="utf-8"?>\n<tv>\n'
    xml += '<channel id="alpha.cy">\n  <display-name>Alpha Cyprus</display-name>\n</channel>\n'

    for base_date in target_days:
        is_thursday = base_date.strftime('%A') == 'Thursday'
        
        for i, (time_str, title) in enumerate(programmes):
            try:
                h, m = map(int, time_str.split(":"))
                start_dt = base_date.replace(hour=h, minute=m, second=0, microsecond=0)

                # Υπολογισμός λήξης (stop time)
                if i < len(programmes) - 1:
                    nh, nm = map(int, programmes[i + 1][0].split(":"))
                    stop_dt = base_date.replace(hour=nh, minute=nm, second=0, microsecond=0)
                    if nh < h or (nh == h and nm < m):
                        stop_dt += timedelta(days=1)
                else:
                    stop_dt = start_dt + timedelta(hours=1)

                # Διόρθωση για τις πρώτες πρωινές ώρες (μετά τα μεσάνυχτα)
                if h < 5:
                    start_dt += timedelta(days=1)
                    stop_dt += timedelta(days=1)

                # Ειδικός κανόνας για το DEAL Πέμπτης
                if is_thursday and h == 19 and m == 0:
                    title_text = "DEAL"
                    desc_text = "Με τον Γιώργο Θαναηλάκη"
                else:
                    # Χωρίζουμε τον τίτλο και την περιγραφή αν υπάρχει παύλα ή τελεία
                    # Αν δεν υπάρχει, βάζουμε όλο το κείμενο στον τίτλο
                    title_text = title
                    desc_text = f"Πρόγραμμα του Alpha Cyprus: {title}"

                start_str = start_dt.strftime("%Y%m%d%H%M%S +0300")
                stop_str  = stop_dt.strftime("%Y%m%d%H%M%S +0300")

                xml += f'<programme channel="alpha.cy" start="{start_str}" stop="{stop_str}">\n'
                xml += f"  <title>{title_text}</title>\n"
                xml += f"  <desc>{desc_text}</desc>\n"
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

    # Παίρνουμε το πρόγραμμα από το site
    programmes = fetch_programmes()
    
    if programmes:
        # Δημιουργούμε το αρχείο για Σήμερα και Αύριο
        build_xml(programmes, [today, tomorrow])
        print(f"✅ epg.xml ενημερώθηκε επιτυχώς για {today.strftime('%d/%m')} και {tomorrow.strftime('%d/%m')}.")
    else:
        print("⚠️ Δεν βρέθηκαν δεδομένα.")

if __name__ == "__main__":
    main()
