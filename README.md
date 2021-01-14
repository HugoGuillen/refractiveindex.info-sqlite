# refractiveindex.info-sqlite
Python 3 + SQLite wrapper for the [refractiveindex.info database](http://refractiveindex.info/) by [Mikhail Polyanskiy](https://github.com/polyanskiy).

Database files parsing was made with a modified version of `refractiveIndex.py` from [PyTMM project](https://github.com/kitchenknif/PyTMM) by [Pavel Dmitriev](https://github.com/kitchenknif).

## Features
- Create SQLite database from refractiveindex yml folder.
- Create SQLite database from refractiveindex.zip url.
- Search database pages by approximate or exact terms.
- Search material data (refractiveindex, extinctioncoefficient) by intervals.
- Execute custom SQL queries on the database.
- Export material data (refractiveindex, extinctioncoefficient) to numpy arrays or csv files.
- Get data (refractiveindex, extinctioncoefficient) at specified wavelengths.

## Usage
Just copy the `refractivesqlite` folder to your project, and you are ready. For more information, see the [Tutorial notebook](Tutorial.ipynb)

## Dependencies
- python 3
- numpy
- scipy
- pyyaml

## Disclaimer
Same as the refractiveindex.info webpage: *NO GUARANTEE OF ACCURACY - Use on your own risk*.

## Version
2021-01-14

---
## Contributors
- [tnorth](https://github.com/tnorth) (Implementation of formulas 4,7,8, and 9)
- [p-tillmann](https://github.com/p-tillmann) (Update database format)
- [lyd1ng](https://github.com/lyd1ng) (PEP 8 compliant code and docstrings)
