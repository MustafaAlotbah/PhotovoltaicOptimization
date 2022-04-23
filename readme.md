# Project

## Introduction

This project is a tool for estimating an optimal design of a grid-connected photovoltaic (PV) open rack panel system, optionally coupled with a battery storage system (BESS).

The underlying input data are Test Reference Years (TRY) hourly meteorological data from the German weather agency (DWD), solar cadaster for the buildings in the North Rhine-Westfalia state of Germany from LANUV, and a mean residential and commercial load profile from BDEW.

## Requirements

The following python modules are needed to run the project

- [NumPy](https://numpy.org)

    ```$conda install numpy```

- [GeoPandas](https://geopandas.org/en/stable/)

    ```$conda install geopandas```

- [Requests](https://docs.python-requests.org/en/latest/)

    ```$conda install requests```

## Gettings started

To get started with the project, install python and fork the project. Then install the aforementioned python modules.

Example scripts are in the folder _tests_.

### Run a simulation

Go to _tests/simulation\_test.py_ and do the following:

- Replace the address with your address

- Make sure the relative path to the photovoltaic models data-set is correct with respect to your working directory and choose your model.

- adjust the load profile

- adjust the simulation parameters

- Run the script

    ```$python -m tests.simulation_test```

### Find an optimal size

Go to _tests/optimization\_test.py_ and do the following:

- Replace the address with your address

- Make sure the relative path to the photovoltaic models data-set is correct with respect to your working directory and choose your model.

- adjust the load profile

- adjust the simulation parameters

- Run the script

    ```$python -m tests.optimization_test```
