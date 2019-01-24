"""
Configure the main program.
This file is adapted from solcore5 (https://github.com/dalonsoa/solcore5)

"""

from configparser import ConfigParser
import os

config_file_dir = os.path.abspath(os.path.dirname(__file__))

default_config_file = "default_config.txt"

home_folder = os.path.expanduser('~')
user_config_file = os.path.join(config_file_dir, 'user_config.txt')


def load_user_config_data():
    if not os.path.exists(user_config_file):
        generate_default_setting()

    config_data = ConfigParser()
    config_data.read(os.path.join(config_file_dir, user_config_file))

    return config_data


def check_config(config_data):
    spice_location = config_data['External programs']['spice']
    if not os.path.exists(spice_location):
        raise ValueError("The designated ngspice location:{} does not exist. "
                         "Please assign a valid path by python setup_spice.py [ngspice_path]".format(spice_location))


user_config_data = load_user_config_data()


def generate_default_setting():
    default_config_data = ConfigParser()
    default_config_data.read(os.path.join(config_file_dir, default_config_file))

    save_user_config(default_config_data)


def set_location_of_spice(location):
    """ Sets the location of the spice executable. It does not test if it works.

    :param location: The location of the spice executable.
    :return: None
    """

    if not os.path.exists(user_config_file):
        generate_default_setting()

    user_config_data = ConfigParser()
    user_config_data.read(user_config_file)

    user_config_data['External programs']['spice'] = location
    save_user_config(user_config_data)


def save_user_config(config_data):
    """ Saves the current user configuration

    :return: None
    """
    with open(user_config_file, 'w') as fp:
        config_data.write(fp)
