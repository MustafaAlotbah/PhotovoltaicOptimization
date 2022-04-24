# Project

## Introduction

This project is a tool for estimating an optimal design of a grid-connected photovoltaic (PV) open rack panel system, optionally coupled with a battery storage system (BESS).

The underlying input data are Test Reference Years ([TRY](https://www.dwd.de/DE/leistungen/testreferenzjahre/testreferenzjahre.html;)) hourly meteorological data from the German weather agency ([DWD](https://www.dwd.de/EN)), solar cadaster for the buildings in the North Rhine-Westfalia state of Germany from [LANUV](https://www.lanuv.nrw.de) ([click here](https://www.opengeodata.nrw.de/produkte/umwelt_klima/klima/solarkataster/photovoltaik/)), and a mean residential and commercial load profile from [BDEW](https://www.bdew.de) ([click here](https://www.bdew.de/energie/standardlastprofile-strom/)).

## Requirements

The following python modules are needed to run the project

- [Anaconda](https://docs.anaconda.com/anaconda/install/index.html) (Optional but recommended)

- [Python 3.8.13](https://www.python.org/downloads/release/python-3813/)

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
