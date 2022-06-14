"""Class for managing source capta from the National Parks Service."""

import pandas as pd

from np_scraper import NationalParkScraper


class NPSCaptaset(object):
    """Object for managing source capta from the National Parks Service.

    Attributes:
        visitor_base_url (str): a base URL for retrieving monthly
            visitor information for every park
        min_year (int): the earliest year of capta to retrieve
        max_year (int): the latest year of capta to retrieve
        parks (dict[str:NationalParkScraper]): an indexed collection of
            NationalParkScraper objects
    """

    def __init__(self, min_year, max_year, visitor_base_url):
        self.min_year = min_year
        self.max_year = max_year
        self.visitor_base_url = visitor_base_url
        self.parks = {}

    def add_and_populate_park(self, name, park_type):
        """Adds a populated NationalParkScraper object to the captaset.

        Args:
            name (str): the abbreviated name for a park (e.g., 'ACAD')
            park_type (str): the type of park (must be listed in
                config/source_capta/park_types.yaml, e.g., 'NP')
        """
        park = NationalParkScraper(name=name, park_type=park_type)
        park_url = self.visitor_base_url.replace('{park}', name)
        park.scrape_monthly_visitors(
            park_url=park_url, max_year=self.max_year, min_year=self.min_year
        )
        # TODO (WW): call additional populate methods
        self.parks[name] = park

    def clear_parks(self):
        self.parks.clear()

    def _collect_monthly_visitors(self):
        """Helper function to collect monthly visitors.

        Returns:
            pd.DataFrame: a DataFrame with monthly visitors across all parks,
                with columns ['full_park_name', 'park_name', 'park_type',
                'year', 'month', 'visitors']
        """
        return pd.concat(
            [park.get_monthly_visitors() for park in self.parks.values()],
            ignore_index=True,
        )

    def write_source_capta(self, visitors_fp):
        """Writes all accumulated source capta.

        Args:
            visitors_fp (str): the filepath where monthly visitor capta should
                be written

        Returns:
            None
        """
        # Monthly visitors
        monthly_visitors_df = self._collect_monthly_visitors()
        monthly_visitors_df.to_csv(visitors_fp, index=False)
        # TODO (WW): usage
