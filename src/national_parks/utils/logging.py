"""Logging utility functions."""

import logging


def setup_logging(step_name):
    logging.basicConfig(level=logging.INFO)
    logging.info(f'Logging set up for step - {step_name}')


def log_job_succeeded():
    logging.info('JOB SUCCEEDED')
