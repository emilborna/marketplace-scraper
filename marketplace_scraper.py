from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

listings_URLs = []

def crawl_facebook_marketplace(city: str, query: str, max_price: int):
    listings_URLs = extract_links()
    marketplace_url = f'https://www.facebook.com/marketplace/category/search/?query={query}&maxPrice={max_price}'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(marketplace_url)
    
        #ändra denna
        time.sleep(1)

        try:
            press_button('Neka valfria cookies', page)
            logger.info("Closed the cookies pop-up.")
        except TimeoutError:
            logger.warning("No login pop-up found.")

        try:
            press_button('Stäng', page)
            logger.info("Closed the login pop-up.")
        except TimeoutError:
            logger.warning("No login pop-up found.")

        try:
            close_button = page.wait_for_selector('div[role="button"]:has-text("San Francisco")', timeout=5000)  # Timeout på 5 sekunder
            close_button.click()  # Klicka på stängknappen
            logger.info("Closed the login pop-up.")
        except TimeoutError:
            logger.warning("No login pop-up found.")

        page.fill('input[aria-label="Plats"]', city)

        page.wait_for_selector('ul[role="listbox"]', timeout=5000)

        page.click(f'li[role="option"]:has-text("Ort")') 

        page.evaluate('document.body.style.zoom = "80%"')

        press_button('Tillämpa', page)

        logger.info("Clicked on 'Tillämpa' button.")
        #ändra denna
        time.sleep(3)

        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        parsed = []

        listings = soup.find_all('div', class_='x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24')

        if not listings:
            logger.warning("No listings found with the given class!")
        else:
            logger.info(f"Found {len(listings)} listings")

        for listing in listings:
            try:
                title = extract_title(listing)
                price = extract_price(listing)
                post_url = extract_post_url(listing)
                location = extract_location(listing)
                image = extract_image(listing)

                # Kontrollera att de viktigaste uppgifterna finns
                if not title or not price or not post_url:
                    logger.warning(f"Skipping listing due to missing data: title={title}, price={price}, post_url={post_url}")
                    continue  # Hoppa över denna annons

                logger.info(f"Processing listing: {title}")

                parsed.append({
                    'image': image,
                    'title': title,
                    'price': price,
                    'post_url': post_url,
                    'location': location
                })
            except Exception as e:
                logger.error(f"Error processing listing: {e}")

        # Close the browser.
        try:
            browser.close()
        except Exception as e:
            logger.error(f"Error closing the browser: {e}")
        # Return the parsed data as a JSON.
        result = []
        for item in parsed:
            result.append({
                'name': item['title'],
                'price': item['price'],
                'location': item['location'],
                'title': item['title'],
                'image': item['image'],
                'link': item['post_url']
            })
            if item['post_url'] not in listings_URLs:
                print(item['post_url'])
                send_listing_to_discord(item['title'], item['price'], item['location'], item['post_url'], item['image'])
                add_URL_to_listings(item['post_url'])
                save_to_excel(result)
        return result
    
def send_listing_to_discord(TITLE, PRICE, LOCATION, URL, IMAGE):
    data = {
        "username": "Marketplace Bot",
        "embeds": [{
            "title": "Ny annons!",
            "description": "En ny annons har dykt upp på Marketplace.",
            "color": 16711680,  # Röd färg
            "fields": [
                {"name": "Titel", "value": TITLE, "inline": True},
                {"name": "Pris", "value": PRICE, "inline": True},
                {"name": "Plats", "value": LOCATION, "inline": False}
            ],
            "url": "https://www.facebook.com" + URL,  # Fullständig URL här
            "image": {"url": IMAGE}  # Visar en bild i inlägget
        }]
    }

    print(f"Skickar följande data till Discord: {data}")  # Lägg till denna logg för att inspektera datan

    response = requests.post(WEBHOOK_URL, json=data)

    if response.status_code == 204:
        print("✅ Meddelandet skickades!")
    else:
        print(f"❌ Fel vid skickande: {response.status_code} {response.text}")


def save_to_excel(data, filename="listings.xlsx"):
    try:
        # Försök läsa in befintlig fil
        df = pd.read_excel(filename, engine="openpyxl")
    except FileNotFoundError:
        # Om filen inte finns, skapa en ny DataFrame
        df = pd.DataFrame(columns=["name", "price", "location", "title", "image", "link"])

    # Skapa en DataFrame från den nya datan
    new_df = pd.DataFrame(data)

    # Slå ihop med befintlig data (om några annonser redan finns)
    df = pd.concat([df, new_df], ignore_index=True)

    # Spara till Excel
    df.to_excel(filename, index=False, engine="openpyxl")
    logger.info(f"Sparade {len(new_df)} annonser i '{filename}'")

def extract_links(filename="listings.xlsx"):
    try:
        df = pd.read_excel(filename, engine="openpyxl")  # Läser Excel-filen
        if "link" not in df.columns:
            print("❌ Kolumnen 'link' saknas i filen!")
            return []

        links = df["link"].dropna().tolist()  # Tar bort tomma värden och gör en lista
        return links

    except FileNotFoundError:
        print(f"❌ Filen '{filename}' hittades inte!")
        return []
    except Exception as e:
        print(f"❌ Fel vid läsning av Excel: {e}")
        return []

def clear_excel(filename="listings.xlsx"):
    # Skapa en tom DataFrame med samma kolumner
    df = pd.DataFrame(columns=["name", "price", "location", "title", "image", "link"])
    
    # Spara den tomma DataFrame till Excel-filen
    df.to_excel(filename, index=False, engine="openpyxl")
    logger.info(f"Rensade innehållet i '{filename}' och sparade en tom fil.")

def add_URL_to_listings(URL):
    listings_URLs.append(URL)

def press_button(button, page):
    close_button = page.wait_for_selector(f'div[aria-label="{button}"]', timeout=5000)  # Timeout på 5 sekunder
    close_button.click()

def extract_image(listing):
    image = listing.find('img', class_='x168nmei x13lgxp2 x5pf9jr xo71vjh xt7dq6l xl1xv1r x6ikm8r x10wlt62 xh8yej3')
    return image['src'] if image else None

def extract_title(listing):
    title = listing.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6')
    return title.text if title else None

def extract_price(listing):
    price = listing.find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x1lkfr7t x1lbecb7 x1s688f xzsf02u')
    return price.text if price else None

def extract_post_url(listing):
    post_url = listing.find('a', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g xkrqix3 x1sur9pj x1s688f x1lku1pv')
    return post_url['href'] if post_url else None

def extract_location(listing):
    location = listing.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft')
    return location.text if location else None