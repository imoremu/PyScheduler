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

import logging
import logging.config
import json
import os


def create_logger(name):
    # Get the path to the configuration file
    config_path = os.path.join(os.path.dirname(__file__), '../conf/logger_conf.json')

    # Load the configuration from the json file
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Create directories needed for file handlers
    for handler in config['handlers'].values():
        if 'filename' in handler:
            log_directory = os.path.dirname(handler['filename'])
            if not os.path.exists(log_directory):
                os.makedirs(log_directory)

    logging.config.dictConfig(config)

    # Create and return the logger
    return logging.getLogger(name)