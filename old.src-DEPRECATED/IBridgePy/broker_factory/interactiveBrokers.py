# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from broker_factory.broker import Broker
from broker_factory.records_def import print_contract
from IBridgePy import IBCpp
from IBridgePy.quantopian import ReqData
from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_security, \
    add_exchange_primaryExchange_to_security
import time
from IBridgePy.constants import OrderStatus, LiveBacktest
import datetime as dt
import pytz
from sys import exit

# https://www.interactivebrokers.com/en/software/api/apiguide/tables/tick_types.htm
TICK_TYPE_MAPPER = {
    'ask_price': IBCpp.TickType.ASK,
    'bid_price': IBCpp.TickType.BID,
    'last_price': IBCpp.TickType.LAST,
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


def validate_not_equal_none(funName, val, infoTuple):
    if val is None:
        print(funName, infoTuple, 'should not equal to None')
        exit()


class InteractiveBrokers(Broker):
    @property
    def name(self):
        return "InteractiveBrokers"

    def add_exchange_primaryExchange_to_security(self, security):
        """
        This function stays here because it is specific to brokers.
        The solution can be local file, security_info.csv or get from IB server directly
        :param security:
        :return: adjusted security with correct exchange and primaryExchange
        """
        return add_exchange_primaryExchange_to_security(security)

    def get_active_accountCodes(self):
        """
        get a list of accountCodes from IB server to check if the user input accountCode is acceptable.
        :return:
        """
        self.log.debug(__name__ + '::get_active_accountCodes')
        return self.traderAccountSummaryRecords.get_all_active_accountCodes() + self.traderAccountValueRecords.get_all_active_accountCodes()

    def get_datetime(self):
        """
        Get IB server time
        :return: datetime in UTC timezone
        """
        self.log.debug(__name__ + '::get_datetime')
        if self.userConfig.liveOrBacktest == LiveBacktest.LIVE:
            return self.timeGenerator.get_next_time() + self.brokerClient.localServerTimeDiff
        else:
            return self.timeGenerator.get_current_time() + self.brokerClient.localServerTimeDiff

    def get_real_time_price(self, security, tickType):  # return real time price
        self.log.debug(__name__ + '::get_real_time_price: security=%s tickType=%s' % (str(security), str(tickType)))

        # if the request of real time price is not already submitted
        # do it right now
        # request_data guarantee valid ask_price and valid bid_price
        if not self.brokerClient.check_if_real_time_price_requested(security):
            self.request_data(10, 0, ReqData.reqMktData(security, followUp=True))

        if isinstance(tickType, int):
            return self.traderTickPriceRecords.getPrice(security, tickType)
        else:
            return self.traderTickPriceRecords.getPrice(security, TICK_TYPE_MAPPER[tickType])

    def get_real_time_size(self, security, tickType):  # return real time price
        self.log.debug(__name__ + '::get_real_time_size: security=%s tickType=%s' % (str(security), str(tickType)))

        # if the request of real time price is not already submitted
        # do it right now
        # request_data guarantee valid ask_price and valid bid_price
        # DO NOT guarantee valid size
        if not self.brokerClient.check_if_real_time_price_requested(security):
            self.request_data(10, 0, ReqData.reqMktData(security, followUp=True))

        if isinstance(tickType, int):
            return self.traderTickSizeRecords.getSize(security, tickType)
        else:
            return self.traderTickSizeRecords.getSize(security, TICK_TYPE_MAPPER[tickType])

    def get_historical_data(self, security, barSize, goBack, endTime='', whatToShow='', useRTH=1, formatDate=2):
        """

        :param security: Security
        :param barSize: string
        :param goBack: string
        :param endTime: datetime
        :param whatToShow: string
        :param useRTH: int
        :param formatDate: int
        :return: a dataFrame, keyed by a datetime with timezone UTC, colums = ['open', 'high', 'low', 'close', 'volume']
                The latest time record at the bottom of the dateFrame.
        """
        # barSize can be any of the following values(string)
        # 1 sec, 5 secs,15 secs,30 secs,1 min,2 mins,3 mins,5 mins,
        # 15 mins,30 mins,1 hour,1 day

        # whatToShow: see IB documentation for choices
        # TRADES,MIDPOINT,BID,ASK,BID_ASK,HISTORICAL_VOLATILITY,
        # OPTION_IMPLIED_VOLATILITY

        # all request datetime MUST be switched to UTC then submit to IB
        if endTime != '':
            if endTime.tzinfo is None:
                self.log.error(__name__ + '::request_historical_data: EXIT, endTime=%s must have timezone' % (endTime,))
                exit()
            endTime = endTime.astimezone(tz=pytz.utc)
            endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
        if whatToShow == '':
            if security.secType in ['STK', 'FUT', 'IND', 'BOND']:
                whatToShow = 'TRADES'
            elif security.secType in ['CASH', 'OPT', 'CFD', 'CONTFUT']:
                whatToShow = 'ASK'
            else:
                self.log.error(
                    __name__ + '::request_historical_data: EXIT, cannot handle security.secType=' + security.secType)
                exit()
        orderIdList = self.request_data(30, 0,
                                        ReqData.reqHistoricalData(security, barSize, goBack, endTime, whatToShow,
                                                                  useRTH, formatDate))
        return self.brokerClient.requestResults[orderIdList[0]]  # return a pandas dataFrame

    def get_scanner_results(self, kwargs):
        #        numberOfRows=-1, instrument='', locationCode='', scanCode='', abovePrice=0.0,
        #        belowPrice=0.0, aboveVolume=0, marketCapAbove=0.0, marketCapBelow=0.0, moodyRatingAbove='',
        #        moodyRatingBelow='', spRatingAbove='', spRatingBelow='', maturityDateAbove='', maturityDateBelow='',
        #        couponRateAbove=0.0, couponRateBelow=0.0, excludeConvertible=0, averageOptionVolumeAbove=0,
        #        scannerSettingPairs='', stockTypeFilter=''
        tagList = ['numberOfRows', 'instrument', 'locationCode', 'scanCode', 'abovePrice', 'belowPrice', 'aboveVolume',
                   'marketCapAbove',
                   'marketCapBelow', 'moodyRatingAbove', 'moodyRatingBelow', 'spRatingAbove', 'spRatingBelow',
                   'maturityDateAbove',
                   'maturityDateBelow', 'couponRateAbove', 'couponRateBelow', 'excludeConvertible',
                   'averageOptionVolumeAbove',
                   'scannerSettingPairs', 'stockTypeFilter']
        subscription = IBCpp.ScannerSubscription()
        for ct in kwargs:
            if ct in tagList:
                setattr(subscription, ct, kwargs[ct])
        orderIdList = self.brokerClient.request_data(30, 0, ReqData.reqScannerSubscription(subscription))
        reqId = orderIdList[0]
        result = self.brokerClient.requestResults[reqId].copy()
        self.brokerClient.request_data(30, 0, ReqData.cancelScannerSubscription(reqId))
        return result

    def get_option_greeks(self, security, tickType, fields):
        self.log.debug(__name__ + '::get_option_greeks security=%s tickType=%s fields=%s'
                       % (security.full_print(), str(tickType), str(fields)))
        ans = {}
        for field in fields:
            ans[field] = self.traderTickOptionComputationRecords.getValue(security, TICK_TYPE_MAPPER[tickType], field)
        return ans

    def get_contract_details(self, security, field):
        orderIdList = self.brokerClient.request_data(30, 0, ReqData.reqContractDetails(security))
        result = self.brokerClient.requestResults[orderIdList[0]]  # return a dataFrame
        return self._extract_contractDetails(result, field)

    def _extract_contractDetails(self, df, field):
        ans = {}
        if type(field) == str:
            field = [field]
        for item in field:
            if item in ['conId', 'symbol', 'secType', 'LastTradeDateOrContractMonth', 'strike', 'right', 'multiplier',
                        'exchange', 'currency', 'localSymbol', 'primaryExchange', 'tradingClass', 'includeExpired',
                        'secIdType', 'secId', 'comboLegs', 'underComp', 'comboLegsDescrip']:

                if hasattr(df.iloc[0]['contractDetails'].summary, item):
                    ans[item] = getattr(df.iloc[0]['contractDetails'].summary, item)
                else:
                    ans[item] = 'not found'
            elif item in ['marketName', 'minTick', 'priceMagnifier', 'orderTypes', 'validExchanges', 'underConId',
                          'longName', 'contractMonth', 'industry', 'category', 'subcategory', 'timeZoneId',
                          'tradingHours', 'liquidHours', 'evRule', 'evMultiplier', 'mdSizeMultiplier', 'aggGroup',
                          'secIdList', 'underSymbol', 'underSecType', 'marketRuleIds', 'realExpirationDate', 'cusip',
                          'ratings', 'descAppend', 'bondType', 'couponType', 'callable', 'putable', 'coupon',
                          'convertible', 'maturity', 'issueDate', 'nextOptionDate', 'nextOptionType',
                          'nextOptionPartial',
                          'notes']:
                if hasattr(df.iloc[0]['contractDetails'], item):
                    ans[item] = getattr(df.iloc[0]['contractDetails'], item)
                else:
                    ans[item] = 'not found'
            elif item == 'summary':
                return df.loc[:, ['contractName', 'expiry', 'strike', 'right', 'multiplier', 'contract', 'security']]
            else:
                self.log.error(__name__ + '::_extract_contractDetails: Invalid item = %s' % (item,))
                exit()
        return ans

    def place_order(self, ibridgePyOrder, followUp=True):
        """
        followUp = True, which means request_data follows up on orderStatues
        """
        self.log.debug(__name__ + '::place_order: ibridgePyOrder=%s' % (str(ibridgePyOrder),))
        orderId = ibridgePyOrder.orderId
        contract = ibridgePyOrder.requestedContract
        order = ibridgePyOrder.requestedOrder
        self.brokerServiceOrderStatusBook.createFromIbridgePyOrder(ibridgePyOrder)
        reqIdList = self.request_data(10, 0, ReqData.placeOrder(orderId, contract, order, followUp))
        return self.brokerClient.requestResults[reqIdList[0]]  # return orderId

    def get_account_info(self, accountCode, tags):  # get account related info
        self.log.debug(__name__ + '::get_account_info: accountCode=%s tags=%s' % (str(accountCode), str(tags)))
        if isinstance(tags, str):
            return self.get_account_info_oneKey(accountCode, tags)
        elif isinstance(tags, list):
            ans = []
            for key in tags:
                ans.append(self.get_account_info_oneKey(accountCode, key))
            return ans

    def get_account_info_oneKey(self, accountCode, key):
        self.log.debug(__name__ + '::get_account_info_oneKey: accountCode=%s key=%s' % (str(accountCode), str(key)))
        if self.userConfig.multiAccountFlag:
            val = self.traderAccountSummaryRecords.getValue(accountCode, key)
        else:
            val = self.traderAccountValueRecords.getValue(accountCode, key)
        # validate_not_equal_none(__name__ + '::get_account_info_oneKey', val, (accountCode, key, currency))
        return val

    def get_position(self, accountCode, security):
        """
        Guarantee to return a PositionRecord
        :param accountCode:
        :param security:
        :return: Guarantee to return a PositionRecord
        """
        adj_security = stripe_exchange_primaryExchange_from_security(security)
        self.log.debug(__name__ + '::get_position: adj_security=%s' % (adj_security.full_print(),))
        return self.traderPositionRecords.getPositionRecord(accountCode, adj_security)

    def get_accountSummary_info(self, accountCode, tags, currency='USD'):  # get account related info
        if isinstance(tags, str):
            return self._get_accountSummary_info_oneKey(accountCode, tags, currency)
        elif isinstance(tags, list):
            ans = []
            for key in tags:
                ans.append(self._get_accountSummary_info_oneKey(accountCode, key, currency))
            return ans

    def _get_accountSummary_info_oneKey(self, accountCode, key, currency='USD'):
        val = self.traderAccountSummaryRecords.getValue(accountCode, key, currency)
        validate_not_equal_none(__name__ + '::_get_accountSummary_info_oneKey', val, (accountCode, key, currency))
        return val

    def hold_any_position(self, accountCode):
        return self.traderPositionRecords.hold_any_position(accountCode)

    def get_all_positions(self, accountCode):
        """
        Get all of positionRecords associated with the accountCode
        :param accountCode:
        :return: dictionary, keyed by str_security, value = PositionRecord
        """
        return self.traderPositionRecords.get_all_positions(accountCode)

    def get_all_orders(self, accountCode):
        orderIdList = self.brokerServiceOrderStatusBook.get_all_orderId(accountCode)
        if len(orderIdList) == 0:
            return []
        ans = {}
        for orderId in orderIdList:
            ans[orderId] = self.get_order(orderId)
        return ans

    def get_all_open_orders_orderIds(self, accountCode):
        orderIds = self.brokerServiceOrderStatusBook.get_all_orderId(accountCode)
        ans = []
        for orderId in orderIds:
            status = self.get_order_status(orderId)
            if status in [OrderStatus.APIPENDING, OrderStatus.PENDINGSUBMIT, OrderStatus.PENDINGCANCEL,
                          OrderStatus.PRESUBMITTED, OrderStatus.SUBMITTED]:
                ans.append(orderId)
        return ans

    def get_order_status(self, orderId):
        return self.get_order_info(orderId, 'status')

    def get_order(self, orderId):
        """

        :param orderId: int
        :return: broker_factory::records_def::IBridgePyOrder
        """
        self.log.debug(__name__ + '::get_order: orderId=%s' % (orderId,))
        return self.get_order_info(orderId, 'IbridgePyOrder')

    def get_order_info(self, orderId, tag):
        accountCode = self.brokerClient.getAccountCodeFromOrderId(orderId)
        return self.brokerServiceOrderStatusBook.getValue(accountCode, orderId, tag)

    def cancel_order(self, orderId):
        self.log.debug(__name__ + '::cancel_order: orderId=%s' % (orderId,))
        self.request_data(30, 0, ReqData.cancelOrder(orderId))

    def order_status_monitor(self, orderId, target_status, waitingTimeInSeconds=30):
        self.log.notset(__name__ + '::order_status_monitor: orderId=%s target_status=%s' % (orderId, target_status))
        timer = dt.datetime.now()
        exit_flag = True
        while exit_flag:
            time.sleep(0.1)
            self.brokerClient.processMessagesWrapper(self.get_datetime())

            if (dt.datetime.now() - timer).total_seconds() <= waitingTimeInSeconds:
                tmp_status = self.get_order_status(orderId)
                if isinstance(target_status, str):
                    if tmp_status == target_status:
                        return True
                elif isinstance(target_status, list):
                    if tmp_status in target_status:
                        return True
            else:
                self.log.error(__name__ + '::order_status_monitor: EXIT, waiting time is too long, >%i' % (
                    waitingTimeInSeconds,))
                status = self.get_order_status(orderId)
                ibridgePyOrder = self.get_order_info(orderId, 'IbridgePyOrder')
                contract = ibridgePyOrder.requestedContract
                self.log.error(__name__ + '::order_status_monitor: EXIT, orderId=%i, status=%s, contract=%s'
                               % (orderId, status, print_contract(contract)))
                exit()
