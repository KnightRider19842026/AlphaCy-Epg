import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_alpha_epg(days=4):
    # Ξεκινάμε από σήμερα (timezone Κύπρου +0300)
    tz = datetime.timezone(datetime.timedelta(hours=3))
    start_date = datetime.datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

    tv = ET.Element("tv")
    
    channel = ET.SubElement(tv, "channel")
    channel.set("id", "alpha.cy")
    ET.SubElement(channel, "display-name").text = "Alpha Cyprus"

    # Πραγματικό καθημερινό πρόγραμμα (Δευτέρα - Πέμπτη/Παρασκευή)
    daily_schedule = [
        ("060000", "064500", "DEAL (E)"),
        ("064500", "092000", "ALPHA ΚΑΛΗΜΕΡΑ"),
        ("092000", "110000", "BUONGIORNO"),
        ("110000", "135000", "ALPHA ΕΝΗΜΕΡΩΣΗ"),
        ("135000", "151500", "ΤΟ ΣΟΪ ΣΟΥ (E)"),
        ("151500", "170000", "ΜΕ ΑΓΑΠΗ ΧΡΙΣΤΙΑΝΑ"),
        ("170000", "180000", "THE CHASE GREECE"),
        ("180000", "190000", "ΝΑ Μ' ΑΓΑΠΑΣ"),
        ("190000", "200000", "DEAL"),
        ("200000", "210000", "ALPHA NEWS"),
        ("210000", "222000", "ΑΓΙΟΣ ΕΡΩΤΑΣ"),
        ("222000", "230000", "Η ΓΗ ΤΗΣ ΕΛΙΑΣ"),
        ("230000", "010000", "ΝΑ Μ' ΑΓΑΠΑΣ (Ε)"),   # μέχρι 01:00 επόμενης μέρας
    ]

    for d in range(days):
        current_date = start_date + datetime.timedelta(days=d)
        date_str = current_date.strftime("%Y%m%d")

        for start_time, stop_time, title in daily_schedule:
            start = f"{date_str}{start_time} +0300"

            if stop_time == "010000":
                # Πάει στην επόμενη μέρα
                stop_date = current_date + datetime.timedelta(days=1)
                stop = f"{stop_date.strftime('%Y%m%d')}010000 +0300" if stop_time == "010000" else f"{date_str}{stop_time} +0300"
            else:
                stop = f"{date_str}{stop_time} +0300"

            programme = ET.SubElement(tv, "programme")
            programme.set("channel", "alpha.cy")
            programme.set("start", start)
            programme.set("stop", stop)
            ET.SubElement(programme, "title").text = title

    # Pretty XML
    rough_string = ET.tostring(tv, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Καθαρισμός
    lines = pretty_xml.split('\n')
    clean_xml = '\n'.join(line for line in lines if line.strip())

    with open("alpha_epg.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(clean_xml)

    print(f"✅ Δημιουργήθηκε alpha_epg.xml με {days} μέρες (από {start_date.strftime('%d/%m/%Y')})")

if __name__ == "__main__":
    generate_alpha_epg(days=4)
