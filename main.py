import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

SENT_ADS_PATH = "sent_ads.txt"
BASE_URL = "https://etf.unibl.org/oglasi/"

def ucitaj_stare_oglase():
    if not os.path.exists(SENT_ADS_PATH):
        print("📄 Fajl sent_ads.txt ne postoji, kreiram novi...")
        return set()
    with open(SENT_ADS_PATH, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def sacuvaj_nove_oglase(oglasi, stari_oglasi):
    novi_oglasi = [o for o in oglasi if o not in stari_oglasi]
    if not novi_oglasi:
        print("ℹ️ Nema novih oglasa.")
        return
    print(f"🆕 Novi oglasi ({len(novi_oglasi)}):")
    for oglas in novi_oglasi:
        print(" -", oglas)
    with open(SENT_ADS_PATH, "a", encoding="utf-8") as f:
        for oglas in novi_oglasi:
            f.write(oglas + "\n")

def pokreni_selenium():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.get(BASE_URL)
    time.sleep(5)  # sačekaj da se JS izvrši
    page_source = driver.page_source
    driver.quit()
    return page_source

def pronadji_oglase(html):
    soup = BeautifulSoup(html, "html.parser")
    oglasi = []
    coll_list = soup.find_all("div", {"data-role": "collapsible"})
    print(f"✅ Pronađeno {len(coll_list)} sekcija (godina/ciklusa)")
    for section in coll_list:
        naslov = section.find("h3").get_text(strip=True)
        ul = section.find("ul", class_="ui-listview")
        if not ul:
            continue
        li_list = ul.find_all("li")
        print(f"📚 {naslov}: {len(li_list)} oglasa")
        for li in li_list:
            heading = li.find(class_="ui-li-heading")
            desc = li.find(class_="ui-li-desc")
            naslov_oglasa = heading.get_text(strip=True) if heading else ""
            tekst_oglasa = desc.get_text(strip=True) if desc else ""
            if naslov_oglasa or tekst_oglasa:
                oglasi.append(f"{naslov}: {naslov_oglasa} - {tekst_oglasa}")
    return oglasi

def main():
    print("🔧 Pokrećem skriptu za oglase...")
    print(f"📁 SENT_ADS_PATH = {os.path.abspath(SENT_ADS_PATH)}")

    stari_oglasi = ucitaj_stare_oglase()
    print(f"📊 Broj učitanih starih oglasa: {len(stari_oglasi)}")

    print("🌐 Učitavam oglase sa stranice...")
    html = pokreni_selenium()
    oglasi = pronadji_oglase(html)

    print(f"🔎 Broj trenutno pronađenih oglasa na sajtu: {len(oglasi)}")
    sacuvaj_nove_oglase(oglasi, stari_oglasi)

if __name__ == "__main__":
    main()
