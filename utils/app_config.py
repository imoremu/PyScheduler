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

# config.py
class AppConfig:
    """ 
    Application configuration settings

    This class is used to store configuration settings for the application. 
    It can be used to load settings from a dictionary or argparse.Namespace object,
    and retrieve or modify settings using dictionary-like syntax.
    """
    settings = {}

    @classmethod
    def load_args(cls, args):
        """ Load configuration settings from argparse.Namespace """
        args_dict = vars(args)
        cls.load_dict(args_dict)

    @classmethod
    def load_dict(cls, config_dict):
        """ Load configuration settings from a dictionary """
        for key, value in config_dict.items():
            cls.settings[key] = value

    @classmethod
    def get(cls, key):
        return cls.settings.get(key)

    @classmethod
    def set(cls, key, value):
        cls.settings[key] = value

    @classmethod
    def __getitem__(cls, key):
        return cls.settings[key]

    @classmethod
    def __setitem__(cls, key, value):
        cls.settings[key] = value

    @classmethod
    def __contains__(cls, key):
        return key in cls.settings
    
    @classmethod
    def __delitem__(cls, key):
        del cls.settings[key]

app_config = AppConfig()