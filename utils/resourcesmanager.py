# Copyright (c) 2024 - Iván Moreno 
#  
# This software is licensed under the MIT License.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import sys
from utils.logger import create_logger
logger = create_logger(__name__)

# Determine the basic path based on whether the application is frozen (packaged)
if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    BASIC_PATH = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
else:
    BASIC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

logger.info("Resources basic path: %s", BASIC_PATH)

def get_resource_path(conf_file):
    """
    Calculate and return the absolute path to a configuration file, handling relative paths based on BASIC_PATH.
    
    Args:
        conf_file (str): The configuration file path, which can be absolute or relative.
    
    Returns:
        str: The absolute path to the configuration file.
    """
    if conf_file.startswith('.'):
        # Handle relative paths assuming they are relative to BASIC_PATH
        return os.path.abspath(os.path.join(BASIC_PATH, conf_file))
    return os.path.abspath(conf_file)

def create_path_if_needed(filepath):
    """
    Ensure that the directory for a given file path exists, creating it if necessary.
    
    Args:
        filepath (str): The path to a file for which the directory needs to be ensured.
    """
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        logger.info("Creating directory path: %s", directory)
        os.makedirs(directory, exist_ok=True)
    else:
        logger.debug("Directory path already exists: %s", directory)