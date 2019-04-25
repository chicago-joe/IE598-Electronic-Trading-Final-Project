# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from IBridgePy.constants import BrokerName, LogLevel


def get_broker_client(userConfig):
    # these are needed to construct an instance
    logLevel = userConfig.logLevel
    brokerName = userConfig.brokerName

    if logLevel == LogLevel.DEBUG:
        print(__name__ + '::get_broker_client')

    if brokerName == BrokerName.LOCAL_BROKER:
        from .ClientLocalBroker import ClientLocalBroker
        clientLocalBroker = ClientLocalBroker()
        clientLocalBroker.setup_client_local_broker(userConfig)
        return clientLocalBroker
    elif brokerName == BrokerName.IB:
        from .ClientIB import ClientIB
        clientIB = ClientIB()
        clientIB.setup_client_IB(userConfig)
        return clientIB
    else:
        print(__name__ + '::get_broker_client: cannot handle brokerName = %s' % (clientName,))
