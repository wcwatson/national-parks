"""Driver script to process capta for modeling."""

from copy import deepcopy
import logging

import hydra
from hydra.utils import to_absolute_path
import pandas as pd

from transformations import Transformation
from utils import (
    log_job_succeeded,
    maybe_create_capta_directory,
    setup_logging
)


@hydra.main(config_path='../config', config_name='main', version_base='1.2')
def main(config):
    setup_logging('process_capta')
    maybe_create_capta_directory('processed')
    inputs_config = config.process.inputs
    input_dfs = {
        item['name']: pd.read_csv(to_absolute_path(item['path']))
        for item in inputs_config
    }
    logging.info('Source data collected')
    steps = config.process.steps
    for step in steps:
        logging.info(f'Executing step {step["name"]}')
        step_input_df = deepcopy(input_dfs[step['input']])
        transformations = [
            Transformation(name=t.get('name'), params=t.get('params'))
            for t in step['transformations']
        ]
        for t in transformations:
            logging.info(f'Transforming {step["input"]} via {t.name}')
            step_processed_df = t.transform(step_input_df)
            step_input_df = step_processed_df
        logging.info(f'Caching result as {step["output"]}')
        input_dfs[step['output']] = step_processed_df
        step_output_path = step.get('output_path')
        if step_output_path is not None:
            logging.info('Writing result to capta/processed')
            step_processed_df.to_csv(to_absolute_path(step_output_path))
    log_job_succeeded()


if __name__ == '__main__':
    main()
