# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from IBridgePy.IbridgepyTools import add_exchange_primaryExchange_to_security
from broker_factory.interactiveBrokers import InteractiveBrokers


class LocalBroker(InteractiveBrokers):
    def __init__(self, userConfig):
        InteractiveBrokers.__init__(self, userConfig)

    @property
    def name(self):
        return "LocalBroker"

    def get_datetime(self):
        timeNow = self.timeGenerator.get_current_time()
        self.log.debug(__name__ + '::get_datetime: timeNow=%s' % (timeNow,))
        return timeNow

    def add_exchange_primaryExchange_to_security(self, security):
        """
        This function stays here because it is specific to brokers.
        The solution can be local file, security_info.csv or get from IB server directly
        :param security:
        :return: adjusted security with correct exchange and primaryExchange
        """
        return add_exchange_primaryExchange_to_security(security)
