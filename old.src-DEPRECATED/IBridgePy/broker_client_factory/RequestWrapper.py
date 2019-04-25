#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
There is a risk of loss when trading stocks, futures, forex, options and other
financial instruments. Please trade with capital you can afford to
lose. Past performance is not necessarily indicative of future results.
Nothing in this computer program/code is intended to be a recommendation, explicitly or implicitly, and/or
solicitation to buy or sell any stocks or futures or options or any securities/financial instruments.
All information and computer programs provided here is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how to use these information and
are solely responsible any consequences of using these information.

If you have any questions, please send email to IBridgePy@gmail.com
All rights reserved.
"""

from broker_client_factory.CallBacks import CallBacks


class RequestWrapper(CallBacks):
    def connectWrapper(self):
        raise NotImplementedError

    def disconnectWrapper(self):
        raise NotImplementedError

    def reqPositionsWrapper(self):
        raise NotImplementedError

    def reqCurrentTimeWrapper(self):
        raise NotImplementedError

    def reqAllOpenOrdersWrapper(self):
        raise NotImplementedError

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        raise NotImplementedError

    def reqAccountSummaryWrapper(self, reqId, group, tag):
        raise NotImplementedError

    def reqIdsWrapper(self):
        raise NotImplementedError

    def reqHistoricalDataWrapper(self, reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        raise NotImplementedError

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot):
        raise NotImplementedError

    def cancelMktDataWrapper(self, reqId):
        raise NotImplementedError

    def reqRealTimeBarsWrapper(self, reqId, contract, barSize, whatToShow, useRTH):
        raise NotImplementedError

    def placeOrderWrapper(self, orderId, contract, order):
        raise NotImplementedError

    def reqContractDetailsWrapper(self, reqId, contract):
        raise NotImplementedError

    def calculateImpliedVolatilityWrapper(self, reqId, contract, optionPrice, underPrice):
        raise NotImplementedError

    def reqScannerSubscriptionWrapper(self, reqId, subscription):
        raise NotImplementedError

    def cancelScannerSubscriptionWrapper(self, tickerId):
        raise NotImplementedError

    def cancelOrderWrapper(self, orderId):
        raise NotImplementedError

    def reqScannerParametersWrapper(self):
        raise NotImplementedError

    def processMessagesWrapper(self, timeNow):
        raise NotImplementedError



