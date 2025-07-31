import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import time

# --- Google Sheets Setup ---


scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_file('gspread_key.json', scopes=scope)
client = gspread.authorize(credentials)

# Open your sheet by name and select first worksheet
SPREADSHEET_NAME = "Gift Preferences"  # change to your sheet name
sheet = client.open(SPREADSHEET_NAME).sheet1

# Read all gift ideas from a column (e.g., first column)
gift_ideas = sheet.col_values(9)  # adjust the column number if needed

print(f"Loaded {len(gift_ideas)} gift ideas from Google Sheets.\n")


# --- Google Search Scraping Setup ---


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def search_google(query):
    try:
        url = "https://www.google.com/search"
        params = {"q": query, "num": "3"}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Parse results here...
        print(f"Results for '{query}':")
        for g in soup.select('.tF2Cxc'):  # This is a common Google result container class
            title = g.select_one('h3')
            link = g.select_one('a')['href']
            if title and link:
                print(title.text)
                print(link)
        time.sleep(2)  # polite delay
    except Exception as e:
        print(f"Error searching for '{query}': {e}")

gifts = [
    "Customized Gaming Controller Skin",
    "Customized Phone Case",
]

for gift in gifts:
    print(f"Searching for: {gift}")
    search_google(gift)

def google_search(query, num_results=3):
    """Scrape Google Search results for a query, return list of (title, url)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36"
    }

    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"
    response = requests.get(search_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for g in soup.find_all('div', class_='tF2Cxc')[:num_results]:
        title = g.find('h3')
        link = g.find('a', href=True)
        if title and link:
            results.append((title.get_text(), link['href']))

    return results


# --- Main ---

for gift in gift_ideas:
    if not gift.strip():
        continue  # skip empty rows

    print(f"Searching for: {gift}")
    try:
        results = google_search(gift, num_results=3)
        if results:
            for i, (title, url) in enumerate(results, 1):
                print(f"  {i}. {title}\n     {url}")
        else:
            print("  No results found.")
    except Exception as e:
        print(f"  Error searching for '{gift}': {e}")

    print("\n---\n")
    time.sleep(2)  # be polite, avoid Google blocking

