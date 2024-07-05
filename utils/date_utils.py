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

import pandas as pd

from utils.app_config import AppConfig
from utils.util_constants import CONF_DAYFIRST

DAY_FIRST = AppConfig()[CONF_DAYFIRST] if CONF_DAYFIRST in AppConfig() else True

def safe_to_datetime(val, errors='raise', dayfirst=DAY_FIRST):
    try:
        return pd.to_datetime(val, dayfirst=dayfirst)
    except (ValueError, TypeError):
        if errors == 'raise':
            raise
        elif errors == 'coerce':
            return pd.NaT
        elif errors == 'ignore':
            return val
        else:
            raise ValueError(f"Invalid value for 'errors' parameter: {errors}")