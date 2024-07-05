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

from re import match
import pandas as pd
from pandas import Series
from utils.logger import create_logger
logger = create_logger(__name__)

def data_filter_by_dataframe(dataframe_filter, dataframe):
    """Filter a DataFrame using another DataFrame as a filter."""
    selection_mask = data_selection_by_dataframe(dataframe_filter, dataframe)
    return dataframe[selection_mask]


def data_selection_by_dataframe(dataframe_filter, dataframe):
    """Create a selection mask based on values from a filtering DataFrame."""
    keys = list(dataframe_filter.columns.values)
    return dataframe.set_index(keys).index.isin(dataframe_filter.set_index(keys).index)


def data_filter_by_dict(data_filter, dataframe):
    """Filter data based on a dictionary or list of dictionaries."""
    if isinstance(data_filter, list):
        combined_selection = Series([False] * dataframe.shape[0], index=dataframe.index)
        for sub_filter in data_filter:
            combined_selection |= data_selection_by_dict(sub_filter, dataframe)
        return dataframe[combined_selection]

    return dataframe[data_selection_by_dict(data_filter, dataframe)]


def data_selection_by_dict(data_filter, dataframe):
    """Create a selection mask from a dictionary or list of conditions."""
    
    selection = Series([True] * dataframe.shape[0], index=dataframe.index)

    if isinstance(data_filter, list):
        selection = Series([False] * dataframe.shape[0], index=dataframe.index)
        for sub_filter in data_filter:
            selection |= data_selection_by_dict(sub_filter, dataframe)
    else:
        for key, value in data_filter.items():
            try:
                logger.debug(f"Applying filter {key}: {value}")

                if callable(value):
                    selection &= dataframe.apply(value, axis=1)
                elif isinstance(value, str):
                    if match(r"^[<>=]", value):
                        selection &= dataframe.eval(f"`{key}` {value}")
                    else:
                        selection &= dataframe[key].astype(str).str.match(f"^{value}$", na=False)
                elif isinstance(value, list):
                    selection = data_selection_by_dict(value, dataframe)
                else:
                    selection &= (dataframe[key] == value)

            except KeyError as e:
                logger.error(f"Key {key} is missing or not valid in the DataFrame.")
                raise KeyError(f"Key {key} is missing or not valid: {e}")
            except Exception as e:
                logger.error(f"Error applying filter on {key}: {e}")
                raise Exception(f"Error applying filter on {key}: {e}")

    return selection