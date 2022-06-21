"""Driver script to train models."""

import logging
import os
import warnings

import hydra
from hydra.utils import to_absolute_path
import pandas as pd

from national_parks.model import NationalParksModel
from national_parks.utils.io import get_step_inputs, read_config_file
from national_parks.utils.logging import log_job_succeeded, setup_logging


def _maybe_make_output_directories():
    """Helper function to create directories for step outputs. Exists purely to
    make the structure of this step's main() function parallel to those of
    other steps.
    """
    for directory in ['models', 'plots']:
        abs_path = to_absolute_path(directory)
        os.makedirs(abs_path, exist_ok=True)


def _time_index_dataframe(df, dt_col='dt_pk', freq='M', method='ffill'):
    """Helper function to temporally index a DataFrame for training.

    Args:
        df (pd.DataFrame): a DataFrame
        dt_col (str): a column containing datetime-parsable entries
        freq (str): a frequency input to pd.asfreq()
        method (str): an imputation method input to pd.asfreq()

    Returns:
        pd.DataFrame: a modified copy of df
    """
    df[dt_col] = pd.to_datetime(df[dt_col])
    df = df.set_index(dt_col)
    return df.asfreq(freq, method=method)


@hydra.main(config_path='../config', config_name='main', version_base='1.2')
def main(config):
    setup_logging('train_models')
    warnings.filterwarnings('ignore')
    _maybe_make_output_directories()
    stage_config = config.train_models
    inputs_config = read_config_file(to_absolute_path(stage_config.inputs))
    recipes_config = read_config_file(to_absolute_path(stage_config.recipes))

    # At this stage only simple transformations, such as setting a datetime
    # index from an already-existing column, should be performed in preparation
    # for modeling. Anything more complex should have already been handled in
    # the previous DVC stage.
    modeling_dfs = get_step_inputs(inputs_config)
    modeling_dfs = {
        k: _time_index_dataframe(df)
        for k, df in modeling_dfs.items()
    }
    logging.info('Modeling capta retrieved')

    for recipe in recipes_config:
        logging.info(f'Building {recipe.name}')
        df = modeling_dfs[recipe.input]
        model = NationalParksModel(
            algorithm_name=recipe.algorithm,
            outputs_subdir=recipe.outputs_subdir,
            params=recipe.params
        )
        model.fit_and_evaluate(df)

    log_job_succeeded()


if __name__ == '__main__':
    main()
