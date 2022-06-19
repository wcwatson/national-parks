"""Driver script to train models."""

import logging
import os
import warnings

import hydra
from hydra.utils import to_absolute_path
import pandas as pd

from national_park_model import NationalParkModel
from utils import get_step_inputs, log_job_succeeded, setup_logging


def _maybe_make_output_directories():
    """Helper function to create directories for step outputs. Exists purely to
    make the structure of this step's main() function parallel to those of other
    steps.
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
    step_config = config.train_models

    # Retrieve input capta and perform simple preparations for modeling
    modeling_dfs = get_step_inputs(step_config.inputs)
    modeling_dfs = {
        k: _time_index_dataframe(df)
        for k, df in modeling_dfs.items()
    }
    logging.info('Modeling capta retrieved')

    # Apply all modeling procedures outlined in configuration file
    # TODO (WW): adjust to configs following reallocation
    for model_recipe in step_config.model_recipes:
        logging.info(f'Building {model_recipe.name}')
        df = modeling_dfs[model_recipe.input]
        model = NationalParkModel(
            algorithm_name=model_recipe.algorithm,
            outputs_subdir=model_recipe.outputs_subdir,
            params=model_recipe.params
        )
        model.fit_and_evaluate(df)

    log_job_succeeded()


if __name__ == '__main__':
    main()
