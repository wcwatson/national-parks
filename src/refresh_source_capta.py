"""Driver script to refresh source capta."""

import logging
import yaml

import hydra
from hydra.utils import to_absolute_path

from np_source_captaset import NPSCaptaset
from utils import log_job_succeeded, setup_logging, parse_park_name


@hydra.main(config_path='../config', config_name='main', version_base='1.2')
def main(config):
    setup_logging('refresh_source_capta')
    park_set = 'all' if config.refresh_source.refresh_all_parks else 'sample'
    logging.info(f'Refreshing source capta for {park_set} parks')
    park_list_subconf = config.refresh_source.park_sets
    park_list_fn = to_absolute_path(park_list_subconf[park_set])
    with open(park_list_fn, 'r') as fi:
        parks = yaml.safe_load(fi)

    # Scrape NPS websites for all source capta
    npsc = NPSCaptaset(
        min_year=config.refresh_source.date_range.min,
        max_year=config.refresh_source.date_range.max,
        visitor_base_url=config.refresh_source.nps.monthly_visitors.base_url,
    )
    for park_name, full_park_name in parks.items():
        _, park_type = parse_park_name(full_park_name)
        try:
            npsc.add_and_populate_park(name=park_name, park_type=park_type)
            logging.info(f'Successfully added source capta for {park_name}')
        except (KeyError, ValueError) as e:
            logging.info(
                f'Error encountered adding source capta for {park_name} - {e}'
            )
            continue
    logging.info('Park source capta refreshed, writing outputs')
    monthly_visitors_fp = to_absolute_path(
        config.refresh_source.nps.monthly_visitors.output_path
    )
    npsc.write_source_capta(monthly_visitors_fp)

    # TODO (WW): weather capta?

    log_job_succeeded()


if __name__ == '__main__':
    main()
