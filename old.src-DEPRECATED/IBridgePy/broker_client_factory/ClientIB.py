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

from IBridgePy.constants import LiveBacktest
from broker_client_factory.RequestImpl import RequestImpl


class ClientIB(RequestImpl):
    def setup_client_IB(self, userConfig):
        self.setup(userConfig)
        # these are needed to construct an instance
        self.host = userConfig.host
        self.port = userConfig.port
        self.clientId = userConfig.clientId

        self.log.debug(__name__ + '::setup_client_IB')
        self.setRunningMode(LiveBacktest.LIVE)
        # ClientIB does not need a dataProvider

    def isConnectedWrapper(self):
        self.log.debug(__name__ + '::isConnectedWrapper')
        return self.isConnected()

    def connectWrapper(self):
        self.log.debug(__name__ + '::connectWrapper')
        self.connect(self.host, self.port, self.clientId)

    def disconnectWrapper(self):
        self.disconnect()

    def reqPositionsWrapper(self):
        self.reqPositions()

    def reqCurrentTimeWrapper(self):
        self.reqCurrentTime()

    def reqAllOpenOrdersWrapper(self):
        self.reqAllOpenOrders()

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        self.reqAccountUpdates(subscribe, accountCode)

    def reqAccountSummaryWrapper(self, reqId, group, tag):
        self.reqAccountSummary(reqId, group, tag)

    def reqIdsWrapper(self):
        self.reqIds(0)

    def reqHistoricalDataWrapper(self, reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        self.reqHistoricalData(reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate)

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot):
        self.reqMktData(reqId, contract, genericTickList, snapshot)

    def cancelMktDataWrapper(self, reqId):
        self.cancelMktData(reqId)

    def reqRealTimeBarsWrapper(self, reqId, contract, barSize, whatToShow, useRTH):
        self.reqRealTimeBars(reqId, contract, barSize, whatToShow, useRTH)

    def placeOrderWrapper(self, orderId, contract, order):
        self.placeOrder(orderId, contract, order)

    def reqContractDetailsWrapper(self, reqId, contract):
        self.reqContractDetails(reqId, contract)

    def calculateImpliedVolatilityWrapper(self, reqId, contract, optionPrice, underPrice):
        self.calculateImpliedVolatility(reqId, contract, optionPrice, underPrice)

    def reqScannerSubscriptionWrapper(self, reqId, subscription):
        self.reqScannerSubscription(reqId, subscription)

    def cancelScannerSubscriptionWrapper(self, tickerId):
        self.cancelScannerSubscription(tickerId)

    def cancelOrderWrapper(self, orderId):
        self.cancelOrder(orderId)

    def reqScannerParametersWrapper(self):
        self.reqScannerParameters()

    def processMessagesWrapper(self, dummy):
        self.log.debug(__name__ + '::processMessagesWrapper: dummyTimeNow=%s' % (dummy,))
        self.processMessages()  # IBCpp function
        return True
