"""Class for managing model training. Note that all "helper" training functions
must take a DataFrame as input, as well as an optional argument named
outputs_subdir, which specifies identically named subdirectories of models/ and
plots/ where relevant artifacts may be written. Additional keyword arguments
may also be required and are passed in with the ** unpacking operator.
"""

from ._arima import train_and_evaluate_arima_models


class NationalParksModel(object):
    """Object for managing model training.

    Attributes:
        algorithm_name (str): the name of an ML algorithm to apply
        outputs_subdir (str): identically named subdirectory within models/ and
            plots/ where output artifacts should be written
        params (dict): a dictionary of parameters to be passed to the relevant
            algorithm
    """

    def __init__(self, algorithm_name, outputs_subdir, params=None):
        _allowable_algorithms = {
            'arima': train_and_evaluate_arima_models
        }
        if algorithm_name not in _allowable_algorithms:
            raise NotImplementedError(
                f'Unimplemented algorithm {algorithm_name}'
            )
        self.algorithm_name = algorithm_name
        self._algorithm = _allowable_algorithms[algorithm_name]
        self.outputs_subdir = outputs_subdir
        self.params = params if params is not None else {}

    def fit_and_evaluate(self, df):
        """Applies the indicated ML training algorithm to a DataFrame and
        evaluates the result, including writing any artifacts to models/ and
        plots/.

        Args:
            df (pd.DataFrame): a DataFrame to be fit

        Returns:
            None
        """
        self._algorithm(df, self.outputs_subdir, **self.params)
