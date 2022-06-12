"""Common utility functions"""

import datetime
import logging


def now():
    return datetime.datetime.now().isoformat().replace(':', '-').split(".")[0]


def setup_logging(step_name):
    logging.basicConfig(level=logging.INFO)
    logging.info(f'Logging set up for step - {step_name}')


def log_job_succeeded():
    logging.info('JOB SUCCEEDED')
