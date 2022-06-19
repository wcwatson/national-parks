"""Driver script to process capta for modeling."""

from copy import deepcopy
import logging
import warnings

import hydra
from hydra.utils import to_absolute_path

from transformations import Transformation
from utils import (
    get_step_inputs,
    log_job_succeeded,
    maybe_create_capta_directory,
    setup_logging
)


@hydra.main(config_path='../config', config_name='main', version_base='1.2')
def main(config):
    setup_logging('process_capta')
    warnings.filterwarnings('ignore')
    maybe_create_capta_directory('processed')
    step_config = config.process_capta

    # Collect inputs
    input_dfs = get_step_inputs(step_config.inputs)
    logging.info('Source data collected')

    # Execute processing steps outlined in configuration fil
    # TODO (WW): adjust once these steps have been moved
    steps = step_config.processing_steps
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
            # Every output captaset written to disk for use by the model
            # training step must include a "dt_pk" column that contains
            # "datetime primary keys" for time series modeling
            # assert 'dt_pk' in step_processed_df.columns
            logging.info('Writing result to capta/processed')
            step_processed_df.to_csv(to_absolute_path(step_output_path))

    log_job_succeeded()


if __name__ == '__main__':
    main()
