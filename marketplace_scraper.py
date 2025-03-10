from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def press_button(button, page):
    close_button = page.wait_for_selector(f'div[aria-label="{button}"]', timeout=5000)  # Timeout på 5 sekunder
    close_button.click()
                 

def crawl_facebook_marketplace(city: str, query: str, max_price: int):
    marketplace_url = f'https://www.facebook.com/marketplace/category/search/?query={query}&maxPrice={max_price}'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(marketplace_url)
    
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
                # Get the item image
                image = listing.find('img', class_='x168nmei x13lgxp2 x5pf9jr xo71vjh xt7dq6l xl1xv1r x6ikm8r x10wlt62 xh8yej3')
                image_src = image['src'] if image else None
                
                # Get the item title
                title = listing.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6')
                title_text = title.text if title else 'No Title'
                
                # Get the item price
                price = listing.find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x1lkfr7t x1lbecb7 x1s688f xzsf02u')
                price_text = price.text if price else 'No Price'
                
                
                # Get the item URL
                post_url = listing.find('a', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g xkrqix3 x1sur9pj x1s688f x1lku1pv')
                post_url_href = post_url['href'] if post_url else 'No URL'
                
                # Get the item location
                location = listing.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft')
                location_text = location.text if location else 'No Location'
                
                
                parsed.append({
                    'image': image_src,
                    'title': title_text,
                    'price': price_text,
                    'post_url': post_url_href,
                    'location': location_text
                })
            except Exception as e:
                logger.warning(f"Error processing listing: {e}")

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
        return result
