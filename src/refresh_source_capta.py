"""Driver script to refresh source capta."""

import logging
import warnings

import hydra
from hydra.utils import to_absolute_path

from national_parks.nps import NPSCaptaset
from national_parks.utils.io import (
    maybe_create_capta_directory, read_config_file
)
from national_parks.utils.logging import log_job_succeeded, setup_logging
from national_parks.utils.park_names import get_park_type


@hydra.main(config_path='../config', config_name='main', version_base='1.2')
def main(config):
    setup_logging('refresh_source_capta')
    warnings.filterwarnings('ignore')
    maybe_create_capta_directory('source')
    step_config = config.refresh_source_capta

    # Retrieve parks whose capta are to be curated
    park_set = 'all' if step_config.refresh_all_parks else 'sample'
    logging.info(f'Refreshing source capta for {park_set} parks')
    park_list_subconf = step_config.park_sets
    parks = read_config_file(park_list_subconf[park_set])

    # Scrape NPS websites for all source capta
    npsc = NPSCaptaset(
        min_year=step_config.date_range.min,
        max_year=step_config.date_range.max,
        visitor_base_url=step_config.nps.monthly_visitors.base_url,
    )
    for park_code, nps_park_name in parks.items():
        park_type = get_park_type(nps_park_name)
        try:
            npsc.add_and_populate_park(name=park_code, park_type=park_type)
            logging.info(f'Successfully added source capta for {park_code}')
        except (KeyError, ValueError) as e:
            logging.info(
                f'Error encountered adding source capta for {park_code} - {e}'
            )
            continue
    logging.info('Park source capta refreshed, writing outputs')
    monthly_visitors_fp = to_absolute_path(
        step_config.nps.monthly_visitors.output_path
    )
    npsc.write_source_capta(monthly_visitors_fp)

    # TODO (WW): weather capta?

    log_job_succeeded()


if __name__ == '__main__':
    main()
