from IBridgePy.TraderBase import Trader
from sys import exit
from IBridgePy.constants import RequestDataParam, OrderStatus, FollowUpRequest, SecType
from IBridgePy.quantopian import ReqData, TimeBasedRules, calendars, MarketOrder, LimitOrder, StopOrder, \
    from_contract_to_security
from IBridgePy.IbridgepyTools import special_match, create_order, check_same_security, from_symbol_to_security
from IBridgePy import IBCpp
import datetime as dt
import pytz
from IBridgePy.validator import ShowRealTimePriceValidator

# https://www.interactivebrokers.com/en/software/api/apiguide/tables/tick_types.htm
TICK_TYPE_MAPPER = {
    'ask_price': IBCpp.TickType.ASK,
    'bid_price': IBCpp.TickType.BID,
    'last_price': IBCpp.TickType.LAST,
    'price': IBCpp.TickType.LAST,
    'open': IBCpp.TickType.OPEN,
    'high': IBCpp.TickType.HIGH,
    'low': IBCpp.TickType.LOW,
    'close': IBCpp.TickType.CLOSE,
    'volume': IBCpp.TickType.VOLUME,
    'ask_size': IBCpp.TickType.ASK_SIZE,
    'bid_size': IBCpp.TickType.BID_SIZE,
    'last_size': IBCpp.TickType.LAST_SIZE,
    'ask_option_computation': IBCpp.TickType.ASK_OPTION_COMPUTATION,
    'bid_option_computation': IBCpp.TickType.BID_OPTION_COMPUTATION,
    'last_option_computation': IBCpp.TickType.LAST_OPTION_COMPUTATION,
    'model_option': IBCpp.TickType.MODEL_OPTION
}


class TraderBasicResources(Trader):
    def processMessages(self, timeNow):
        """
        this function is created to fit the new RepeaterEngine because any functions to be scheduled must have two input
        times. It is easier to input two times to repeated function(?)
        :param timeNow:
        :return:
        """
        self.log.debug(__name__ + '::process_messages: timeNow=%s' % (str(timeNow),))
        self.runRepeatFunctionFlag = self.brokerService.processMessages(timeNow)

    def _validate_input_accountCode(self, accountCode):
        self.log.debug(__name__ + '::_validate_input_accountCode: accountCode=%s' % (accountCode,))
        if accountCode in self.accountCodeCallBackList:
            return
        else:
            self.log.error(__name__ + '::initialize_Function: EXIT, accountCode=%s is not acceptable' % (accountCode,))
            self.log.error(
                __name__ + '::initialize_Function: possible accountCodes are %s' % (str(self.accountCodeCallBackList),))
            exit()

    def get_datetime(self, timezoneName='default'):
        """
        function to get the current datetime of IB system similar to that
        defined in Quantopian
        timezone: str 'US/Pacific'
        """
        self.log.debug(__name__ + '::get_datetime: timezoneName=%s' % (timezoneName,))
        timeNow = self.brokerService.get_datetime()
        if timezoneName == 'default':
            return timeNow.astimezone(self.showTimeZone)
        else:
            return timeNow.astimezone(pytz.timezone(timezoneName))

    def initialize_Function(self):
        self.log.debug(__name__ + '::initialize_Function')
        self.log.info('IBridgePy version %s' % (self.versionNumber,))
        self.log.info('fileName = %s' % (self.userConfig.fileName,))

        self.brokerService.request_data(RequestDataParam.WAIT_30_SECONDS, RequestDataParam.DO_NOT_REPEAT,
                                        ReqData.reqIds())
        self.brokerService.request_data(RequestDataParam.WAIT_30_SECONDS, RequestDataParam.DO_NOT_REPEAT,
                                        ReqData.reqCurrentTime())
        if self.userConfig.multiAccountFlag:
            self.brokerService.request_data(RequestDataParam.WAIT_30_SECONDS, RequestDataParam.DO_NOT_REPEAT,
                                            ReqData.reqAccountSummary(),
                                            ReqData.reqAllOpenOrders(),
                                            ReqData.reqPositions())
        else:
            self.brokerService.request_data(RequestDataParam.WAIT_30_SECONDS, RequestDataParam.DO_NOT_REPEAT,
                                            ReqData.reqAccountUpdates(True, self.accountCode),
                                            ReqData.reqAllOpenOrders(),
                                            ReqData.reqPositions())

        self.accountCodeCallBackList = self.brokerService.get_active_accountCodes()

        self.log.debug(__name__ + '::initialize_Function::start to run customers init function')
        self.initialize_quantopian(self.context)  # function name was passed in.

        self.log.info('####    Starting to initialize trader    ####')
        if self.userConfig.multiAccountFlag:
            for acctCode in self.accountCodeSet:
                self._validate_input_accountCode(acctCode)
                self.display_all(acctCode)
        else:
            self._validate_input_accountCode(self.accountCode)
            self.display_all()

        # to debug schedule_function()
        # print(__name__)
        # for ct in self.scheduledFunctionList:
        #    print(ct)

        self.log.info('####    Initialize trader COMPLETED    ####')

    def repeat_Function(self, dummyTime):
        self.log.debug(__name__ + '::repeat_Function: dummyTime=%s' % (str(dummyTime),))

        # In backtest mode, if real time prices are not available, do not run repeat_Function
        # In live mode, always run repeat_function
        if not self.runRepeatFunctionFlag:
            return
        # TODO: it is better off to set self.runScheduledFunctionsToday every day to save time for simulation
        if self.runScheduledFunctionsToday:
            if self.userConfig.runScheduledFunctionBeforeHandleData:
                self._check_schedules()

        self.handle_data_quantopian(self.context, self.qData)

        if self.runScheduledFunctionsToday:
            if not self.userConfig.runScheduledFunctionBeforeHandleData:
                self._check_schedules()

    def before_trade_start_Function(self, dummyTime):
        self.log.debug(__name__ + '::before_trade_start_Function: dummyTime=%s' % (str(dummyTime),))
        self.before_trading_start_quantopian(self.context, self.qData)

    def display_positions(self, accountCode='default'):
        self.log.notset(__name__ + '::display_positions: accountCode=%s' % (accountCode,))
        adj_accountCode = self.adjust_accountCode(accountCode)
        positions = self.get_all_positions(adj_accountCode)  # return a dictionary

        if len(positions) == 0:
            self.log.info('##    NO ANY POSITION    ##')
        else:
            self.log.info('##    POSITIONS %s   ##' % (adj_accountCode,))
            self.log.info('Symbol Amount Cost_basis')

            for security in positions:
                a = positions[security].str_security
                b = positions[security].amount
                c = positions[security].cost_basis
                self.log.info(str(a) + ' ' + str(b) + ' ' + str(c))

    def display_orderStatus(self, accountCode='default'):
        self.log.notset(__name__ + '::display_orderStatus: accountCode=%s' % (accountCode,))
        adj_accountCode = self.adjust_accountCode(accountCode)
        orders = self.brokerService.get_all_orders(adj_accountCode)

        if len(orders) >= 1:
            self.log.info('##    Order Status %s   ##' % (adj_accountCode,))
            for orderId in orders:
                self.log.info(str(orders[orderId]))
            self.log.info('##    END    ##')
        else:
            self.log.info('##    NO any order    ##')

    def display_account_info(self, accountCode='default'):
        """
        display account info such as position values in format ways
        """
        self.log.notset(__name__ + '::display_account_info: accountCode=%s' % (accountCode,))
        self.log.info('##    ACCOUNT Balance  %s  ##' % (self.adjust_accountCode(accountCode),))
        a = self.get_portfolio(accountCode).cash
        b = self.get_portfolio(accountCode).portfolio_value
        c = self.get_portfolio(accountCode).positions_value
        self.log.info('CASH=%s' % (str(a),))
        self.log.info('portfolio_value=%s' % (str(b),))
        self.log.info('positions_value=%s' % (str(c),))

        if a + b + c <= 0.0:
            self.log.error(__name__ + '::display_account_info: EXIT, Wrong input accountCode = %s'
                           % (self.accountCode,))
            # self.accountCodeCallBackSet.discard(self.accountCode)
            # self.accountCodeCallBackSet.discard('default')
            # if len(self.accountCodeCallBackSet):
            #     self.log.error(__name__ + '::display_account_info: Possible accountCode = %s'
            #                    % (' '.join(self.accountCodeCallBackSet)))
            exit()

    def display_all(self, accountCode='default'):
        self.log.notset(__name__ + '::display_all: accountCode=%s' % (accountCode,))
        accountCode = self.adjust_accountCode(accountCode)
        self.display_account_info(accountCode)
        self.display_positions(accountCode)
        self.display_orderStatus(accountCode)

    def show_account_info(self, field, accountCode='default'):
        adj_accountCode = self.adjust_accountCode(accountCode)
        portfolio = self.get_portfolio(adj_accountCode)
        if hasattr(portfolio, field):
            return getattr(portfolio, field)
        else:
            self.log.error(__name__ + '::show_account_info: EXIT, field=%s is not accessible' % (field,))
            exit()

    def hold_any_position(self, accountCode='default'):
        self.log.debug(__name__ + '::hold_any_position')
        adj_accountCode = self.adjust_accountCode(accountCode)
        return self.brokerService.hold_any_position(adj_accountCode)

    def request_historical_data(self, security, barSize, goBack, endTime='', whatToShow='', useRTH=1, formatDate=1):
        # The format in which the incoming bars' date should be presented. Note that for day bars, only yyyyMMdd format is available.
        return self.brokerService.get_historical_data(security, barSize, goBack, endTime, whatToShow, useRTH,
                                                      formatDate)

    def show_real_time_price(self, security, param):
        self.log.notset(__name__ + '::show_real_time_price: security=%s param=%s' % (str(security), str(param)))
        adj_param = TICK_TYPE_MAPPER[param]
        self.validator.showRealTimePriceValidator.validate(security, adj_param)
        return self.brokerService.get_real_time_price(security, adj_param)

    def show_real_time_size(self, security, param):
        self.log.notset(__name__ + '::show_real_time_price: security=%s param=%s' % (str(security), str(param)))
        return self.brokerService.get_real_time_size(security, TICK_TYPE_MAPPER[param])

    def cancel_order(self, order):
        """
        function to cancel orders
        """
        if isinstance(order, int):
            self.log.debug(__name__ + '::cancel_order: orderId=%s' % (order,))
            self.brokerService.cancel_order(order)
        else:
            self.log.debug(__name__ + '::cancel_order: orderId=%s' % (order.orderId,))
            self.brokerService.cancel_order(order.orderId)

    def order(self, security, amount, style=MarketOrder(), orderRef='',
              accountCode='default', outsideRth=False, hidden=False):
        self.log.debug(__name__ + '''::order: security=%s amount=%s style=%s orderRef=%s accountCode=%s
         outsideRth=%s hidden=%s''' % (str(security), str(amount), str(style), str(orderRef), str(accountCode),
                                       str(outsideRth), str(hidden)))
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderId = self.brokerService.use_next_id()
        ibridgePyOrder = create_order(orderId, adj_accountCode, security, amount, style, self.get_datetime(),
                                      orderRef=orderRef,
                                      outsideRth=outsideRth, hidden=hidden)
        return self.brokerService.place_order(ibridgePyOrder)

    def modify_order(self, orderId, newQuantity=None, newLimitPrice=None, newStopPrice=None, newTif=None,
                     newOrderRef=None):
        self.log.debug(__name__ + '::modify_order: orderId = %s' % (orderId,))
        currentOrder = self.brokerService.get_order(orderId)
        if currentOrder.status in [OrderStatus.PRESUBMITTED, OrderStatus.SUBMITTED]:
            if newQuantity is not None:
                currentOrder.order.totalQuantity = newQuantity
            if newLimitPrice is not None:
                currentOrder.order.lmtPrice = newLimitPrice
            if newStopPrice is not None:
                currentOrder.order.auxPrice = newStopPrice
            if newTif is not None:
                currentOrder.order.tif = newTif
            if newOrderRef is not None:
                currentOrder.order.orderRef = newOrderRef
            self.brokerService.request_data(RequestDataParam.WAIT_30_SECONDS, RequestDataParam.DO_NOT_REPEAT,
                                            ReqData.placeOrder(orderId, currentOrder.contract, currentOrder.order,
                                                               FollowUpRequest.DO_NOT_FOLLOW_UP))
        else:
            self.log.error(__name__ + '::modify_order: Cannot modify order. orderId = %s' % (orderId,))
            exit()

    def get_order_status(self, orderId):
        """
        orderId is unique for any orders in any session
        """
        return self.brokerService.get_order_status(orderId)

    def order_status_monitor(self, orderId, target_status, waitingTimeInSeconds=30):
        """

        :param orderId: int
        :param target_status: either str or list[str]
        :param waitingTimeInSeconds: int
        :return:
        """
        self.log.notset(__name__ + '::order_status_monitor: orderId=%s target_status=%s' % (orderId, target_status))
        if orderId < 0:
            self.log.error(__name__ + '::order_status_monitor: EXIT, orderId=%s Must >= 0' % (orderId,))
            exit()
        elif orderId == 0:
            return True
        return self.brokerService.order_status_monitor(orderId, target_status, waitingTimeInSeconds)

    def get_order(self, orderId):
        """
        tested at integ_test_cancel_all_order.py
        :param orderId:
        :return: broker_factory::records_def::IbridgePyOrder
        """
        self.log.debug(__name__ + '::get_order: orderId = %s' % (orderId,))
        return self.brokerService.get_order(orderId)

    def get_open_orders(self, security=None, accountCode='default'):
        """

        :param security: IBridgePy::quantopian::Security
        :param accountCode: string
        :return: dictionary keyed=orderId value=broker_factory::records::IbridgePyOrder
        """
        self.log.debug(__name__ + '::get_open_orders')
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderIdList = self.brokerService.get_all_open_orders_orderIds(adj_accountCode)

        if security is None:
            ans = {}
            for orderId in orderIdList:
                contract = self.brokerService.get_order_info(orderId, 'contract')
                security = from_contract_to_security(contract)
                if security not in ans:
                    ans[security] = []
                ans[security].append(self.get_order(orderId))
        else:
            ans = []
            for orderId in orderIdList:
                contract = self.brokerService.get_order_info(orderId, 'contract')
                if check_same_security(from_contract_to_security(contract), security):
                    ans.append(self.get_order(orderId))
        return ans

    def get_all_orders(self, accountCode='default'):
        self.log.debug(__name__ + '::get_all_orders')
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderIdList = self.brokerService.get_all_orders(adj_accountCode)
        ans = {}
        for orderId in orderIdList:
            ans[orderId] = self.get_order(orderId)
        return ans

    def get_all_positions(self, accountCode='default'):
        """

        :param accountCode: string
        :return: dictionary, keyed by Security object, value = PositionRecord
        """
        self.log.debug(__name__ + '::get_all_positions')
        adj_accountCode = self.adjust_accountCode(accountCode)
        allPositions = self.brokerService.get_all_positions(adj_accountCode)
        ans = {}
        for str_security in allPositions:
            contract = allPositions[str_security].contract
            security = from_contract_to_security(contract)
            adj_security = self.brokerService.add_exchange_primaryExchange_to_security(security)
            ans[adj_security] = allPositions[str_security]
            # ans[security] = allPositions[str_security]
        return ans

    def get_position(self, security, accountCode='default'):
        """

        :param security:
        :param accountCode:
        :return: broker_factory::records_def::PositionRecord
        """
        self.log.debug(__name__ + '::get_position: security=%s' % (str(security),))
        adj_accountCode = self.adjust_accountCode(accountCode)
        return self.brokerService.get_position(adj_accountCode, security)

    def _check_schedules(self):
        self.log.debug(__name__ + '::_check_schedules')
        timeNow = self.get_datetime().astimezone(self.sysTimeZone)
        # ct is an instance of class TimeBasedRules in quantopian.py
        for ct in self.scheduledFunctionList:
            if special_match(ct.onHour, timeNow.hour, 'hourMinute') and \
                    special_match(ct.onMinute, timeNow.minute, 'hourMinute') and \
                    special_match(ct.onNthMonthDay, self.monthDay, 'monthWeek') and \
                    special_match(ct.onNthWeekDay, self.weekDay, 'monthWeek'):
                ct.func(self.context, self.qData)

    def schedule_function(self,
                          func,
                          date_rule=None,
                          time_rule=None,
                          calendar=calendars.US_EQUITIES):
        """
        ONLY time_rule.spot_time depends on
        :param func: the function to be run at sometime
        :param date_rule: IBridgePy::quantopian::date_rule
        :param time_rule: BridgePy::quantopian::time_rule
        :param calendar: TODO this is NOT the real marketCalendar
        :return: self.scheduledFunctionList
        """

        global onHour, onMinute
        self.log.debug(__name__ + '::schedule_function')
        if time_rule is None:
            onHour = 'any'  # every number can match, run every hour
            onMinute = 'any'  # every number can match, run every minute
        else:
            # if there is a time_rule, calculate onHour and onMinute based on market times
            marketOpenHour, marketOpenMinute, marketCloseHour, marketCloseMinute = calendar
            # print (marketOpenHour,marketOpenMinute,marketCloseHour,marketCloseMinute)
            marketOpen = marketOpenHour * 60 + marketOpenMinute
            marketClose = marketCloseHour * 60 + marketCloseMinute
            if time_rule.version == 'market_open' or time_rule.version == 'market_close':
                if time_rule.version == 'market_open':
                    tmp = marketOpen + time_rule.hour * 60 + time_rule.minute
                else:
                    tmp = marketClose - time_rule.hour * 60 - time_rule.minute
                while tmp < 0:
                    tmp += 24 * 60
                startTime = tmp % (24 * 60)
                onHour = int(startTime / 60)
                onMinute = int(startTime % 60)
            elif time_rule.version == 'spot_time':
                onHour = time_rule.hour
                onMinute = time_rule.minute
            else:
                self.log.error(
                    __name__ + '::schedule_function: EXIT, cannot handle time_rule.version=%s' % (time_rule.version,))
                exit()

        if date_rule is None:
            # the default rule is None, means run every_day
            tmp = TimeBasedRules(onHour=onHour, onMinute=onMinute, func=func)
            self.scheduledFunctionList.append(tmp)
            return
        else:
            if date_rule.version == 'every_day':
                tmp = TimeBasedRules(onHour=onHour, onMinute=onMinute, func=func)
                self.scheduledFunctionList.append(tmp)
                return
            else:
                if date_rule.version == 'week_start':
                    onNthWeekDay = date_rule.weekDay
                    tmp = TimeBasedRules(onNthWeekDay=onNthWeekDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return
                elif date_rule.version == 'week_end':
                    onNthWeekDay = -date_rule.weekDay - 1
                    tmp = TimeBasedRules(onNthWeekDay=onNthWeekDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return
                if date_rule.version == 'month_start':
                    onNthMonthDay = date_rule.monthDay
                    tmp = TimeBasedRules(onNthMonthDay=onNthMonthDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return
                elif date_rule.version == 'month_end':
                    onNthMonthDay = -date_rule.monthDay - 1
                    tmp = TimeBasedRules(onNthMonthDay=onNthMonthDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return

    def symbol(self, str_security):
        """
        Stay here because it uses self.add_exchange_primaryExchange_to_security that can be extended easily.
        for example, get primaryExchange and exchange from IB server instead of by security_info.csv
        :param str_security:
        :return:
        """
        security = from_symbol_to_security(str_security)
        return self.brokerService.add_exchange_primaryExchange_to_security(security)

    def symbols(self, *args):
        ans = []
        for item in args:
            ans.append(self.symbol(item))
        return ans
