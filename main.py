from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd


def price_parser(price):
    return price.replace('£', '').replace(',', '').replace('pcm', '').strip()


def zoopla():
    url = 'https://www.zoopla.co.uk/to-rent/property/bristol?beds_max=4&beds_min=2&page_size=25&price_frequency=per_month&price_max=2000&view_type=list&q=Bristol&radius=0&results_sort=newest_listings&search_source=refine&added=24_hours&available_from=1months&feature=has_parking_garage'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    props = soup.find_all('a', {'class': 'evnyp9510 css-1gdcbd8-StyledLink-Link e33dvwd0'})

    prices = [i.find('p', {'class': 'css-1w7anck evnyp9531'}).text.strip() for i in props]
    address = [i.find('p', {'class': 'css-5agpw4 evnyp9533'}).text.strip() for i in props]
    nbedrooms = [i.find('p', {'class': 'css-r8a2xt-Text eczcs4p0'}).text.strip() for i in props]
    urls = [i['href'] for i in soup.find_all('a', {'class': 'evnyp9525 css-18ghosu-StyledLink-Link e33dvwd0'})]

    data = {
        'price (pcm)': [int(price_parser(p)) for p in prices],
        'num_beds': [int(n) for n in nbedrooms],
        'address': address,
        'url': ['https://www.zoopla.co.uk'+u for u in urls]
    }

    df = pd.DataFrame(data)
    rent_per_bed = (df['price (pcm)'] / df['num_beds']).astype(int)
    #df = df[rent_per_bed < 800]
    df['Listed On'] = 'Zoopla'
    return df


def rightmove():
    url = 'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=REGION%5E219&maxBedrooms=4&minBedrooms=2&maxPrice=2000&propertyTypes=&maxDaysSinceAdded=1&includeLetAgreed=false&mustHave=garden%2Cparking&dontShow=retirement&furnishTypes=&keywords='

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    card_info = soup.find_all("div", {"class": "propertyCard-details"})

    urls = [i.find('a')['href'] for i in card_info]
    addresses = [i.find('address').text.strip() for i in card_info]
    num_beds_approx = [i.find('h2').text.strip()for i in card_info]
    prices= [i.text for i in soup.find_all("span", {"class": "propertyCard-priceValue"})]
    #desc = [i.text for i in soup.find_all("span", {"data-test": "property-description"})]

    data = {
        'price (pcm)': [price_parser(p) for p in prices],
        'num_beds': [i.split(' ')[0] for i in num_beds_approx],
        'address': addresses,
        'url': ['https://www.rightmove.co.uk' + u for u in urls],
        #'desc': desc
    }

    df = pd.DataFrame(data).dropna()
    df = df[df['price (pcm)'] != '']
    df['price (pcm)'] = df['price (pcm)'].astype(int)
    df['num_beds'] = df['num_beds'].astype(int)
    rent_per_bed = (df['price (pcm)'] / df['num_beds']).astype(int)
    df = df[rent_per_bed < 800]
    df['Listed On'] = 'Rightmove'
    return df

if __name__ == '__main__':

    df_rm = rightmove()
    df_zp = zoopla()
    scraped = pd.concat((df_rm, df_zp))
    scraped['price (pcm)'] = scraped['price (pcm)'].astype(int)
    scraped['num_beds'] = scraped['num_beds'].astype(int)
    scraped['Discovery Date'] = datetime.now()

    prior_properties = pd.read_csv('properties.csv')
    df = pd.concat((prior_properties, scraped))
    df = df.drop_duplicates(subset='url')  # dont include any already found
    df.to_csv('properties.csv', index=False)
