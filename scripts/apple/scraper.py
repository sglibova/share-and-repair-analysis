import logging
import random
import requests
import re
import time
from tqdm import tqdm
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

def get_token(country:str , app_name:str , app_id: str, user_agents: list):

    """
    Retrieves the bearer token required for API requests.
    Tries the classic Ember.js meta tag approach first, then falls back to
    extracting the token from the Vite JS bundle (used in the SvelteKit App Store).
    Regex adapted from base.py of https://github.com/cowboy-bebug/app-store-scraper
    """

    headers = {'User-Agent': random.choice(user_agents)}
    response = requests.get(f'https://apps.apple.com/{country}/app/{app_name}/id{app_id}',
                            headers=headers)

    if response.status_code != 200:
        logger.info(f"Response failed : {response}")
        print(f"GET request failed. Response: {response.status_code} {response.reason}")
        return None

    # Classic approach: Ember.js meta tag with URL-encoded token
    token = None
    tags = response.text.splitlines()
    logger.info(f"{tags}")
    for tag in tags:
        if re.match(r"<meta.+web-experience-app/config/environment", tag):
            match = re.search(r"token%22%3A%22(.+?)%22", tag)
            if match:
                token = match.group(1)
                break

    if token:
        logger.info(f"Got Token via meta tag.")
        return token

    # Fallback: SvelteKit/Vite JS bundle — find the main script and search it for the bearer token
    script_match = re.search(r'<script[^>]+src="(/assets/index[^"]+\.js)"', response.text)
    if not script_match:
        print("Could not find JS bundle script tag in App Store page.")
        return None

    js_url = f"https://apps.apple.com{script_match.group(1)}"
    logger.info(f"Fetching JS bundle: {js_url}")
    js_response = requests.get(js_url, headers=headers)

    if js_response.status_code != 200:
        print(f"Failed to fetch JS bundle: {js_response.status_code} {js_response.reason}")
        return None

    # Pattern 1: token embedded as string literal next to "bearer"
    token_match = re.search(r'["\']bearer (eyJ[A-Za-z0-9._-]+)["\']', js_response.text, re.IGNORECASE)
    if not token_match:
        # Pattern 2: bare JWT anywhere in the bundle
        token_match = re.search(r'eyJ[A-Za-z0-9._-]{50,}', js_response.text)
    if not token_match:
        print("Could not find bearer token in JS bundle.")
        return None

    token = token_match.group(1) if token_match.lastindex else token_match.group(0)
    logger.info(f"Got Token via JS bundle.")
    return token
    
def fetch_ratings(country: str, app_id: str, user_agents: list, token: str):

    """
    Fetches aggregate rating distribution (counts per star level) for an app.
    Returns the userRating dict with keys:
      - value: average rating
      - ratingCount: total number of ratings
      - ratingCountList: list of counts [1-star, 2-star, 3-star, 4-star, 5-star]
    """

    url = f'https://amp-api-edge.apps.apple.com/v1/catalog/{country}/apps/{app_id}'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'bearer {token}',
        'Origin': 'https://apps.apple.com',
        'Referer': f'https://apps.apple.com/{country}/app/id{app_id}',
        'User-Agent': random.choice(user_agents),
    }
    params = {'platform': 'web', 'fields': 'userRating'}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"GET request failed. Response: {response.status_code} {response.reason}")
        return None
    print(f"Retrieving user ratings for App ID {app_id}")
    return response.json()['data'][0]['attributes']['userRating']


def fetch_reviews(country:str , app_name:str , app_id: str, user_agents: dict, token: str, offset: str = '1'):

    """
    Fetches reviews for a given app from the Apple App Store API.

    - Default sleep after each call to reduce risk of rate limiting
    - Retry with increasing backoff if rate-limited (429)
    - No known ability to sort by date, but the higher the offset, the older the reviews tend to be
    """

    ## Define request headers and params ------------------------------------
    landingUrl = f'https://apps.apple.com/{country}/app/{app_name}/id{app_id}'
    requestUrl = f'https://amp-api-edge.apps.apple.com/v1/catalog/{country}/apps/{app_id}/reviews'

    headers = {
        'Accept': 'application/json',
        'Authorization': f'bearer {token}',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://apps.apple.com',
        'Referer': landingUrl,
        'User-Agent': random.choice(user_agents)
        }

    params = (
        ('l', 'en-GB'),                 # language
        ('offset', str(offset)),        # paginate this offset
        ('limit', '20'),                # max valid is 20
        ('platform', 'web'),
        ('additionalPlatforms', 'appletv,ipad,iphone,mac')
        )

    ## Perform request & exception handling ----------------------------------
    retry_count = 0
    MAX_RETRIES = 5
    BASE_DELAY_SECS = 10
    # Assign dummy variables in case of GET failure
    result = {'data': [], 'next': None}
    reviews = []

    while retry_count < MAX_RETRIES:

        # Perform request
        response = requests.get(requestUrl, headers=headers, params=params)

        # SUCCESS
        # Parse response as JSON and exit loop if request was successful
        if response.status_code == 200:
            result = response.json()
            reviews = result['data']
            if len(reviews) < 20:
                print(f"{len(reviews)} reviews scraped. This is fewer than the expected 20.")
            break

        # FAILURE
        elif response.status_code != 200:
            print(f"GET request failed. Response: {response.status_code} {response.reason}")

            # RATE LIMITED
            if response.status_code == 429:
                # Perform backoff using retry_count as the backoff factor
                retry_count += 1
                backoff_time = BASE_DELAY_SECS * retry_count
                print(f"Rate limited! Retrying ({retry_count}/{MAX_RETRIES}) after {backoff_time} seconds...")
                
                with tqdm(total=backoff_time, unit="sec", ncols=50) as pbar:
                    for _ in range(backoff_time):
                        time.sleep(1)
                        pbar.update(1)
                continue

            # NOT FOUND
            elif response.status_code == 404:
                print(f"{response.status_code} {response.reason}. There are no more reviews.")
                break

    ## Final output ---------------------------------------------------------
    # Get pagination offset for next request
    if 'next' in result and result['next'] is not None:
        offset = re.search("^.+offset=([0-9]+).*$", result['next']).group(1)
        print(f"Offset: {offset}")
    else:
        offset = None
        print("No offset found.")

    # Append offset, number of reviews in batch, and app_id
    for rev in reviews:
        rev['offset'] = offset
        rev['n_batch'] = len(reviews)
        rev['app_id'] = app_id

    # Default sleep to decrease rate of calls
    time.sleep(0.5)
    return reviews, offset, response.status_code 