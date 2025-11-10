from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re
import time

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENT_ADS_PATH = os.path.join(BASE_DIR, "sent_ads.txt")
URL = "https://efee.etf.unibl.org/oglasi/"
EMAIL = "vuk.bojic2025@gmail.com"

def posalji_email(subject, body, to_email):
    from_email = "vuk.bojic2025@gmail.com"
    from_password = "onyk sxem ivsu hfym"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email uspešno poslat!")
    except Exception as e:
        print(f"Greška pri slanju emaila: {e}")

def formatiraj_oglas(oglas_text):
    lines = oglas_text.split('\n')
    if len(lines) < 2:
        return f"<b>{oglas_text}</b><br><hr>"

    # Prva linija je obično naziv predmeta ili naslov
    naslov = lines[0].strip()
    # Druga linija je obično datum i vrijeme
    datum_vrijeme = lines[1].strip()
    # Ostale linije su sadržaj oglasa
    sadrzaj = "<br>".join(lines[2:]).strip()

    # Formatiranje u HTML
    formatiran_oglas = (
        f"<b>{naslov}</b><br>"
        f"Datum i vrijeme: {datum_vrijeme}<br>"
        f"{sadrzaj}<br>"
        "<hr>"
    )
    return formatiran_oglas

def normalizuj_oglas(oglas_text):
    oglas_text = re.sub(r'\s+', ' ', oglas_text)
    oglas_text = oglas_text.strip()
    return oglas_text

def get_oglasi():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        print("🔄 Pokrećem Chrome driver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        print("🔄 Učitavam stranicu...")
        driver.get(URL)
        time.sleep(5)

        print(f"✅ Stranica učítana: {driver.title}")
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        oglasi_po_godinama = {
            "prva_godina": [],
            "druga_godina": [],
            "treca_godina": [],
            "cetvrta_godina": []
        }

        # Look for announcements by year
        ul_ids = ["ul_id_1", "ul_id_2", "ul_id_3", "ul_id_4"]
        godine = ["prva_godina", "druga_godina", "treca_godina", "cetvrta_godina"]
        
        for ul_id, godina in zip(ul_ids, godine):
            ul_tag = soup.find("ul", id=ul_id)
            if ul_tag:
                print(f"✅ Pronađen {ul_id} za {godina}")
                li_elements = ul_tag.find_all("li")
                print(f"   📝 Pronađeno {len(li_elements)} oglasa")
                
                for li in li_elements:
                    oglas_text = li.get_text(separator="\n").strip()
                    if oglas_text and len(oglas_text) > 10:  # samo oglasi sa dovoljno teksta
                        # DODAJEMO SVE OGLASE BEZ FILTRIRANJA PO PREDMETIMA
                        oglasi_po_godinama[godina].append(oglas_text)
                        print(f"   ✅ Dodat oglas: {oglas_text[:80]}...")
            else:
                print(f"❌ Nije pronađen {ul_id}")

        print(f"\n📊 REZULTAT PRETRAGE:")
        ukupno_oglasa = 0
        for godina, oglasi in oglasi_po_godinama.items():
            print(f"   {godina}: {len(oglasi)} oglasa")
            ukupno_oglasa += len(oglasi)
        print(f"   UKUPNO: {ukupno_oglasa} oglasa")

        driver.quit()
        return oglasi_po_godinama

    except Exception as e:
        print(f"🚨 Greška u get_oglasi(): {e}")
        if 'driver' in locals():
            driver.quit()
        return {
            "prva_godina": [],
            "druga_godina": [],
            "treca_godina": [],
            "cetvrta_godina": []
        }

def ucitaj_poslate_oglasa():
    if not os.path.exists(SENT_ADS_PATH):
        return set()
    with open(SENT_ADS_PATH, "r", encoding="utf-8") as f:
        return {normalizuj_oglas(oglas) for oglas in f.read().splitlines()}

def sacuvaj_poslate_oglasa(poslednji_oglasi):
    with open(SENT_ADS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(poslednji_oglasi))

def main():
    if not os.path.exists(SENT_ADS_PATH):
        with open(SENT_ADS_PATH, "w", encoding="utf-8") as f:
            f.write("")

    print("🚀 Pokrećem skriptu...")
    
    poslednji_oglasi = ucitaj_poslate_oglasa()
    print(f"📚 Učitano {len(poslednji_oglasi)} prethodnih oglasa")
    
    oglasi_po_godinama = get_oglasi()
    
    ukupno_oglasa = sum(len(oglasi) for oglasi in oglasi_po_godinama.values())
    print(f"📊 Pronađeno ukupno {ukupno_oglasa} oglasa")
    
    # FOKUSIRAMO SE SAMO NA PRVU I DRUGU GODINU
    godine_za_slanje = ["prva_godina", "druga_godina"]
    
    # Prikupi sve oglase iz prve i druge godine i normalizuj ih
    trenutni_oglasi_normalizovani = set()
    for godina in godine_za_slanje:
        for oglas in oglasi_po_godinama[godina]:
            trenutni_oglasi_normalizovani.add(normalizuj_oglas(oglas))
    
    # Pronađi nove oglase
    novi_oglasi_normalizovani = trenutni_oglasi_normalizovani - poslednji_oglasi
    
    # ISPRAVAN ISPIS - brojimo samo nove oglase
    print(f"📨 Novi oglasi za slanje (prva i druga godina): {len(novi_oglasi_normalizovani)}")
    
    if novi_oglasi_normalizovani:
        print(f"🎉 Pronađeno {len(novi_oglasi_normalizovani)} novih oglasa iz prve i druge godine!")
        
        # Kreiramo email body samo sa novim oglasima iz prve i druge godine
        body = "<html><body>"
        body += "<h1>📢 Novi oglasi sa ETF-a</h1>"
        
        # Brojimo koliko godina ima novih oglasa
        godine_sa_oglasima = []
        ukupno_poslatih_oglasa = 0
        
        for godina in godine_za_slanje:
            oglasi = oglasi_po_godinama[godina]
            novi_oglasi_za_godinu = [oglas for oglas in oglasi if normalizuj_oglas(oglas) in novi_oglasi_normalizovani]
            
            if novi_oglasi_za_godinu:
                godine_sa_oglasima.append((godina, novi_oglasi_za_godinu))
                ukupno_poslatih_oglasa += len(novi_oglasi_za_godinu)
        
        # Ako postoje oglasi, dodajemo podnaslove samo za godine koje imaju oglase
        if godine_sa_oglasima:
            for godina, novi_oglasi in godine_sa_oglasima:
                lep_naziv_godine = godina.replace('_', ' ').capitalize()
                body += f"<h2>📚 {lep_naziv_godine}:</h2>"
                for oglas in novi_oglasi:
                    body += formatiraj_oglas(oglas)
        
        body += "<br><p><i>🔔 Ovo je automatska obaveštenja. Svi novi oglasi su poslati.</i></p>"
        body += "</body></html>"

        # Pošalji email
        posalji_email("Novi oglasi - Prva i druga godina ETF", body, EMAIL)

        # Ažuriraj poslate oglase
        poslednji_oglasi.update(novi_oglasi_normalizovani)
        sacuvaj_poslate_oglasa(poslednji_oglasi)
        print(f"💾 Ažurirana lista poslatih oglasa. Poslato {ukupno_poslatih_oglasa} oglasa.")
        
    else:
        print("ℹ️ Nema novih oglasa u prvoj i drugoj godini.")

if __name__ == "__main__":
    main()
