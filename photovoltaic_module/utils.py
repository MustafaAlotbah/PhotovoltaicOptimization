import os
import json

# globals

def charge_of_electron():
    return 1.602176634e-19


def boltzmann():
    return 1.38064852e-23


def celsius2kelvin(t):
    return t + 273.15


def kelvin2celsius(t):
    return t - 273.15


def load_simple_models(file_path):
    with open(file_path, newline='') as file:
        models = json.load(file)

    return models
