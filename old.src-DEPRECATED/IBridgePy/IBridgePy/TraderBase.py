import time
import pytz
import BasicPyLib.simpleLogger as simpleLogger
from IBridgePy.quantopian import QDataClass
from IBridgePy.trader_defs import Context
from IBridgePy.validator import Validator
from sys import exit


class Trader:
    # In backtester mode, run Trader::repeat_Function only when real time prices are available.
    # In live mode, always True. Set by broker_client_factory::RequestWrapper::processMessageWrapper
    runRepeatFunctionFlag = True

    # handle_data is not required anymore. This flag will only be used in backtest mode to decide if backtester
    # should run handle_data or not during the backtesting
    runHandleDataFlag = False

    # In run_like_quantopian mode, at the beginning of a day, run code to check if
    # scheduled_functions should run on that day. This is the flag. It will be saved for the whole day.
    runScheduledFunctionsToday = True

    # these two param are used in quantopian mode
    # For schedule function
    # They will be put in a value at the beginning of everyday
    # check_date_rules in MarketManagerBase.py
    monthDay = None
    weekDay = None

    # MarketMangerBase will monitor it to stop
    # False is want to run
    wantToEnd = False

    scheduledFunctionList = []  # record all of user scheduled function conditions

    # passed in broker, so that backtester can use broker's functions
    # set by IBridgePy::MarketManagerBase::setup_services
    brokerService = None

    # a list of accountCodes called back from IB server
    # user's input accountCode will be checked against this list
    accountCodeCallBackList = None

    # Validate user's inputs
    validator = Validator()

    def __init__(self, userConfig):
        self.userConfig = userConfig

        # in the run_like_quantopian mode
        # the system should use Easter timezone as the system time
        # self.sysTimeZone will be used for this purpose
        # schedule_function will use this to run schedules
        # Repeater will use this to run schedules as well
        self.sysTimeZone = pytz.timezone(self.userConfig.sysTimeZoneName)

        self.showTimeZone = pytz.timezone(self.userConfig.showTimeZoneName)

        # set up context and qData.data
        self.accountCode = self.userConfig.accountCode
        if userConfig.multiAccountFlag:
            self.accountCodeSet = set(self.accountCode)
        else:
            self.accountCodeSet = {self.accountCode}
        self.context = Context(self, self.accountCodeSet)
        self.qData = QDataClass(self)

        # userLog is for the function of record (). User will use it for any reason.
        dateTimeStr = time.strftime("%Y_%m_%d_%H_%M_%S")
        self.userLog = simpleLogger.SimpleLoggerClass(filename='userLog_' + dateTimeStr + '.txt', logLevel='NOTSET',
                                                      addTime=False)
        self.log = userConfig.log
        self.initialize_quantopian = userConfig.initialize_quantopian
        self.handle_data_quantopian = userConfig.handle_data_quantopian
        self.runHandleDataFlag = userConfig.runHandleDataFlag
        self.before_trading_start_quantopian = userConfig.before_trading_start_quantopian
        self.log.notset(__name__ + '::setup_trader')

    @property
    def versionNumber(self):
        return self.brokerService.versionNumber

    def getWantToEnd(self, dummyTimeNow=None):
        """
        The function is used in Repeater in MarketManagerBase.py to know if repeat should stop
        dummy input = because it can be program to stop based on an input datetime
        :return: bool
        """
        self.log.notset(__name__ + '::getWantToEnd: dummyTimeNow=%s' % (dummyTimeNow,))
        return self.wantToEnd

    def setWantToEnd(self):
        self.wantToEnd = True

    def adjust_accountCode(self, accountCode):
        if accountCode == 'default':
            if not self.userConfig.multiAccountFlag:
                return self.accountCode
            else:
                self.log.error(__name__ + '::adjust_accountCode: EXIT, Must specify an accountCode')
                exit()
        else:
            if not self.userConfig.multiAccountFlag:
                if accountCode in self.accountCodeSet:
                    return accountCode
                else:
                    self.log.error(
                        __name__ + '::adjust_accountCode: EXIT, wrong input accountCode=%s accountCodeSet=%s' % (
                        accountCode, str(self.accountCodeSet)))
                    exit()
            else:
                if accountCode in self.accountCodeSet:
                    return accountCode
                else:
                    self.log.error(
                        __name__ + '::adjust_accountCode: EXIT, wrong input accountCode=%s, not in Multi account codes' % (
                            accountCode,))
                    exit()

    def get_portfolio(self, accountCode):
        adj_accountCode = self.adjust_accountCode(accountCode)
        return self.context.portfolioQ[adj_accountCode]

    def connect(self):
        self.brokerService.connect()

    def disconnect(self):
        self.brokerService.disconnect()

    def get_next_time(self):
        return self.brokerService.get_next_time().astimezone(self.sysTimeZone)
