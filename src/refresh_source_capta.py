"""Runner script to refresh source capta."""

import argparse
import logging
import os
import yaml

import hydra
from hydra.utils import to_absolute_path

from np_source_captaset import NPSCaptaset
from utils import log_job_succeeded, setup_logging


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--park_set',
        type=str,
        choices=['all', 'sample'],
        default='sample',
        help='whether to run on "all" parks or a "sample" (the default)',
    )
    return parser.parse_args()


def _parse_park_name(park_name):
    """Helper function to parse a park name.

    Args:
        park_name (str): a park name as found in the configuration files

    Returns:
        str, str: the long park name and the park type
    """
    park_name_split = park_name.split(' ')
    return ' '.join(park_name_split[:-1]), park_name_split[-1]


@hydra.main(config_path='config', config_name='main')
def main(config):
    setup_logging('refresh_source_capta')
    args = parse_args()
    logging.info(f'Refreshing source capta for {args.park_set} parks')
    park_list_fn = os.path.join(
        'config', 'source_capta', f'{args.park_set}_parks.yml'
    )
    with open(park_list_fn, 'r') as fi:
        parks = yaml.safe_load(fi)

    # Scrape NPS websites
    npsc = NPSCaptaset(
        min_year=config.source_capta.date_range.min,
        max_year=config.source_capta.date_range.max,
        visitor_base_url=config.source_capta.nps.monthly_visitors.base_url,
    )
    for park_name, full_park_name in parks.items():
        long_park_name, park_type = _parse_park_name(full_park_name)
        try:
            npsc.add_and_populate_park(
                name=park_name, long_name=long_park_name, park_type=park_type
            )
            logging.info(f'Successfully added source capta for {park_name}')
        except (KeyError, ValueError) as e:
            logging.info(
                f'Error encountered adding source capta for {park_name} - {e}'
            )
            continue
    logging.info('Park source capta refreshed, writing outputs')
    npsc.write_source_capta(
        visitors_fp=to_absolute_path(
            config.source_capta.nps.monthly_visitors.output_path
        )
    )

    # TODO (WW): weather capta?

    log_job_succeeded()


if __name__ == '__main__':
    main()
