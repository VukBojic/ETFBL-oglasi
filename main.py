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

# Definišite apsolutnu putanju do sent_ads.txt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Direktorijum gde se nalazi skripta
SENT_ADS_PATH = os.path.join(BASE_DIR, "sent_ads.txt")  # Apsolutna putanja do sent_ads.txt

# Konfiguracija
URL = "https://efee.etf.unibl.org/oglasi/"
PREDMETI = [
    "Formalne metode u softverskom inženjerstvu",
    "Математика 4",
    "Основи комуникација и теорија информација",
    "Програмски језици 2",
    "Основи електротехнике 1",
    "Основи електротехнике 2",
    "Strukture podataka i algoritmi"
]
EMAIL = "vuk.bojic2025@gmail.com"

# Funkcija za slanje emaila
def posalji_email(subject, body, to_email):
    from_email = "vuk.bojic2025@gmail.com"  # vaš email
    from_password = "onyk sxem ivsu hfym"   # lozinka (app password)

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("✅ Email uspešno poslat!")
    except Exception as e:
        print(f"❌ Greška pri slanju emaila: {e}")

# Formatira oglas u HTML
def formatiraj_oglas(oglas_text):
    lines = oglas_text.split('\n')
    if len(lines) < 2:
        return oglas_text
    predmet = lines[0].strip()
    datum_vrijeme = lines[1].strip()
    sadrzaj = "<br>".join(lines[2:]).strip()
    return (
        f"<b>{predmet}</b><br>"
        f"Datum i vrijeme: {datum_vrijeme}<br>"
        f"{sadrzaj}<br><hr>"
    )

# Blaža normalizacija (da ne izgubi razlike)
def normalizuj_oglas(oglas_text):
    oglas_text = oglas_text.replace('\r', '').strip()
    oglas_text = re.sub(r'[ \t]+', ' ', oglas_text)  # uklanja duple razmake, ali ne nove redove
    return oglas_text

# Učitava oglase sa sajta
def get_oglasi():
    print("🌐 Učitavam oglase sa stranice...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(URL)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-content"))
        )
        print("✅ Stranica učitana i sadrži 'ui-content'")
    except Exception as e:
        print(f"⚠️ Stranica nije učitana na vreme: {e}")
        driver.quit()
        return {}

    oglasi_po_godinama = {
        "prva_godina": [],
        "druga_godina": [],
        "treca_godina": [],
        "cetvrta_godina": []
    }

    godine = [
        ("Прва година", "prva_godina"),
        ("Друга година", "druga_godina"),
        ("Трећа година", "treca_godina"),
        ("Четврта година", "cetvrta_godina"),
    ]

    for naziv, key in godine:
        try:
            # Klik na dugme godine
            dugme = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{naziv}')]"))
            )
            driver.execute_script("arguments[0].click();", dugme)

            # Sačekaj da se pojavi sadržaj
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-collapsible-content"))
            )

            soup = BeautifulSoup(driver.page_source, "html.parser")
            content = soup.find("div", class_="ui-content")
            collapsibles = content.find_all("div", class_="ui-collapsible-content")

            for coll in collapsibles:
                oglasi = coll.find_all("li", class_="ui-li")
                for oglas in oglasi:
                    naslov = oglas.find("span", class_="ui-li-heading")
                    opis = oglas.find("p", class_="ui-li-desc")

                    if not naslov or not opis:
                        continue

                    oglas_text = f"{naslov.get_text(strip=True)}\n{opis.get_text(strip=True)}"

                    # Provjera da li oglas pripada relevantnim predmetima
                    for predmet in PREDMETI:
                        if predmet in oglas_text:
                            oglasi_po_godinama[key].append(oglas_text)
                            break

            print(f"📚 {naziv}: pronađeno {len(oglasi_po_godinama[key])} oglasa.")

        except Exception as e:
            print(f"⚠️ Greška pri čitanju oglasa za {naziv}: {e}")

    driver.quit()
    return oglasi_po_godinama

# Učitava poslate oglase
def ucitaj_poslate_oglasa():
    if not os.path.exists(SENT_ADS_PATH):
        return set()
    with open(SENT_ADS_PATH, "r", encoding="utf-8") as f:
        return {normalizuj_oglas(oglas) for oglas in f.read().splitlines()}

# Čuva poslate oglase
def sacuvaj_poslate_oglasa(poslednji_oglasi):
    with open(SENT_ADS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(poslednji_oglasi))

# ---------------- MAIN FUNKCIJA ----------------
def main():
    print("🔧 Pokrećem skriptu za oglase...")
    print("📁 SENT_ADS_PATH =", SENT_ADS_PATH)

    # Provera fajla
    if os.path.exists(SENT_ADS_PATH):
        print(f"📄 Fajl postoji. Veličina: {os.path.getsize(SENT_ADS_PATH)} B")
    else:
        print("⚠️ Fajl ne postoji! Kreiram novi...")
        with open(SENT_ADS_PATH, "w", encoding="utf-8") as f:
            f.write("")

    # Učitavanje starih oglasa
    poslednji_oglasi = ucitaj_poslate_oglasa()
    print("📊 Broj učitanih starih oglasa:", len(poslednji_oglasi))

    # Učitavanje trenutnih oglasa
    oglasi_po_godinama = get_oglasi()
    ukupno_trenutnih = sum(len(v) for v in oglasi_po_godinama.values())
    print("🔎 Broj trenutno pronađenih oglasa na sajtu:", ukupno_trenutnih)

    # Normalizacija
    trenutni_oglasi_normalizovani = set()
    for godina, oglasi in oglasi_po_godinama.items():
        for oglas in oglasi:
            trenutni_oglasi_normalizovani.add(normalizuj_oglas(oglas))

    # Pronalaženje novih
    novi_oglasi_normalizovani = trenutni_oglasi_normalizovani - poslednji_oglasi
    print("🆕 Novi oglasi detektovani:", len(novi_oglasi_normalizovani))

    if novi_oglasi_normalizovani:
        print("✅ Pronađeno novih oglasa! Šaljem email...")
        body = "<html><body>"
        for godina, oglasi in oglasi_po_godinama.items():
            if oglasi:
                body += f"<h2>Obaveštenja za {godina.replace('_', ' ').capitalize()}:</h2><br>"
                for oglas in oglasi:
                    if normalizuj_oglas(oglas) in novi_oglasi_normalizovani:
                        body += formatiraj_oglas(oglas)
        body += "</body></html>"

        posalji_email("Novi oglasi za vaše predmete", body, EMAIL)

        # Sačuvaj nove oglase
        poslednji_oglasi.update(novi_oglasi_normalizovani)
        sacuvaj_poslate_oglasa(poslednji_oglasi)
        print("💾 Novi oglasi sačuvani u sent_ads.txt.")
    else:
        print("ℹ️ Nema novih oglasa.")

# Pokretanje
if __name__ == "__main__":
    main()


