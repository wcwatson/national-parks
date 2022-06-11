"""Common utility functions"""

import datetime
import logging


def now():
    return datetime.datetime.now().isoformat().replace(':', '-').split(".")[0]


def setup_logging(step_name):
    logging.basicConfig(
        filename=f'logs/{step_name}_{now()}.log', level=logging.INFO
    )


def log_job_succeeded():
    logging.info('JOB SUCCEEDED')
