# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""
from broker_factory.records_def import TraderAccountValueRecords, TraderPositionRecords, \
    TraderAccountSummaryRecords, TraderTickStringRecords, TraderTickSizeRecords, \
    TraderTickPriceRecords, TraderTickOptionComputationRecords, BrokerServiceOrderStatusBook


class Broker:
    # aTrader will call brokerService
    # brokerService will call dataProvider
    # brokerService and brokerClient will call each other
    # set by IBridgePy::MarketManagerBase::setup_services
    def __init__(self, userConfig):
        self.userConfig = userConfig
        self.log = userConfig.log
        self.tickTransformer = {'bid_price': 1,
                                'ask_price': 2,
                                'last_traded': 4,
                                'high': 6,
                                'low': 7,
                                'close': 9,
                                'open': 14,
                                'volume': 8
                                }

        # key is str of a str_security, without exchange / primaryExchange
        # str as key is a method to easier searching
        # Value is a tuple (the reqId of reqMktData, str_security)
        self.mktDataRequest = {}

        # Record the time difference between local machine time and server time
        # It is used by get_datetime()
        self.localToServerTimeDiff = None

        self.brokerServiceOrderStatusBook = BrokerServiceOrderStatusBook()
        self.traderTickPriceRecords = TraderTickPriceRecords()
        self.traderTickSizeRecords = TraderTickSizeRecords()
        self.traderTickStringRecords = TraderTickStringRecords()
        self.traderAccountValueRecords = TraderAccountValueRecords()
        self.traderPositionRecords = TraderPositionRecords()
        self.traderAccountSummaryRecords = TraderAccountSummaryRecords()
        self.traderTickOptionComputationRecords = TraderTickOptionComputationRecords()

        # request_data's results will be saved to requestResult, keyed by reqId, value = result
        # It is reset every time when request_data is called.
        self.requestResult = {}

        # the client who will talk to the real broker, who is an instance of IBCpp
        # set by IBridgePy::MarketManagerBase::setup_services
        self.brokerClient = None

        # Generate get_datetime
        self.timeGenerator = None
        self.log.notset(__name__ + '::__init__')

    @property
    def name(self):
        """
        Name of the broker

        :return: string name
        """
        raise NotImplementedError()

    @property
    def versionNumber(self):
        return self.brokerClient.versionNumber

    def disconnect(self):
        self.brokerClient.disconnectWrapper()

    def connect(self):
        self.log.debug(__name__ + '::connect')
        return self.brokerClient.connectWrapper()

    def processMessages(self, timeNow):
        self.log.notset(__name__ + '::processMessages')
        return self.brokerClient.processMessagesWrapper(timeNow)

    def request_data(self, waitForFeedbackInSeconds, repeat, *args):
        self.log.debug(__name__ + '::request_data')
        return self.brokerClient.request_data(waitForFeedbackInSeconds, repeat, *args)

    def add_exchange_primaryExchange_to_security(self, security):
        raise NotImplementedError

    # Used by aTrader and
    def get_datetime(self):
        """
        Get server time on broker's side
        :return: datetime in UTC timezone
        """
        raise NotImplementedError

    # Only used by aTrader
    def use_next_id(self):
        return self.brokerClient.use_next_id()

    # Only used by IBridgePy::MarketManagerBase::setup_services
    def setClientRunningMode_deprecated(self, mode):
        self.log.debug(__name__ + '::setClientRunningMode: mode = %s' % (mode,))
        self.brokerClient.setRunningMode(mode)

    # Only used by ib_client
    def setLocalToServerTimeDiff(self, timeDiff):
        self.log.debug(__name__ + '::setLocalToServerTimeDiff: timeDiff=%s' % (str(timeDiff),))
        self.localToServerTimeDiff = timeDiff

    # Only used by MarketManagerBase
    def get_next_time(self):
        self.log.debug(__name__ + '::get_next_time')
        return self.timeGenerator.get_next_time() + self.localToServerTimeDiff

    # Only used by ib_client
    def setTickPrice(self, tickPriceRecord):
        self.log.notset(__name__ + '::setTickPrice: tickPriceRecord=%s' % (str(tickPriceRecord),))
        self.traderTickPriceRecords.update(tickPriceRecord)

    # Only used by ib_client
    def setTickSize(self, tickSizeRecord):
        self.traderTickSizeRecords.update(tickSizeRecord)

    # Only used by ib_client
    def setTickString(self, tickStringRecord):
        self.traderTickStringRecords.update(tickStringRecord)

    # Only used by ib_client
    def setPosition(self, positionRecord):
        self.log.debug(__name__ + '::setPosition: positionRecord=%s' % (str(positionRecord),))
        self.traderPositionRecords.update(positionRecord)

    # Only used by ib_client
    def setAccountValue(self, accountValueRecord):
        self.log.debug(__name__ + '::setAccountValue: accountValueRecord=%s' % (accountValueRecord,))
        self.traderAccountValueRecords.update(accountValueRecord)

    # Only used by ib_client
    def setOrderStatus(self, orderStatusRecord):
        orderId = orderStatusRecord.orderId
        accountCode = self.brokerClient.getAccountCodeFromOrderId(orderId)
        orderStatusRecord.setAccountCode(accountCode)
        self.brokerServiceOrderStatusBook.updateFromOrderStatus(orderStatusRecord)

    # Only used by ib_client
    def setOpenOrder(self, openOrderRecord):
        self.brokerServiceOrderStatusBook.updateFromOpenOrder(openOrderRecord)

    # Only used by ib_client
    def setAccountSummary(self, accountSummaryRecord):
        self.log.debug(__name__ + '::setAccountSummary: accountSummaryRecord=%s' % (str(accountSummaryRecord),))
        self.traderAccountSummaryRecords.update(accountSummaryRecord)

    # Only used by ib_client
    def setExecDetails(self, execDetailsRecord):
        self.brokerServiceOrderStatusBook.updateFromExecDetails(execDetailsRecord)

    # Only used by ib_client
    def setTickOptionComputation(self, tickOptionComputation):
        self.traderTickOptionComputationRecords.update(tickOptionComputation)
