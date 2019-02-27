import urllib3
import certifi
import time
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from bld.project_paths import project_paths_join as ppj


def load_webdriver(webdriver_path, url, delay):
    """This functions loads the firefox webdriver for a prespecified 
    url. The sec argument generates some delay to ensure that the 
    driver is properly loaded before further code is run."""

    # Lod webdriver with specified url.
    driver = webdriver.Firefox(executable_path=webdriver_path)
    driver.get(url)

    # Use some delay, since webdriver needs some time to load.
    time.sleep(delay)

    return driver


def get_mun_soup(driver):
    """Given a webdriver object this function returns the
    corresponding soup object containing all municipalites
    listed on current site."""

    # Secure https sites.
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())

    # Get soup object.
    page = driver.execute_script('return document.body.innerHTML')
    soup = BeautifulSoup(''.join(page), 'html.parser')
    mun_soup = soup.find_all("tr", {"role": "row"})[1:]
    return soup, mun_soup


def fill_mun_dict(mun, elec_df):
    """This functions stores the name, state and url of a single
    municipality in a dictionary. Afterwards this dict is appended to 
    a prespecified dataframe."""

    mun_dict = dict()
    mun_dict["mun_url"] = mun.a["href"]
    mun_dict["mun_name"] = mun.a.text
    mun_dict["state"] = mun.find_all("td")[2].text

    elec_df = elec_df.append(mun_dict, ignore_index=True)
    return elec_df


def run_scraping(driver):
    """This function scrapes all relevant information of municipalities<
    in the state of NRW. As soon as the end of a page is read, the scraping
    automatically continues on the next site, until the last page of 
    the votemanager site is reached."""

    # Dataframe to store data.
    elec_df = pd.DataFrame()

    # Loop through all available sites.
    while True:
        soup, mun_soup = get_mun_soup(driver)

        # Loop through all municipalities on each site.
        for mun in mun_soup:
            if mun.find_all("td")[2].text == "Nordrhein-Westfalen":
                elec_df = fill_mun_dict(mun, elec_df)

        # Go to next page when all municipalties are scraped.
        driver.find_element_by_xpath('//a[text()="weiter"]').click()

        # After each iteration check if last page is reached.
        if soup.find("li", {"class": "paginate_button next disabled"}) != None:
            driver.close()
            break

    # Identify scrapable municipalties by checking url string.
    url_indicators = ["://votemanager.", "://wahlen."]
    elec_df["scrapable"] = elec_df["mun_url"].apply(
        lambda x: 1 if any(key in x for key in url_indicators) else 0)
    return elec_df

if __name__ == '__main__':
    # Open Firefox driver and open votemanager site.
    webdriver_path = r"C:/Users/maxim/Documents/master_eco/eco/geckodriver.exe"
    votemanger_url = "http://wahlen.votemanager.de"
    driver = load_webdriver(webdriver_path, votemanger_url, 5)

    # Run scraping process, afterwards store resulting dataframe.
    elec_df = run_scraping(driver)
    elec_df = elec_df[elec_df["scrapable"] == 1]
    elec_df.drop("scrapable",  axis=1, inplace=True)

    elec_df.to_csv(ppj("OUT_DATA_ELEC", "scrapable_mun.csv"), index=False)