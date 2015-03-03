#!/usr/bin/env python
#
# Simple python script to utilize the modes functionality of the touchring
# on Wacom tablets. Make the script executable, (chmod +x) and assign a
# global shortcut to it. Then assign the global shortcut to the button "1"
# (or any other button that you want) of your Wacom tablet.
#
# Copyright (C) 2014 Vangelis Tasoulas <vangelis@tasoulas.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re
import argparse
import logging
import subprocess
import datetime
from collections import OrderedDict

##########################################################################
##########################################################################
##########################################################################
##########################################################################

# A profile defined in the  cannot have more than MAX_MODES_PER_PROFILE.
MAX_MODES_PER_PROFILE = 4

# Define your different profiles with their corresponding modes in the 'PROFILE' dict.
# Look at the examples below, on how to define different profiles.
#
# A profile can have up to MAX_MODES_PER_PROFILE sequential modes, and the mode IDs should
# start from 0 to MAX_MODES_PER_PROFILE - 1. My Wacom Intuos Pro Medium has 4 modes, thus, I
# have set the variable MAX_MODES_PER_PROFILE to '4', and the profile IDs I use are 0, 1, 2, and 3.
# I don't know if there are other devices with less or more modes, but if they do, feel free to
# change the variable and define the corresponding modes accordingly.
#
# In principle, the way the script works could support unlimited modes for any device, and with
# some slight modifications, it could even support changing other wacom keys on the "fly". Not
# only the behavior of the touchring. However, you will not have proper LED indication if you choose
# to add more modes than those supported by your device.
PROFILE = OrderedDict({
    #####################
    ## DEFAULT PROFILE ##
    #####################
    'Default': {
        # Scroll Up/Down in default mode. Use only mode 0.
        '0':{'mode_description': "Default Mode 0 - Scroll Up/Down",
             'apply_to_dev_type': "PAD",
             'cmdlist': {'param_up_key':'AbsWheelUp',
                         'param_up_val':'4' ,
                         'param_down_key':'AbsWheelDown',
                         'param_down_val':'5'}
             }
    },
    ###################
    ## KRITA PROFILE ##
    ###################
    'Krita':{
        # Zoom In/Out in Krita
        '0':{'mode_description': "Krita Mode 0 - Zoom In/Out",
             'apply_to_dev_type': "PAD",
             'cmdlist': {'param_up_key':'AbsWheelUp',
                         'param_up_val':'4' ,
                         'param_down_key':'AbsWheelDown',
                         'param_down_val':'5'}
             },
        # Rotate Right/Left in Krita
        '1':{'mode_description': "Krita Mode 1 - Rotate Right/Left",
             'apply_to_dev_type': "PAD",
             'cmdlist': {'param_up_key':'AbsWheelUp',
                         'param_up_val':'key 4' ,
                         'param_down_key':'AbsWheelDown',
                         'param_down_val':'key 6'}
             }
    },
    ##################
    ## GIMP PROFILE ##
    ##################
    "Gimp": {
        # Scroll up/down in Gimp
        '0':{'mode_description': "Krita Mode 0 - Zoom in/out",
             'apply_to_dev_type': "PAD",
             'cmdlist': {'param_up_key':'AbsWheelUp',
                         'param_up_val':'4' ,
                         'param_down_key':'AbsWheelDown',
                         'param_down_val':'5'}
             },
        # Zoom In/Out in Gimp
        '1':{'mode_description': "Krita Mode 0 - Zoom in/out",
             'apply_to_dev_type': "PAD",
             'cmdlist': {'param_up_key':'AbsWheelUp',
                         'param_up_val':'key alt up' ,
                         'param_down_key':'AbsWheelDown',
                         'param_down_val':'key alt down'}
             },
        # Next/Prev Layer in Gimp
        '2':{'mode_description': "Krita Mode 1 - Rotate Right/left",
             'apply_to_dev_type': "PAD",
             'cmdlist': {'param_up_key':'AbsWheelUp',
                         'param_up_val':'key PgUp' ,
                         'param_down_key':'AbsWheelDown',
                         'param_down_val':'key PgDn'}
             },
    }
})

##########################################################################
##########################################################################
##########################################################################
##########################################################################

__all__ = [
    'quick_regexp', 'print_', 'validate_profile_modes',
    'strip_string_list', 'executeCommand', 'LOG'
]

PROGRAM_NAME = 'toggle-wacom-touchring-mode'
VERSION = '0.0.1'
AUTHOR = 'Vangelis Tasoulas'

LOG = logging.getLogger('default.' + __name__)

################################################
############### HELPER FUNCTIONS ###############
################################################
# I have already added a bunch of helper functions
# that I use often. If you don't need them, feel
# free to remove them (except the error_and_exit() function)

#----------------------------------------------------------------------
def print_(value_to_be_printed, print_indent=0, spaces_per_indent=4, endl="\n"):
    """
    This function, among anything else, it will print dictionaries (even nested ones) in a good looking way

    # value_to_be_printed: The only needed argument and it is the
                           text/number/dictionary to be printed
    # print_indent: indentation for the printed text (it is used for
                    nice looking dictionary prints) (default is 0)
    # spaces_per_indent: Defines the number of spaces per indent (default is 4)
    # endl: Defines the end of line character (default is \n)

    More info here:
    http://stackoverflow.com/questions/19473085/create-a-nested-dictionary-for-a-word-python?answertab=active#tab-top
    """

    if(isinstance(value_to_be_printed, dict)):
        for key, value in value_to_be_printed.iteritems():
            if(isinstance(value, dict)):
                print_('{0}{1!r}:'.format(print_indent * spaces_per_indent * ' ', key))
                print_(value, print_indent + 1)
            else:
                print_('{0}{1!r}: {2}'.format(print_indent * spaces_per_indent * ' ', key, value))
    else:
        string = ('{0}{1}{2}'.format(print_indent * spaces_per_indent * ' ', value_to_be_printed, endl))
        sys.stdout.write(string)

#----------------------------------------------------------------------
def strip_string_list(string_list):
    """
    This function will parse all the elements from a list of strings (string_list),
    and trim leading or trailing white spaces and/or new line characters
    """
    return [s.strip() for s in string_list]

#----------------------------------------------------------------------
class quick_regexp(object):
    """
    Quick regular expression class, which can be used directly in if() statements in a perl-like fashion.

    #### Sample code ####
    r = quick_regexp()
    if(r.search('pattern (test) (123)', string)):
        print(r.groups[0]) # Prints 'test'
        print(r.groups[1]) # Prints '123'
    """
    def __init__(self):
        self.groups = None
        self.matched = False

    def search(self, pattern, string, flags=0):
        match = re.search(pattern, string, flags)
        if match:
            self.matched = True
            if(match.groups()):
                self.groups = re.search(pattern, string, flags).groups()
            else:
                self.groups = True
        else:
            self.matched = False
            self.groups = None

        return self.matched

#----------------------------------------------------------------------
class executeCommand(object):
    """
    Custom class to execute a shell command and
    provide to the user, access to the returned
    values
    """

    def __init__(self, args=None, isUtc=True, shell = False):
        self._stdout = None
        self._stderr = None
        self._returncode = None
        self._timeStartedExecution = None
        self._timeFinishedExecution = None
        self._args = args
        self._shell = shell
        self.isUtc = isUtc
        if(self._args != None):
            self.execute()

    def execute(self, args=None):
        if(args != None):
            self._args = args

        if(self._args != None):
            if(self.isUtc):
                self._timeStartedExecution = datetime.datetime.utcnow()
            else:
                self._timeStartedExecution = datetime.datetime.now()
            p = subprocess.Popen(self._args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=self._shell)
            if(self.isUtc):
                self._timeFinishedExecution = datetime.datetime.utcnow()
            else:
                self._timeFinishedExecution = datetime.datetime.now()
            self._stdout, self._stderr = p.communicate()
            self._returncode = p.returncode
            return 1
        else:
            self._stdout = None
            self._stderr = None
            self._returncode = None
            return 0

    def getStdout(self, getList=True):
        """
        Get the standard output of the executed command

        getList: If True, return a list of lines.
                 Otherwise, return the result as one string
        """

        if getList:
            return self._stdout.split('\n')

        return self._stdout

    def getStderr(self, getList=True):
        """
        Get the error output of the executed command

        getList: If True, return a list of lines.
                 Otherwise, return the result as one string
        """

        if getList:
            return self._stderr.split('\n')

        return self._stderr

    def getReturnCode(self):
        """
        Get the exit/return status of the command
        """
        return self._returncode

    def getTimeStartedExecution(self, inMicroseconds=False):
        """
        Get the time when the execution started
        """
        if(isinstance(self._timeStartedExecution, datetime.datetime)):
            if(inMicroseconds):
                return int(str(calendar.timegm(self._timeStartedExecution.timetuple())) + str(self._timeStartedExecution.strftime("%f")))
        return self._timeStartedExecution

    def getTimeFinishedExecution(self, inMicroseconds=False):
        """
        Get the time when the execution finished
        """
        if(isinstance(self._timeFinishedExecution, datetime.datetime)):
            if(inMicroseconds):
                return int(str(calendar.timegm(self._timeFinishedExecution.timetuple())) + str(self._timeFinishedExecution.strftime("%f")))
        return self._timeFinishedExecution

#----------------------------------------------------------------------

########################################
###### Configure logging behavior ######
########################################

def _configureLogging(loglevel):
    """
    Configures the default logger.

    If the log level is set to NOTSET (0), the
    logging is disabled

    # More info here: https://docs.python.org/2/howto/logging.html
    """
    numeric_log_level = getattr(logging, loglevel.upper(), None)
    try:
        if not isinstance(numeric_log_level, int):
            raise ValueError()
    except ValueError:
        error_and_exit('Invalid log level: %s\n'
        '\tLog level must be set to one of the following:\n'
        '\t   CRITICAL <- Least verbose\n'
        '\t   ERROR\n'
        '\t   WARNING\n'
        '\t   INFO\n'
        '\t   DEBUG    <- Most verbose'  % loglevel)

    defaultLogger = logging.getLogger('default')

    # If numeric_log_level == 0 (NOTSET), disable logging.
    if(not numeric_log_level):
        numeric_log_level = 1000
    defaultLogger.setLevel(numeric_log_level)

    logFormatter = logging.Formatter()

    defaultHandler = logging.StreamHandler()
    defaultHandler.setFormatter(logFormatter)

    defaultLogger.addHandler(defaultHandler)

#######################################################
###### Add command line options in this function ######
#######################################################
# Add the user defined command line arguments in this function

def _command_Line_Options():
    """
    Define the accepted command line arguments in this function

    Read the documentation of argparse for more advanced command line
    argument parsing examples
    http://docs.python.org/2/library/argparse.html
    """

    parser = argparse.ArgumentParser(description=PROGRAM_NAME + " version " + VERSION)

    parser.add_argument("-v", "--version",
                        action="version", default=argparse.SUPPRESS,
                        version=VERSION,
                        help="show program's version number and exit")

    loggingGroupOpts = parser.add_argument_group('Logging Options', 'List of optional logging options')
    loggingGroupOpts.add_argument("-q", "--quiet",
                                  action="store_true",
                                  default=False,
                                  dest="isQuiet",
                                  help="Disable logging in the console. Nothing will be printed.")
    loggingGroupOpts.add_argument("-l", "--loglevel",
                                  action="store",
                                  default="INFO",
                                  dest="loglevel",
                                  metavar="LOG_LEVEL",
                                  help="LOG_LEVEL might be set to: CRITICAL, ERROR, WARNING, INFO, DEBUG. (Default: INFO)")

    opts = parser.parse_args()

    if(opts.isQuiet):
        opts.loglevel = "NOTSET"

    return opts


#----------------------------------------------------------------------
def validate_profile_modes():
    """
    Validate the defined modes on each profile.
    """
    for key in PROFILE.keys():
        # The modes on each profile should not exceed MAX_MODES_PER_PROFILE.
        if len(PROFILE[key]) > MAX_MODES_PER_PROFILE:
            LOG.error("Maximum of {} touchring modes are supported.".format(MAX_MODES_PER_PROFILE))
            exit(1)

        # The modes should be sequential, starting from 0.
        for i in xrange(len(PROFILE[key])):
            if not PROFILE[key].has_key(str(i)):
                LOG.critical("The available modes are '0, 1, 2, 3', and they have to be sequential,\ni.e. you cannot define mode 0 and mode 2 if you do not define mode 1.\n")
                LOG.critical("Currently defined modes for profile '{}': {}.".format(key, str(PROFILE[key].keys())))
                LOG.critical("Please edit the 'PROFILE' dict in this python script accordingly.")
                exit(1)


class toggle_touchring(object):
    """
    Class to change the mode of the touchring
    """
    #----------------------------------------------------------------------
    def __init__(self):
        # Get the status_led0_select file
        cmd = executeCommand('ls /sys/bus/usb/devices/*/wacom_led/status_led0_select', shell=True)
        # If the return status of the ls file == 0, the file exists.
        if cmd.getReturnCode() == 0:
            self.SYS_LED_FILE = cmd.getStdout(False).strip()
            self.CURRENT_MODE = -1
            self.CURRENT_WACOM_PROFILE = "Default"
            self.WACOM_DEVICES = {}
            try:
                # Try to open the file and read its contents
                f = open(self.SYS_LED_FILE)
                self.CURRENT_MODE = int(f.read(1)) % 4
                f.close()
            except:
                LOG.debug("Could not open the '{}' file :(".format(self.SYS_LED_FILE))
                exit(1)

            # Read the current Wacom profile and try to match it with on of the profiles
            # defined in the "PROFILE" dict. If a profile cannot be matched, fall back to
            # the Default profile.
            cmd.execute('qdbus org.kde.Wacom /Tablet org.kde.Wacom.getProfile')
            self.CURRENT_WACOM_PROFILE = cmd.getStdout(False).strip()
            if self.CURRENT_WACOM_PROFILE not in PROFILE.keys():
                LOG.debug("Currently selected profile '{}' is node defined in PROFILE dict. Falling back to 'Default'".format(self.CURRENT_WACOM_PROFILE))
                self.CURRENT_WACOM_PROFILE = "Default"

            LOG.debug("Selected profile '{}' with {} modes.".format(self.CURRENT_WACOM_PROFILE, len(PROFILE[self.CURRENT_WACOM_PROFILE])))

            # Add all of the devices listed by 'xsetwacom --list' in a dict.
            # Use the "type" of the device as the dict key.
            cmd.execute('xsetwacom --list')
            r = quick_regexp()
            for wacom_device in cmd.getStdout():
                if(r.search("(.*)\s+id:\s+(\d+)\s+type:\s+(\w+)", wacom_device)):
                    r.groups = strip_string_list(r.groups)
                    wacom_dev_name = r.groups[0]
                    wacom_dev_id = r.groups[1]
                    wacom_dev_type = r.groups[2]
                    self.WACOM_DEVICES[wacom_dev_type] = {
                        'id': wacom_dev_id,
                        'name': wacom_dev_name
                    }

            #print_(self.WACOM_DEVICES)

        else:
            LOG.debug("Return code of 'ls /sys/bus/usb/devices/*/wacom_led/status_led0_select': {}".format(cmd.getReturnCode()))
            exit(cmd.getReturnCode())


    #----------------------------------------------------------------------
    def toggle_mode(self):
        """
        Loop through the available modes (one at a time)
        """
        cmd = executeCommand(shell=True)
        # Each time the script is executed, find the currently used mode in the profile and change
        # the functionality to that of the next mode.
        # If the last mode is currently used, then loop and start from mode 0.
        if self.CURRENT_MODE <= len(PROFILE[self.CURRENT_WACOM_PROFILE]) - 2:
            self.CURRENT_MODE = self.CURRENT_MODE + 1
        else:
            self.CURRENT_MODE = 0

        # Update the LED indication
        cmd.execute('echo {} > {}'.format(self.CURRENT_MODE, self.SYS_LED_FILE))

        LOG.debug("Changing to mode '{}'".format(PROFILE[self.CURRENT_WACOM_PROFILE][str(self.CURRENT_MODE)]['mode_description']))

        current_mode = PROFILE[self.CURRENT_WACOM_PROFILE][str(self.CURRENT_MODE)]
        dev_name = self.WACOM_DEVICES[current_mode['apply_to_dev_type']]['name']
        # Update the 'param_up_key' and 'param_down_key' properties as defined in the currently used profile.
        cmd.execute('xsetwacom --set "{}" {} {}'.format(dev_name, current_mode['cmdlist']['param_up_key'], current_mode['cmdlist']['param_up_val']))
        cmd.execute('xsetwacom --set "{}" {} {}'.format(dev_name, current_mode['cmdlist']['param_down_key'], current_mode['cmdlist']['param_down_val']))



if __name__ == '__main__':
    """
    Write the main program here
    """
    # Parse the command line options
    options = _command_Line_Options()
    # Configure logging
    _configureLogging(options.loglevel)

    # Validate the user defined profiles
    validate_profile_modes()

    # Create a toggle_touchring() object and call the toggle_mode() method.
    wacom = toggle_touchring()
    wacom.toggle_mode()


