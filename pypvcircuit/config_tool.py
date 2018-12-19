"""
Configure the main program.
This file is adapted from solcore5 (https://github.com/dalonsoa/solcore5)

"""


from configparser import ConfigParser
import os

home_folder = os.path.expanduser('~')
user_config = os.path.join(home_folder, '.solcore_config.txt')
user_config_data = ConfigParser()
user_config_data.read(user_config)


def set_location_of_spice(location):
    """ Sets the location of the spice executable. It does not test if it works.

    :param location: The location of the spice executable.
    :return: None
    """
    user_config_data['External programs']['spice'] = location
    save_user_config()

def save_user_config():
    """ Saves the current user configuration

    :return: None
    """
    with open(user_config, 'w') as fp:
        user_config_data.write(fp)

