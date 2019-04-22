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

import pandas as pd
import datetime as dt
import os
import time
import pytz
from IBridgePy.quantopian import Security, from_security_to_contract, from_contract_to_security
from IBridgePy.constants import SymbolStatus, OrderType, RunMode, ExchangeName, LiveBacktest, TimeConcept, ReqHistParam
from IBridgePy import IBCpp
from broker_factory.records_def import IbridgePyOrder, print_contract, print_IB_order
from copy import copy
from BasicPyLib.BasicTools import roundToMinTick, dt_to_utc_in_seconds
from sys import exit


def calculate_startTime(endTime, goBack, barSize):
    # 1S = 1 second; 1T = 1 minute; 1H = 1 hour
    global startTime
    # !!!!strptime silently discard tzinfo!!!
    endTime = dt.datetime.strptime(endTime, "%Y%m%d %H:%M:%S %Z")  # string -> dt.datetime
    endTime = pytz.timezone('UTC').localize(endTime)

    if barSize == '1 second':
        endTime = endTime.replace(microsecond=0)
    elif barSize == ReqHistParam.BarSize.ONE_MIN:
        endTime = endTime.replace(second=0, microsecond=0)
    elif barSize == '1 hour':
        endTime = endTime.replace(minute=0, second=0, microsecond=0)
    elif barSize == '1 day':
        endTime = endTime.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        print(__name__ + '::calculate_startTime: cannot handle barSize=%s' % (barSize,))
        exit()

    if 'S' in goBack:
        startTime = endTime - dt.timedelta(seconds=int(goBack[:-1]))
    elif 'D' in goBack:
        startTime = endTime - dt.timedelta(days=int(goBack[:-1]))
    elif 'W' in goBack:
        startTime = endTime - dt.timedelta(weeks=int(goBack[:-1]))
    elif 'Y' in goBack:
        startTime = endTime.replace(endTime.year - int(goBack[:-1]))
    return startTime, endTime


def calculate_startTimePosition(endTime, goBack, barSize):
    """

    :param endTime: string, "%Y%m%d %H:%M:%S %Z"
    :param goBack:
    :param barSize: '1 day', '1 hour', '1 min'
    :return:
    """

    # !!!!strptime silently discard tzinfo!!!
    global startTimePosition
    endTime = dt.datetime.strptime(endTime, "%Y%m%d %H:%M:%S %Z")  # string -> dt.datetime
    endTime = pytz.timezone('UTC').localize(endTime)

    endTime = int(dt_to_utc_in_seconds(endTime))

    if barSize == ReqHistParam.BarSize.ONE_DAY:
        if 'D' in goBack:
            startTimePosition = int(goBack[:-1])
        else:
            print(__name__ + '::calculate_startTimePosition: EXIT, cannot handle goBack=%s' % (goBack,))
            exit()
    elif barSize == ReqHistParam.BarSize.ONE_MIN:
        if 'S' in goBack:
            startTimePosition = int(goBack[:-1] / 60)
        else:
            print(__name__ + '::calculate_startTimePosition: EXIT, cannot handle goBack=%s' % (goBack,))
            exit()
    return startTimePosition, endTime


def add_exchange_primaryExchange_to_security(security):
    """
    security_info.csv must stay in this directory with this file
    :param security:
    :return:
    """
    # do nothing if it is a superSymbol
    if security.symbolStatus == SymbolStatus.SUPER_SYMBOL:
        return security

    stockList = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'security_info.csv'))

    # if it is not a superSymbol, strictly follow security_info.csv
    security.exchange = search_security_in_file(stockList, security.secType, security.symbol,
                                                security.currency, 'exchange')
    security.primaryExchange = search_security_in_file(stockList, security.secType, security.symbol,
                                                       security.currency, 'primaryExchange')
    return security


def symbol(str_security):
    """
    IBridgePy::TraderBasicResources has self.symbol that will be used by IBridgePy users.
    This symbol will be used by other purposes.
    :param str_security:
    :return:
    """
    security = from_symbol_to_security(str_security)
    return add_exchange_primaryExchange_to_security(security)


def symbols(*args):
    ans = []
    for item in args:
        ans.append(symbol(item))
    return ans


def from_symbol_to_security(s1):
    if ',' not in s1:
        s1 = 'STK,%s,USD' % (s1,)

    secType = s1.split(',')[0].strip()
    ticker = s1.split(',')[1].strip()
    currency = s1.split(',')[2].strip()
    if secType in ['CASH', 'STK']:
        return Security(secType=secType, symbol=ticker, currency=currency)
    else:
        print('Definition of %s is not clear!' % (s1,))
        print('Please use superSymbol to define a str_security')
        print(r'http://www.ibridgepy.com/ibridgepy-documentation/#superSymbol')
        exit()


def from_string_to_security(st):
    if ',' not in st:
        print(__name__ + '::from_string_to_security: EXIT, format is not correct')
        exit()
    stList = st.split(',')
    secType = stList[0].strip()
    if secType in ['CASH', 'STK']:
        primaryExchange = stList[1].strip()
        exchange = stList[2].strip()
        ticker = stList[3].strip()
        currency = stList[4].strip()
        return Security(secType=secType, symbol=ticker, currency=currency, exchange=exchange,
                        primaryExchange=primaryExchange, symbolStatus=SymbolStatus.STRING_CONVERTED)

    elif secType in ['FUT', 'BOND']:
        primaryExchange = stList[1].strip()
        exchange = stList[2].strip()
        ticker = stList[3].strip()
        currency = stList[4].strip()
        expiry = stList[5].strip()
        return Security(secType=secType, symbol=ticker, currency=currency, exchange=exchange,
                        primaryExchange=primaryExchange, expiry=expiry,
                        symbolStatus=SymbolStatus.STRING_CONVERTED)
    else:
        primaryExchange = stList[1].strip()
        exchange = stList[2].strip()
        ticker = stList[3].strip()
        currency = stList[4].strip()
        expiry = stList[5].strip()
        strike = float(stList[6].strip())
        right = stList[7].strip()
        multiplier = stList[8].strip()
        return Security(secType=secType, symbol=ticker, currency=currency, exchange=exchange,
                        primaryExchange=primaryExchange, expiry=expiry, strike=strike, right=right,
                        multiplier=multiplier,
                        symbolStatus=SymbolStatus.STRING_CONVERTED)


def superSymbol(secType=None,
                symbol=None,
                currency='USD',
                exchange='',
                primaryExchange='',
                localSymbol='',
                expiry='',
                strike=0.0,
                right='',
                multiplier='',
                includeExpired=False):
    return Security(secType=secType, symbol=symbol, currency=currency, exchange=exchange, localSymbol=localSymbol,
                    primaryExchange=primaryExchange, expiry=expiry, strike=strike, right=right,
                    multiplier=multiplier, includeExpired=includeExpired, symbolStatus=SymbolStatus.SUPER_SYMBOL)


def read_in_hash_config(fileName):
    full_file_path = os.path.join(os.getcwd(), 'IBridgePy', fileName)
    return read_hash_config(full_file_path)


def read_hash_config(full_file_path):
    if os.path.isfile(full_file_path):
        with open(full_file_path) as f:
            line = f.readlines()
        return line[0].strip()
    else:
        print('hash.conf file is missing at %s. EXIT' % (str(full_file_path),))
        exit()


def search_security_in_file(df, secType, ticker, currency, param, waive=False):
    if secType == 'CASH':
        if param == 'exchange':
            return 'IDEALPRO'
        elif param == 'primaryExchange':
            return 'IDEALPRO'
        else:
            error_messages(5, secType + ' ' + ticker + ' ' + param)
    else:
        tmp_df = df[(df['Symbol'] == ticker) & (df['secType'] == secType) & (df['currency'] == currency)]
        if tmp_df.shape[0] == 1:  # found 1
            exchange = tmp_df['exchange'].values[0]
            primaryExchange = tmp_df['primaryExchange'].values[0]
            if param == 'exchange':
                if type(exchange) == float:
                    if secType == 'STK':
                        return 'SMART'
                    else:
                        error_messages(4, secType + ' ' + ticker + ' ' + param)
                else:
                    return exchange
            elif param == 'primaryExchange':
                if type(primaryExchange) == float:
                    return ''
                return primaryExchange
            else:
                error_messages(5, secType + ' ' + ticker + ' ' + param)
        elif tmp_df.shape[0] > 1:  # found more than 1
            error_messages(3, secType + ' ' + ticker + ' ' + param)
        else:  # found None
            if waive:
                return 'WAIVED'
            error_messages(4, secType + ' ' + ticker + ' ' + param)


def error_messages(n, st):
    if n == 1:
        print ('Definition of %s is not clear!' % (st,))
        print ('Please add this str_security in IBridgePy/security_info.csv')
        exit()
    elif n == 2:
        print ('Definition of %s is not clear!' % (st,))
        print ('Please use superSymbol to define a str_security')
        print (r'http://www.ibridgepy.com/ibridgepy-documentation/#superSymbol')
        exit()
    elif n == 3:
        print ('Found too many %s in IBridgePy/security_info.csv' % (st,))
        print ('%s must be unique.' % (' '.join(st.split(' ')[:-1]),))
        exit()
    elif n == 4:
        print ('Exchange of %s is missing.' % (' '.join(st.split(' ')[:-1]),))
        print ('Please add this str_security in IBridgePy/security_info.csv')
        exit()
    elif n == 5:
        print ('%s of %s is missing.' % (st.split(' ')[-1], ' '.join(st.split(' ')[:-1])))
        print ('Please add this info in IBridgePy/security_info.csv')
        exit()


def transform_action(amount):
    if amount > 0:
        return 'BUY', 'SELL', amount
    else:
        return 'SELL', 'BUY', -1 * amount


def special_match(target, val, version):
    if target == 'any':
        return True
    else:
        if version == 'monthWeek':
            if target >= 0:
                return target == val[0]
            else:
                return target == val[1]
        elif version == 'hourMinute':
            return target == val
        else:
            print (__name__ + '::_match: EXIT, cannot handle version=%s' % (version,))
            exit()


def display_all_contractDetails(contractDetails):
    for item in ['conId', 'symbol', 'secType', 'LastTradeDateOrContractMonth',
                 'strike', 'right', 'multiplier', 'exchange', 'currency',
                 'localSymbol', 'primaryExchange', 'tradingClass',
                 'includeExpired', 'secIdType', 'secId', 'comboLegs', 'underComp',
                 'comboLegsDescrip']:
        try:
            print (item, getattr(contractDetails.summary, item))
        except AttributeError:
            print (item, 'not found')
    for item in ['marketName', 'minTick', 'priceMagnifier', 'orderTypes',
                 'validExchanges', 'underConId', 'longName', 'contractMonth',
                 'industry', 'category', 'subcategory',
                 'timeZoneId', 'tradingHours', 'liquidHours',
                 'evRule', 'evMultiplier', 'mdSizeMultiplier', 'aggGroup',
                 'secIdList',
                 'underSymbol', 'underSecType', 'marketRuleIds', 'realExpirationDate',
                 'cusip', 'ratings', 'descAppend',
                 'bondType', 'couponType', 'callable', 'putable',
                 'coupon', 'convertible', 'maturity', 'issueDate',
                 'nextOptionDate', 'nextOptionType', 'nextOptionPartial',
                 'notes']:
        try:
            print (item, getattr(contractDetails, item))
        except AttributeError:
            print (item, 'not found in contractDetails')


def from_arg_to_pandas_endCheckList(args):
    ans = pd.DataFrame()
    temp = 0
    for ct in args:
        newRow = pd.DataFrame({'reqId': ct.reqId, 'status': ct.status,
                               'followUp': bool(ct.followUp), 'reqData': ct,
                               'reqType': ct.reqType, 'resendOnFailure': ct.resendOnFailure}, index=[temp])
        temp += 1
        ans = ans.append(newRow)
    return ans


def simulate_commissions(execution):
    # self.log.debug(__name__ + '::simulate_commission: $0.0075 per share or $1.00')
    return roundToMinTick(max(execution.shares * 0.0075, 1.0), 0.01)


class Event:
    def __init__(self):
        pass

    class SingleEvent:
        def __init__(self, onHour, onMinute, do_something, passFunc=(lambda x: True)):
            self.passFunc = passFunc
            self.do_something = do_something  # !!!!!! do_something must have one input -- datetime
            self.onHour = onHour
            self.onMinute = onMinute

    class RepeatedEvent:
        def __init__(self, freq, do_something, passFunc=(lambda x: True)):
            """

            :param freq: number in seconds !!!
            :param do_something: !!!!!! do_something must have one input -- datetime
            :param passFunc: True = stop repeater
            """
            self.freq = freq
            self.do_something = do_something
            self.passFunc = passFunc

    class ConceptEvent:
        def __init__(self, concept, do_something, passFunc=(lambda x: True)):
            """

            :param concept: NEW_DAY, NEW_HOUR
            :param do_something: !!!!!! do_something must have one input -- datetime
            :param passFunc: True = stop repeater
            """
            self.concept = concept
            self.do_something = do_something
            self.passFunc = passFunc


class RepeaterEngine:
    def __init__(self, liveOrTest, getTimeNowFuncGlobal, stopFuncGlobal=(lambda x: False)):
        self.spotEvents = {}  # hold all events scheduled at spot time
        self.repeatedEvents = {}  # hold all repeated events
        self.conceptEvents = {}  # new day, new hour etc
        self.getTimeNowFuncGlobal = getTimeNowFuncGlobal
        self.stopFuncGlobal = stopFuncGlobal
        self.timePrevious = dt.datetime(1970, 12, 31, 23, 59, 59)
        self.liveOrTest = liveOrTest

    def schedule_event(self, event):
        if isinstance(event, Event.SingleEvent):
            self._spot_time_scheduler(event)
        elif isinstance(event, Event.RepeatedEvent):
            self._repeated_scheduler(event)
        elif isinstance(event, Event.ConceptEvent):
            self._concept_scheduler(event)

    def _repeated_scheduler(self, repeatedEvent):
        """
        Change repeated events to spot-time events, Then, add it to repeaterEngine which only process spot-time events
        :param repeatedEvent:
        :return:
        """
        if repeatedEvent.freq not in self.repeatedEvents:
            self.repeatedEvents[repeatedEvent.freq] = []
        self.repeatedEvents[repeatedEvent.freq].append(repeatedEvent)

    def _concept_scheduler(self, conceptEvent):
        """
        Change repeated events to spot-time events, Then, add it to repeaterEngine which only process spot-time events
        :param conceptEvent:
        :return:
        """
        if conceptEvent.concept not in self.conceptEvents:
            self.conceptEvents[conceptEvent.concept] = []
        self.conceptEvents[conceptEvent.concept].append(conceptEvent)

    def _spot_time_scheduler(self, singleEvent):
        spotTime = singleEvent.onHour * 60 + singleEvent.onMinute
        if spotTime not in self.spotEvents:
            self.spotEvents[spotTime] = []
        self.spotEvents[spotTime].append(singleEvent)

    def repeat(self):
        # print(__name__ + '::repeat')
        while True:
            try:
                timeNow = self.getTimeNowFuncGlobal()
            except StopIteration:
                break

            if self.stopFuncGlobal(timeNow):
                break

            # print(__name__, timeNow)
            # handle repeated Events
            currentHourMinuteSeconds = timeNow.hour * 60 * 60 + timeNow.minute * 60 + timeNow.second

            # If a new time comes in, check repeatedEvents
            if timeNow.second != self.timePrevious.second or timeNow.minute != self.timePrevious.minute or timeNow.hour != self.timePrevious.hour:
                for freq in self.repeatedEvents:
                    if currentHourMinuteSeconds % freq == 0:
                        # print('repeat freq=%s %s' % (freq, currentHourMinuteSeconds))
                        for event in self.repeatedEvents[freq]:
                            # print(event.passFunc, timeNow, event.passFunc(timeNow))
                            if event.passFunc(timeNow):
                                event.do_something(timeNow)

            # handle spot-time events
            # timezone of onHour and onMinute is as same as the timezone of the timeNow, which is passed by by invoker
            currentHourMinute = timeNow.hour * 60 + timeNow.minute
            prevHourMinute = self.timePrevious.hour * 60 + self.timePrevious.minute
            if currentHourMinute != prevHourMinute:  # Do not run twice within the same minute
                if currentHourMinute in self.spotEvents:  # some events are scheduled at this spot time
                    for event in self.spotEvents[currentHourMinute]:
                        if event.passFunc(timeNow):
                            event.do_something(timeNow)

            if timeNow.day != self.timePrevious.day:
                if TimeConcept.NEW_DAY in self.conceptEvents:
                    for event in self.conceptEvents[TimeConcept.NEW_DAY]:
                        if event.passFunc(timeNow):
                            event.do_something(timeNow)
            if timeNow.hour != self.timePrevious.hour:
                if TimeConcept.NEW_HOUR in self.conceptEvents:
                    for event in self.conceptEvents[TimeConcept.NEW_HOUR]:
                        if event.passFunc(timeNow):
                            event.do_something(timeNow)

            # slow down for live mode
            if self.liveOrTest == LiveBacktest.LIVE:
                # print('slow down')
                time.sleep(0.5)
            self.timePrevious = timeNow


def create_order(orderId, accountCode, security, amount, orderDetails, createdTime,
                 ocaGroup=None, ocaType=None, transmit=None, parentId=None,
                 orderRef='', outsideRth=False, hidden=False):
    contract = from_security_to_contract(security)

    order = IBCpp.Order()
    if hidden:
        if contract.exchange == ExchangeName.ISLAND:
            order.hidden = True
        else:
            print(__name__ + '::create_order: EXIT, only ISLAND accept hidden orders')
            exit()

    if amount > 0:
        order.action = 'BUY'
    elif amount < 0:
        order.action = 'SELL'

    order.account = accountCode
    order.totalQuantity = abs(amount)  # int only
    order.orderType = orderDetails.orderType  # LMT, MKT, STP
    order.tif = orderDetails.tif
    order.orderRef = str(orderRef)
    order.outsideRth = outsideRth

    if ocaGroup is not None:
        order.ocaGroup = ocaGroup
    if ocaType is not None:
        order.ocaType = ocaType
    if transmit is not None:
        order.transmit = transmit
    if parentId is not None:
        order.parentId = parentId

    if orderDetails.orderType == 'MKT':
        pass
    elif orderDetails.orderType == 'LMT':
        order.lmtPrice = orderDetails.limit_price
    elif orderDetails.orderType == 'STP':
        order.auxPrice = orderDetails.stop_price
    elif orderDetails.orderType == 'STP LMT':
        order.lmtPrice = orderDetails.limit_price
        order.auxPrice = orderDetails.stop_price
    elif orderDetails.orderType == 'TRAIL LIMIT':
        if orderDetails.trailing_amount is not None:
            order.auxPrice = orderDetails.trailing_amount  # trailing amount
        if orderDetails.trailing_percent is not None:
            order.trailingPercent = orderDetails.trailing_percent
        order.trailStopPrice = orderDetails.stop_price
        if order.action == 'SELL':
            order.lmtPrice = orderDetails.stop_price - orderDetails.limit_offset
        elif order.action == 'BUY':
            order.lmtPrice = orderDetails.stop_price + orderDetails.limit_offset
    elif orderDetails.orderType == 'TRAIL':
        if orderDetails.trailing_amount is not None:
            order.auxPrice = orderDetails.trailing_amount  # trailing amount
        if orderDetails.trailing_percent is not None:
            order.trailingPercent = orderDetails.trailing_percent
        if orderDetails.stop_price is not None:
            order.trailStopPrice = orderDetails.stop_price
    else:
        print(__name__ + '::create_order: EXIT,Cannot handle orderType=%s' % (orderDetails.orderType,))

    an_order = IbridgePyOrder(orderId, requestedContract=contract, requestedOrder=order, createdTime=createdTime)
    return an_order


def stripe_exchange_primaryExchange_from_contract(contract):
    security = from_contract_to_security(contract)
    return stripe_exchange_primaryExchange_from_security(security)


def stripe_exchange_primaryExchange_from_security(security):
    copy_security = copy(security)
    copy_security.exchange = ''
    copy_security.primaryExchange = ''
    return copy_security


def check_same_security(sec1, sec2):
    if sec1.secType in ['STK', 'CASH']:
        items = ['secType', 'symbol', 'currency']
    elif sec1.secType == 'FUT':
        items = ['secType', 'symbol', 'currency', 'expiry']
    else:
        items = ['secType', 'symbol', 'currency', 'expiry', 'strike',
                 'right', 'multiplier']
    for para in items:
        if getattr(sec1, para) != getattr(sec2, para):
            return False
    return True
