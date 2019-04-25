# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""
from IBridgePy.constants import DataProviderName


def get_data_provider(userConfig):
    name = userConfig.dataProviderName
    if name == DataProviderName.LOCAL_FILE:
        from .local_file import LocalFile
        return LocalFile(userConfig)
    elif name == DataProviderName.RANDOM:
        from .random_data import RandomDataProvider
        return RandomDataProvider(userConfig)
    elif name == DataProviderName.IB:
        from .dataProvider_IB import IB
        return IB(userConfig)
    else:
        print(__name__, 'cannot handle dataProviderName = %s' % (name,))
