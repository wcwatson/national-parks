"""Driver script to process capta for modeling."""

from copy import deepcopy
import logging
import warnings

import hydra
from hydra.utils import to_absolute_path

from national_parks.processing import Transformation
from national_parks.utils.io import (
    get_step_inputs, maybe_create_capta_directory, read_config_file
)
from national_parks.utils.logging import log_job_succeeded, setup_logging


@hydra.main(config_path='../config', config_name='main', version_base='1.2')
def main(config):
    setup_logging('process_capta')
    warnings.filterwarnings('ignore')
    maybe_create_capta_directory('processed')
    stage_config = config.process_capta
    inputs_config = read_config_file(to_absolute_path(stage_config.inputs))
    steps_config = read_config_file(to_absolute_path(stage_config.steps))

    # Collect inputs
    input_dfs = get_step_inputs(inputs_config)
    logging.info('Source data collected')

    # Execute processing steps outlined in configuration fil
    for step in steps_config:
        logging.info(f'Executing step {step.name}')
        step_input_df = deepcopy(input_dfs[step.input])
        transformations = [
            # Using .get() for params allows them to be omitted in the
            # configuration file
            Transformation(name=t.name, params=t.get('params'))
            for t in step.transformations
        ]
        # Every step must execute at least one transformation
        assert len(transformations)
        for t in transformations:
            logging.info(f'Transforming {step.input} via {t.name}')
            step_processed_df = t.transform(step_input_df)
            step_input_df = step_processed_df
        logging.info(f'Caching result as {step.output}')
        input_dfs[step.output] = step_processed_df
        step_output_path = step.get('output_path')
        if step_output_path is not None:
            # Every output captaset written to disk for use by the model
            # training step must include a "dt_pk" column (which may be its
            # index) that contains "datetime primary keys" for time series
            # modeling
            assert (
                'dt_pk' in step_processed_df.columns
                or 'dt_pk' == step_processed_df.index.name
            )
            logging.info('Writing result to capta/processed')
            step_processed_df.to_csv(to_absolute_path(step_output_path))

    log_job_succeeded()


if __name__ == '__main__':
    main()
