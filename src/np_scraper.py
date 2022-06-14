"""Class for managing scraping functionality for a single national park."""

from copy import deepcopy
import requests
import time

from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd


def _scrape_url(url, sleep_t=1):
    """Simple helper function that avoids spamming client servers"""
    response = requests.get(url)
    time.sleep(sleep_t)
    return response


def _bs_table_to_pandas(html_table, header=True):
    """Helper function for parsing BeautifulSoup tables to pandas.

    Args:
        html_table (bs4.element.Tag): a BeautifulSoup-extracted HTML table
        header (bool): whether the table's first row should be read as a header

    Returns:
        pd.DataFrame
    """
    df_rows = []
    for tr in html_table.children:
        row = [td.text for td in tr]
        # Ignore empty rows and rows populated only by empty values
        if len(row) and min(len(c) for c in row):
            df_rows.append(row)
    if header:
        df = pd.DataFrame(df_rows[1:], columns=df_rows[0])
    else:
        df = pd.DataFrame(df_rows)
    return df


class NationalParkScraper(object):
    """Webscraping and capta storage class for an individual national park.

    Attributes:
        name (str): the abbreviated name or 'code' for a park (e.g., 'ACAD')
        park_type (str): the type of park (must be listed in
            config/source_capta/park_types.yaml, e.g., 'NP')
        _monthly_visitors (pd.DataFrame): a DataFrame (NB: use
            get_monthly_visitors() to retrieve capta associated with this
            object, do not retrieve it directly)
    """

    def __init__(self, name, park_type):
        self.name = name
        self.park_type = park_type
        self._monthly_visitors = None

    def scrape_monthly_visitors(self, park_url, min_year, max_year):
        """Scrapes and caches monthly visitors from the relevant NPS site.

        Args:
            park_url (str): the URL for retrieving monthly visitor data
            min_year (int): the earliest year of capta to retrieve
            max_year (int): the latest year of capta to retrieve

        Raises:
            ValueError: if no HTTP response is received
            KeyError: if no capta table can be located in the response
        """
        # Initial query to NPS
        park_response = _scrape_url(park_url)
        if park_response:
            park_soup = BeautifulSoup(park_response.content, 'html.parser')
            # The publicly viewable NPS website is itself really just a
            # 'view' - i.e., an iframe wrapped around another website with
            # the actual capta
            park_suburl = park_soup.find('iframe')['src']
            capta_url = 'https://irma.nps.gov/' + park_suburl
            capta_response = _scrape_url(capta_url)
            capta_soup = BeautifulSoup(capta_response.content, 'html.parser')
            # The desired table has 14 columns: one for the year, one for
            # each month's visitor counts, and one for the total annual
            # visitor count
            capta_table = capta_soup.find('table', cols='14')
            if capta_table is not None:
                capta_df = _bs_table_to_pandas(capta_table)
                # The 'Total' column is redundant information and can always be
                # recalculated, so there's no need to store it
                capta_df = capta_df.drop(columns='Total')
                # Convert to numeric where possible, catching numbers written
                # with commas
                capta_df = capta_df.apply(
                    lambda x: pd.to_numeric(
                        x.astype(str).str.replace(',', ''), errors='ignore'
                    )
                )
                # Filter out any years outside those specified in the
                # configuration files
                capta_df = capta_df.query(f'{min_year} <= Year <= {max_year}')
                self._monthly_visitors = capta_df
            else:
                raise KeyError('Could not retrieve capta')
        else:
            raise ValueError('No HTTP response received')

    def get_monthly_visitors(self):
        """Adds metadata columns to the cached DataFrame and returns it.

        Returns:
            pd.DataFrame: a DataFrame with columns ['full_park_name',
                'park_name', 'park_type', 'year', 'month', 'visitors']

        Raises:
            AttributeError: if visitor capta has not been scraped yet
        """
        if self._monthly_visitors is None:
            raise AttributeError('Monthly visitors have not been scraped')
        return_df = deepcopy(self._monthly_visitors)
        return_df['park_name'] = self.name
        return_df['park_type'] = self.park_type
        return return_df

    def scrape_monthly_use(self, park_url, min_year, max_year):
        """Scrapes and caches usage information from the relevant NPS site.

        Args:
            park_url (str): the URL for retrieving monthly visitor data
            min_year (int): the earliest year of capta to retrieve
            max_year (int): the latest year of capta to retrieve

        Raises:
            ValueError: if no HTTP response is received
            KeyError: if no capta table can be located in the response
        """
        # driver = webdriver.Chrome(ChromeDriverManager(path='.').install())
        # TODO (WW): for another feature branch
