# national-parks
> 0.3.0

Simple ML project modeling monthly attendance at national parks using publicly available capta.

## Project Overview
The project is structured as a series of pipeline stages managed by [DVC](https://dvc.org/).
The pipeline may be run with the command `dvc repro [stage-name]`.

| Stage Name             | "Driver" Script               | Inputs & Dependencies                                                                                                                           | Outputs                                    |
|------------------------|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `refresh_source_capta` | `src/refresh_source_capta.py` | <ul><li>`config/refresh_source_capta`</li><li>`src/national_parks/nps`</li></ul>                                                                | `capta/source`                             |
| `process_capta`        | `src/process_capta.py`        | <ul><li>`capta/source`</li><li>`config/process_capta`</li><li>`src/national_parks/processing`</li></ul>                                         | `capta/processed`                          |
| `train_models`         | `src/train_models.py`         | <ul><li>`capta/processed`</li><li>`config/train_models`</li><li>`src/national_parks/model`</li><li>`src/national_parks/visualization`</li></ul> | <ul><li>`models`</li><li>`plots`</li></ul> |

## Capta
The capta for this project are divided into two categories.
1. "Source capta" are those scraped or otherwise taken directly from external sources (the National Parks Service, etc.) with only a bare minimum of transformations applied&mdash;normally only the addition of metadata columns.
    In other projects these might be called "raw data," but as Geoffrey Bowker advised some two decades ago, "[raw data is both an oxymoron and a bad idea](https://mitpress.mit.edu/books/raw-data-oxymoron)."
    These artifacts are produced by the `refresh_source_capta` stage and used as inputs for the `process_capta` stage.
2. "Processed capta" are source capta that have been reformatted, transformed, and possibly had more complex operations performed in preparation for modeling.
    These artifacts are produced by the `process_capta` stage and used as inputs for the `train_models` stage.
    The processing logic is designed to be easily extensible and configurable, and is outlined in [config/process_capta/steps.yaml](config/process_capta/steps.yaml).

## ML Models
The ML models in this project are produced via "recipes" outlined and described in [config/train_models/recipes.yaml](config/train_models/recipes.yaml).
Each recipe invokes an algorithm implemented in the [national_parks.model](src/national_parks/model) package.
Currently, the project makes use of the following algorithms.
- SARIMAX (Seasonal Auto-Regressive Integrated Moving Average with eXogenous features), with the order hyperparameters tuned using [pmdarima](http://alkaline-ml.com/pmdarima/)'s AutoARIMA (a Python port of R's `auto.arima`).
  For implementation details, see the [_arima](src/national_parks/model/_arima.py) model.

## Acknowledgments
- The National Parks Service not only maintains and protects all of the national parks without which this project could not exist, but freely publishes the capta that make this project worth doing.
- This project's structure is adapted from a general ML project structure [outlined by Khuyen Tran](https://towardsdatascience.com/how-to-structure-a-data-science-project-for-readability-and-transparency-360c6716800).
- My parents took my sister and me on camping and hiking trips, and more generally taught us a healthy appreciation for the worth and splendor of nature.
