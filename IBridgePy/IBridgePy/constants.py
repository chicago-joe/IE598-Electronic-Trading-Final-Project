# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 23:50:16 2018

@author: IBridgePy@gmail.com
"""
from sys import exit
from BasicPyLib.simpleLogger import SimpleLoggerClass
import time
import datetime as dt


class CONSTANTS:
    def __init__(self):
        pass

    def get(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            print(__name__, '::CONSTANTS: key=%s does not exist' % (key,))
            exit()


class SecType(CONSTANTS):
    CASH = 'CASH'
    STK = 'STK'
    FUT = 'FUT'
    OPT = 'OPT'
    IND = 'IND'
    CFD = 'CFD'
    BOND = 'BOND'


class LiveBacktest(CONSTANTS):
    LIVE = 1
    BACKTEST = 2


class BrokerName(CONSTANTS):
    LOCAL_BROKER = 'LocalBroker'
    IB = 'InteractiveBrokers'


class DataProviderName(CONSTANTS):
    LOCAL_FILE = 'LocalFile'
    RANDOM = 'Random'
    IB = 'InteractiveBrokers'


class DataSourceName(CONSTANTS):
    IB = 'InteractiveBrokers'
    YAHOO = 'yahoo'
    GOOGLE = 'google'
    LOCAL_FILE = 'LocalFile'


class SymbolStatus(CONSTANTS):
    DEFAULT = 0
    SUPER_SYMBOL = 1
    ADJUSTED = 2
    STRING_CONVERTED = 3


class RunMode(CONSTANTS):
    REGULAR = 'regular'
    RUN_LIKE_QUANTOPIAN = 'run_like_quantopian'
    SUDO_RUN_LIKE_QUANTOPIAN = 'sudo_run_like_quantopian'
    LIVE = [REGULAR, RUN_LIKE_QUANTOPIAN, SUDO_RUN_LIKE_QUANTOPIAN]
    BACK_TEST = 'back_test'


class OrderStatus(CONSTANTS):
    PRESUBMITTED = 'PreSubmitted'
    SUBMITTED = 'Submitted'
    CANCELLED = 'Cancelled'
    APIPENDING = 'ApiPending'
    PENDINGSUBMIT = 'PendingSubmit'
    PENDINGCANCEL = 'PendingCancel'
    FILLED = 'Filled'
    INACTIVE = 'Inactive'


class OrderType(CONSTANTS):
    MKT = 'MKT'
    LMT = 'LMT'
    STP = 'STP'
    TRAIL_LIMIT = 'TRAIL LIMIT'
    TRAIL = 'TRAIL'


class ReqHistParam(CONSTANTS):
    class Name(CONSTANTS):
        BAR_SIZE = 'barSize'
        GO_BACK = 'goBack'
        END_TIME = 'endTime'

    class BarSize(CONSTANTS):
        ONE_MIN = '1 min'
        ONE_DAY = '1 day'

    class GoBack(CONSTANTS):
        ONE_DAY = '1 D'
        FIVE_DAYS = '5 D'

    class FormatDate(CONSTANTS):
        DATE_TIME = 1
        UTC_SECOND = 2

    class UseRTH(CONSTANTS):
        DATA_IN_REGULAR_HOURS = 1
        ALL_DATA = 0


class ExchangeName(CONSTANTS):
    ISLAND = 'ISLAND'


class MarketName(CONSTANTS):
    NYSE = 'NYSE'
    NONSTOP = 'Fake'


class Default(CONSTANTS):
    DEFAULT = 'default'


class FollowUpRequest(CONSTANTS):
    DO_NOT_FOLLOW_UP = False
    FOLLOW_UP = True


class RequestDataParam(CONSTANTS):
    WAIT_30_SECONDS = 30
    WAIT_1_SECOND = 1
    DO_NOT_REPEAT = 0


class LogLevel(CONSTANTS):
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    NOTSET = 'NOTSET'


class TimeGeneratorType(CONSTANTS):
    LIVE = 'LIVE'
    AUTO = 'AUTO'
    CUSTOM = 'CUSTOM'


class TimeGeneratorConfig:
    def __init__(self, timeGeneratorType, startingTime=None, endingTime=None, freq=None, custom=[]):
        self.timeGeneratorType = timeGeneratorType  # Live, Auto, Custom
        self.startingTime = startingTime
        self.endingTime = endingTime
        self.freq = freq
        self.custom = custom


class MarketManagerRunMode(CONSTANTS):
    TRADING = 'Trading'
    INGESTING = 'Ingesting'


class TimeConcept(CONSTANTS):
    NEW_DAY = 'new_day'
    NEW_HOUR = 'new_hour'


class MarketManagerConfig:
    def __init__(self, runMode=MarketManagerRunMode.TRADING):
        self.runMode = runMode


class RunningConfig:
    def __init__(self,
                 rootFolderPath='empty',
                 fileName='',
                 accountCode='testAccountCode',
                 liveOrBacktest=LiveBacktest.LIVE,
                 brokerName=BrokerName.IB,
                 dataProviderName=DataProviderName.IB,
                 repBarFreq=1,
                 marketName=MarketName.NYSE,
                 logLevel=LogLevel.INFO,
                 clientId=9,
                 runScheduledFunctionBeforeHandleData=False,
                 host='',
                 port=7496,
                 runMode=RunMode.REGULAR,
                 showTimeZoneName='US/Eastern',
                 sysTimeZoneName='US/Eastern',
                 timeGeneratorConfig=TimeGeneratorConfig(TimeGeneratorType.LIVE),
                 marketManager_runMode=MarketManagerRunMode.TRADING
                 ):
        """

        :param liveOrBacktest: 1= Live 2=Backtest
        """
        self.rootFolderPath = rootFolderPath
        self.fileName = fileName
        self.accountCode = accountCode
        self.liveOrBacktest = liveOrBacktest
        self.brokerName = brokerName
        self.dataProviderName = dataProviderName
        self.repBarFreq = repBarFreq
        self.marketName = marketName
        self.clientId = clientId
        self.runScheduledFunctionBeforeHandleData = runScheduledFunctionBeforeHandleData
        self.host = host
        self.port = port
        self.runMode = runMode
        self.showTimeZoneName = showTimeZoneName  # used in TraderBase.py
        self.sysTimeZoneName = sysTimeZoneName  # used in TraderBase.py
        self.logLevel = logLevel
        self.log = None
        self.brokerService = None
        self.brokerClient = None
        self.dataProvider = None
        self.dataProviderClient = None
        self.trader = None
        self.initialize_quantopian = None
        self.handle_data_quantopian = None  # it is better off to check it in TraderBase::__init__
        self.before_trading_start_quantopian = None  # it is better off to check it in TraderBase::__init__
        self.timeGenerator = None
        self.timeGeneratorConfig = timeGeneratorConfig
        self.multiAccountFlag = False
        self.runHandleDataFlag = None  # it is used in MarketManagerBase.py to decide if run handle_data

        self.marketManagerConfig = MarketManagerConfig()
        self.marketManagerConfig.runMode = marketManager_runMode

    def __str__(self):
        ans = ''''''
        for ct in self.__dict__:
            ans += ct + '=' + str(self.__dict__[ct]) + '\n'
        return ans

    def build(self):
        sysLogFileName = 'TraderLog_' + time.strftime("%Y-%m-%d") + '.txt'
        self.log = SimpleLoggerClass(sysLogFileName, self.logLevel)
        if isinstance(self.accountCode, list) or isinstance(self.accountCode, set) or isinstance(self.accountCode,
                                                                                                 tuple):
            self.multiAccountFlag = True
        else:
            self.multiAccountFlag = False

        if self.handle_data_quantopian is None:
            self.handle_data_quantopian = (lambda x, y: None)
            self.runHandleDataFlag = False
        else:
            self.runHandleDataFlag = True

        if self.before_trading_start_quantopian is None:
            self.before_trading_start_quantopian = (lambda x, y: None)


class UserConfig(CONSTANTS):
    REGULAR = RunningConfig()
    RUN_LIKE_QUANTOPIAN = RunningConfig(repBarFreq=60,
                                        runMode=RunMode.RUN_LIKE_QUANTOPIAN)
    SUDO_RUN_LIKE_QUANTOPIAN = RunningConfig(repBarFreq=60,
                                             runMode=RunMode.SUDO_RUN_LIKE_QUANTOPIAN,
                                             marketName=MarketName.NONSTOP)
    BACKTEST_RANDOM = RunningConfig(liveOrBacktest=2,
                                    repBarFreq=60,
                                    runMode=RunMode.RUN_LIKE_QUANTOPIAN,
                                    brokerName=BrokerName.LOCAL_BROKER,
                                    dataProviderName=DataProviderName.RANDOM,
                                    timeGeneratorConfig=TimeGeneratorConfig(TimeGeneratorType.LIVE))
    BACKTEST_CUSTOM_TIME_GENERATOR = RunningConfig(liveOrBacktest=2,
                                                   repBarFreq=60,
                                                   runMode=RunMode.REGULAR,
                                                   brokerName=BrokerName.LOCAL_BROKER,
                                                   dataProviderName=DataProviderName.RANDOM,
                                                   timeGeneratorConfig=TimeGeneratorConfig(TimeGeneratorType.CUSTOM))
    BACKTEST_AUTO_TIME_GENERATOR = RunningConfig(liveOrBacktest=2,
                                                 repBarFreq=60,
                                                 runMode=RunMode.RUN_LIKE_QUANTOPIAN,
                                                 brokerName=BrokerName.LOCAL_BROKER,
                                                 dataProviderName=DataProviderName.RANDOM,
                                                 timeGeneratorConfig=TimeGeneratorConfig(TimeGeneratorType.AUTO))
    BACKTEST_LOCAL_FILE = RunningConfig(liveOrBacktest=2,
                                        repBarFreq=60,
                                        runMode=RunMode.RUN_LIKE_QUANTOPIAN,
                                        brokerName=BrokerName.LOCAL_BROKER,
                                        dataProviderName=DataProviderName.LOCAL_FILE,
                                        timeGeneratorConfig=TimeGeneratorConfig(TimeGeneratorType.CUSTOM))
    BACKTEST_IB = RunningConfig(liveOrBacktest=2,
                                repBarFreq=60,
                                runMode=RunMode.RUN_LIKE_QUANTOPIAN,
                                brokerName=BrokerName.LOCAL_BROKER,
                                dataProviderName=DataProviderName.IB,
                                timeGeneratorConfig=TimeGeneratorConfig(TimeGeneratorType.AUTO))
