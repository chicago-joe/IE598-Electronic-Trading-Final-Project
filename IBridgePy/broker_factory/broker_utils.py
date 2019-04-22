# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from IBridgePy.constants import BrokerName, LogLevel


def get_broker(userConfig):
    if userConfig.logLevel == LogLevel.DEBUG:
        print(__name__ + '::get_broker_client')
    name = userConfig.brokerName
    if name == BrokerName.LOCAL_BROKER:
        from .local_broker import LocalBroker
        return LocalBroker(userConfig)
    elif name == BrokerName.IB:
        from .interactiveBrokers import InteractiveBrokers
        return InteractiveBrokers(userConfig)
    else:
        print(__name__ + '::get_broker: cannot handle brokerName=%s' % (name,))


