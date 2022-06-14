# national-parks
> 0.2.0

Simple ML project using publicly available National Parks capta.

## Project Overview
The project is structured as a series of pipeline stages managed by [DVC](https://dvc.org/).
Each pipeline stage may be run with the command `dvc repro step-name`.

| Stage Name       | "Driver" Script               | Inputs & Dependencies                                                                            | Outputs             |
|------------------|-------------------------------|--------------------------------------------------------------------------------------------------|---------------------|
| `refresh_source` | `src/refresh_source_capta.py` | <ul><li>`config/main.yaml`</li><li>`config/source_capta/*`</li></ul>                             | `capta/source/*`    |
| `process`        | `src/process_capta.py`        | <ul><li>`config/main.yaml`</li><li>`config/processed_capta/*`</li><li>`capta/source/*`</li></ul> | `capta/processed/*` |

## Capta
The capta for this project are divided into two categories.
1. "Source capta" are those scraped or otherwise taken directly from external sources (the National Parks Service, etc.), with a bare minimum of transformations applied&mdash;normally only the addition of metadata columns.
    In other projects these might be called "raw data," but as Geoffrey Bowker advised some two decades ago, "[raw data is both an oxymoron and a bad idea](https://mitpress.mit.edu/books/raw-data-oxymoron)."
    These artifacts are produced by the `refresh_source` stage and used as inputs for the `process` stage.
2. "Processed capta" are source capta that have been reformatted, transformed, and possibly had more complex operations performed in preparation for modeling.
    These artifacts are produced by the `process` stage and used as inputs for the [TK] stage.

## ML Models
TK

## Acknowledgments
- The National Parks Service not only maintains and protects all of the national parks without which this project could not exist, but freely publishes the capta that make this project worth doing.
- This project's structure is adapted from a general ML project structure [outlined by Khuyen Tran](https://towardsdatascience.com/how-to-structure-a-data-science-project-for-readability-and-transparency-360c6716800).
- My parents took my sister and me camping, hiking, and taught us a healthy appreciation for the worth and splendor of mature.
