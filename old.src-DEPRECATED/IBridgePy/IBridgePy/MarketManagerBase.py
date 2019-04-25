# -*- coding: utf-8 -*-
import datetime as dt

import broker_client_factory
import broker_factory as broker_factory
import data_provider_factory
from BasicPyLib.MarketCalendarWrapper import MarketCalendarWrapper
from IBridgePy.IbridgepyTools import Event, RepeaterEngine
from IBridgePy.TimeGenerator import TimeGenerator
from IBridgePy.constants import TimeConcept, RunMode, MarketManagerRunMode, DataProviderName, LogLevel, BrokerName
from sys import exit


class MarketManager:
    def __init__(self, trader, userConfig, userConfig_dataProvider=None):
        """
        Change to this way because MarketManager is used to run multiple fileNames
        Trader is not combined into userConfig because trader.funcs needs to be exposed to users
        by define_functions.txt
        If dataProvider is IB or other real dataProvider, a client to the dataProvider is needed.
        In this case, userConfig_dataProvider is needed to build a dataProvider that has a valid dataProviderClient
        """
        userConfig = setup_services(userConfig, trader=trader)

        self.userConfig = userConfig  # TODO remove it
        self.log = userConfig.log
        self.trader = userConfig.trader

        # If dataProvider is IB or other real dataProvider, a client to the dataProvider is needed.
        # In this case, userConfig_dataProvider is needed to build a dataProvider that has a valid dataProviderClient
        if userConfig_dataProvider is not None:
            self.trader.brokerService.brokerClient.dataProvider = setup_services(userConfig_dataProvider).dataProvider

        self.log.debug(__name__ + '::__init__')

        # get market open/close time every day
        # run_like_quantopian will run following these times
        self.marketCalendar = MarketCalendarWrapper(self.userConfig.marketName).getMarketCalendar()

        self.lastCheckConnectivityTime = dt.datetime.now()
        self.numberOfConnection = 0

        # It will be checked only once at the beginning of a new day
        # then, the status will be saved for the whole day
        # Only use in run_like_quantopian mode
        self.tradingDay = True
        self.todayMarketOpenTime = None
        self.todayMarketCloseTime = None

        # Record the last display message
        # When a new message is to be displayed, it will compare with the last
        # message. If they are not same, then display it
        self.lastDisplayMessage = ''

        # Two modes: Trading and Ingesting, used to control display messages
        self.runMode = userConfig.marketManagerConfig.runMode

    def run_once(self):
        self.trader.connect()
        self.trader.initialize_Function()

    def run(self):
        self.log.debug(__name__ + '::run: START')
        self.run_once()

        if self.userConfig.runMode == RunMode.REGULAR:
            self.run_regular()
        elif self.userConfig.runMode in [RunMode.RUN_LIKE_QUANTOPIAN, RunMode.SUDO_RUN_LIKE_QUANTOPIAN]:
            self.run_q()
        self.log.info(__name__ + '::run: END')

    def run_regular(self):
        self.log.debug(__name__ + '::run_regular')
        re = RepeaterEngine(self.userConfig.liveOrBacktest,
                            self.trader.get_next_time,
                            self.trader.getWantToEnd)
        repeater1 = Event.RepeatedEvent(1,
                                        self.trader.processMessages)  # sequence matters!!! First scheduled, first run.
        repeater2 = Event.RepeatedEvent(self.userConfig.repBarFreq,
                                        self.trader.repeat_Function)
        re.schedule_event(repeater1)
        re.schedule_event(repeater2)
        # for ct in re.repeatedEvents:
        #    print(ct, re.repeatedEvents[ct])
        re.repeat()

    def run_q(self):
        self.log.debug(__name__ + '::run_q')
        self._check_at_beginning_of_a_day(self.trader.get_datetime())
        re = RepeaterEngine(self.userConfig.liveOrBacktest,
                            self.trader.get_next_time,
                            self.trader.getWantToEnd)
        repeater1 = Event.RepeatedEvent(1,
                                        self.trader.processMessages)  # sequence matters!!! First scheduled, first run.
        repeater2 = Event.RepeatedEvent(self.userConfig.repBarFreq, self.trader.repeat_Function,
                                        passFunc=self._check_trading_hours)

        # When a new day starts, check if the new day is a trading day.
        # If it is a trading day, check marketOpenTime and marketCloseTime
        repeater3 = Event.ConceptEvent(TimeConcept.NEW_DAY, self._check_at_beginning_of_a_day)

        # 9:25 EST to run before_trading_start(context, data)
        repeater4 = Event.SingleEvent(9, 25, self.trader.before_trade_start_Function,
                                      passFunc=self._check_trading_day)  # 09:25 to run before_trading_start, a quantopian style function

        re.schedule_event(repeater1)
        re.schedule_event(repeater2)
        re.schedule_event(repeater3)
        re.schedule_event(repeater4)
        re.repeat()

    def _check_at_beginning_of_a_day(self, timeNow):
        self.log.debug(__name__ + '::_check_at_beginning_of_a_day')
        if not self.marketCalendar.trading_day(timeNow):  # do nothing if it is not a trading day
            self.tradingDay = False
            self._display_message('%s is not a trading day, but IBridgePy is running' % (str(timeNow.date()),))
        else:
            self.tradingDay = True
            self.todayMarketOpenTime, self.todayMarketCloseTime = self.marketCalendar.get_market_open_close_time(
                timeNow)
            if not self.todayMarketOpenTime <= timeNow < self.todayMarketCloseTime:
                self.log.debug(str(self.todayMarketOpenTime) + ' ' + str(self.todayMarketCloseTime))
                if self.runMode == MarketManagerRunMode.TRADING:
                    self._display_message('market=%s is closed now.' % (self.userConfig.marketName,))

    def _check_trading_day(self, timeNow):
        self.log.debug(__name__ + '::_check_trading_day: timeNow=%s' % (str(timeNow),))
        return self.tradingDay

    def _check_trading_hours(self, timeNow):
        self.log.debug(__name__ + '::_check_trading_hour: timeNow=%s' % (str(timeNow),))
        if not self.tradingDay:
            return False
        self.log.debug(str(self.todayMarketOpenTime) + ' ' + str(self.todayMarketCloseTime))
        self.log.debug(str(timeNow))
        return self.todayMarketOpenTime <= timeNow < self.todayMarketCloseTime

    def _display_message(self, message):
        if message != self.lastDisplayMessage:
            print('MarketManager::' + message)
            self.lastDisplayMessage = message

    def ingest_historical_data(self, loadingPlan):
        self.log.debug(__name__ + '::ingest_historical_data')
        self.trader.brokerService.brokerClient.dataProvider.ingest_hists(loadingPlan)


def setup_services(userConfig, trader=None):
    """
    stay here to avoid cyclic imports


    trader  <----> brokerService <-----> brokerClient ------> dataProvider
                                 -----> timeGenerator


    :param trader: passed in from configuration.txt because batch inputs
    :param userConfig:
    :return:
    """
    if userConfig.logLevel == LogLevel.DEBUG:
        print(__name__ + '::setup_services:userConfig id=%s trader id=%s' % (id(userConfig), id(trader)))

    userConfig.build()

    # Build a dataProvider instance
    userConfig.dataProvider = data_provider_factory.get_data_provider(userConfig)

    # Build a trader instance if it is not passed in
    if trader is not None:
        userConfig.trader = trader
    else:  # for testing
        from IBridgePy.TraderExtendedResources import Trader
        userConfig.trader = Trader

    userConfig.brokerClient = broker_client_factory.get_broker_client(userConfig)
    userConfig.brokerClient.dataProvider = userConfig.dataProvider

    # Make an instance and setup brokerService
    userConfig.brokerService = broker_factory.get_broker(userConfig)
    userConfig.brokerService.brokerClient = userConfig.brokerClient
    userConfig.timeGenerator = TimeGenerator(userConfig.timeGeneratorConfig)
    userConfig.brokerService.timeGenerator = userConfig.timeGenerator

    # set aTrader to brokerService and set brokerService to aTrader
    # so that they can call each other's functions, for example, Test_trader_single_account
    userConfig.trader.brokerService = userConfig.brokerService  # so that aTrader can call brokerService.reqMktData in TEST
    userConfig.brokerService.aTrader = userConfig.trader

    userConfig.brokerClient.brokerService = userConfig.brokerService

    # If getting hist from IB, dataProvider should have a dataProviderClient
    # For IB, brokerClient is used as dataProviderClient because IB is a dataProvider
    if userConfig.dataProviderName == DataProviderName.IB:
        userConfig.dataProviderClient = userConfig.brokerClient
        userConfig.dataProvider.dataProviderClient = userConfig.dataProviderClient
    # Random dataProvider and LocaFile dataProvider does not need dataProviderClient
    elif userConfig.dataProviderName in [DataProviderName.RANDOM, DataProviderName.LOCAL_FILE]:
        pass
    # For other data providers, need dataProviderClient
    else:
        print(__name__ + '::setup_services: EXIT, cannot handle dataProviderName=%s' % (userConfig.dataProviderName,))
        exit()

    if userConfig.logLevel == LogLevel.DEBUG:
        print(userConfig)
    return userConfig
