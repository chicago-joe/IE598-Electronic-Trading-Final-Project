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
from broker_client_factory.BrokerClientBase import BrokerClientBase
import pandas as pd
import pytz
from IBridgePy.quantopian import from_contract_to_security
import datetime as dt
from sys import exit
from BasicPyLib.BasicTools import dt_to_utc_in_seconds
from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_contract
from IBridgePy.constants import OrderStatus
from broker_factory.records_def import PositionRecord, OrderStatusRecord, OpenOrderRecord, ExecDetailsRecord, \
    TickPriceRecord, print_contract, \
    TickSizeRecord, TickStringRecord, AccountValueRecord, AccountSummaryRecord, TickOptionComputationRecord

# https://www.interactivebrokers.com/en/software/api/apiguide/tables/tick_types.htm
MSG_TABLE = {0: 'bid size', 1: 'bid price', 2: 'ask price', 3: 'ask size',
             4: 'last price', 5: 'last size', 6: 'daily high', 7: 'daily low',
             8: 'daily volume', 9: 'close', 14: 'open', 27: 'option call open interest', 28: 'option put open interest'}


class CallBacks(BrokerClientBase):
    def accountDownloadEnd(self, accountCode):
        """
        Responses of reqAccountUpdates
        """
        self.log.debug(__name__ + '::accountDownloadEnd: accountCode=%s' % (accountCode,))
        reqId = self.end_check_list[self.end_check_list['reqType'] == 'reqAccountUpdates']['reqId']
        self.end_check_list.loc[reqId, 'status'] = 'Done'

    def accountSummary(self, reqId, accountCode, tag, value, currency):
        """
        !!!!!!!! type(value) is STRING !!!!!!!!
        """
        self.log.notset(__name__ + '::accountSummary: reqId=%s accountCode=%s tag=%s value=%s currency=%s'
                        % (str(reqId), accountCode, tag, str(value), currency))
        try:
            value = float(value)
        except:
            pass
        self.brokerService.setAccountSummary(AccountSummaryRecord(reqId, accountCode, tag, value, currency))

    def accountSummaryEnd(self, reqId):
        self.log.debug(__name__ + '::accountSummaryEnd: ' + str(reqId))
        reqId = self.end_check_list[self.end_check_list['reqType'] == 'reqAccountSummary']['reqId']
        self.end_check_list.loc[reqId, 'status'] = 'Done'

    def bondContractDetails(self, reqId, contractDetails):
        """
        IB callback function to receive str_security info
        """
        self.log.info(__name__ + '::bondContractDetails:' + str(reqId))
        newRow = pd.DataFrame({'right': contractDetails.summary.right,
                               'strike': float(contractDetails.summary.strike),
                               # 'expiry':dt.datetime.strptime(contractDetails.summary.expiry, '%Y%m%d'),
                               'expiry': contractDetails.summary.expiry,
                               'contractName': print_contract(contractDetails.summary),
                               'str_security': contractDetails.summary,
                               'multiplier': contractDetails.summary.multiplier,
                               'contractDetails': contractDetails
                               }, index=[len(self.end_check_list_result[reqId])])
        self.end_check_list_result[reqId] = self.end_check_list_result[reqId].append(newRow)

    def commissionReport(self, commissionReport):
        self.log.notset(__name__ + '::commissionReport: DO NOTHING' + str(commissionReport))

    def contractDetails(self, reqId, contractDetails):
        """
        IB callback function to receive str_security info
        """
        self.log.debug(__name__ + '::contractDetails:' + str(reqId))
        newRow = pd.DataFrame({'right': contractDetails.summary.right,
                               'strike': float(contractDetails.summary.strike),
                               'expiry': contractDetails.summary.expiry,
                               'contractName': print_contract(contractDetails.summary),
                               'security': from_contract_to_security(contractDetails.summary),
                               'contract': contractDetails.summary,
                               'multiplier': contractDetails.summary.multiplier,
                               'contractDetails': contractDetails
                               }, index=[len(self.end_check_list_result[reqId])])
        self.end_check_list_result[reqId] = self.end_check_list_result[reqId].append(newRow)

    def contractDetailsEnd(self, reqId):
        """
        IB callback function to receive the ending flag of str_security info
        """
        self.log.debug(__name__ + '::contractDetailsEnd:' + str(reqId))
        self.end_check_list.loc[reqId, 'status'] = 'Done'

        self.setRequestResults(reqId, self.end_check_list_result[reqId])

    def currentTime(self, tm):
        """
        IB C++ API call back function. Return system time in datetime instance
        constructed from Unix timestamp using the showTimeZone from MarketManager
        """
        self.log.debug(__name__ + '::currentTime: tm=%s' % (str(tm),))
        serverTime = dt.datetime.fromtimestamp(tm, tz=pytz.utc)
        self.localServerTimeDiff = serverTime - self.localMachineTime
        self.brokerService.setLocalToServerTimeDiff(self.localServerTimeDiff)
        self.log.debug(__name__ + '::currentTime, localServerTimeDiff = %s serverTime = % s localMachineTime = %s'
                       % (self.localServerTimeDiff, serverTime, self.localMachineTime))
        reqId = self.end_check_list[self.end_check_list['reqType'] == 'reqCurrentTime']['reqId']
        self.end_check_list.loc[reqId, 'status'] = 'Done'

    def error(self, errorId, errorCode, errorString):
        """
        only print real error messages, which is errorId < 2000 in IB's error
        message system, or program is in debug mode
        """
        if errorCode in [2119, 2104, 2108, 2106, 2107, 2103]:
            pass
        elif errorCode == 202:  # cancel order is confirmed
            self.end_check_list.loc[errorId, 'status'] = 'Done'
        elif errorCode in [201, 399, 165, 2113, 2105, 2148, 10148]:  # No action, just show error message
            # 201 = order rejected - Reason: No such order
            # 10148, error message: OrderId 230 that needs to be cancelled can not be cancelled, state: Cancelled.
            # 10147, error message: OrderId 2 that needs to be cancelled is not found.
            # TODO: it should be handled better when it is related to cancel order.
            self.log.error(__name__ + ':errorId = %s, errorCode = %s, error message: %s' % (
                str(errorId), str(errorCode), errorString))
            if errorCode in [10147, 10148]:
                reqId = self.end_check_list[self.end_check_list['reqType'] == 'cancelOrder']['reqId']
                self.end_check_list.loc[reqId, 'status'] = 'Done'
                if errorCode == 10147:
                    self.log.error('this order was placed by another clientId and cannot be cancelled.')
                    exit()

        elif errorCode == 162:
            if 'API scanner subscription cancelled' in errorString:
                self.log.debug(__name__ + ':errorId = %s, errorCode = %s, error message: %s' % (
                    str(errorId), str(errorCode), errorString))
                reqId = self.end_check_list[self.end_check_list['reqType'] == 'cancelScannerSubscription']['reqId']
                self.end_check_list.loc[reqId, 'status'] = 'Done'
            else:
                self.log.error(__name__ + ':errorId = %s, errorCode = %s, error message: %s' % (
                    str(errorId), str(errorCode), errorString))
                self.log.error(__name__ + ':EXIT IBridgePy version = %s' % (str(self.versionNumber),))
                exit()
        elif 110 <= errorCode <= 449:
            self.log.error(__name__ + ':EXIT errorId = %s, errorCode = %s, error message: %s' % (
                str(errorId), str(errorCode), errorString))
            if errorCode == 200:  # No security definition has been found for the request.
                self.log.error(self.reqDataHist.loc[errorId, 'reqData'].param['security'].full_print())
            self.log.error(__name__ + ':EXIT IBridgePy version = %s' % (str(self.versionNumber),))
            exit()

        elif errorCode in [1100, 1101, 1102]:
            if errorCode == 1100:
                self.connectionGatewayToServer = False
            elif errorCode in [1101, 1102]:
                self.connectionGatewayToServer = True
        else:
            self.log.error(__name__ + ':EXIT errorId = %s, errorCode = %s, error message: %s' % (
                str(errorId), str(errorCode), errorString))
            self.log.error(__name__ + ':EXIT IBridgePy version= %s' % (str(self.versionNumber),))
            exit()

    def execDetails(self, reqId, contract, execution):
        self.log.debug(__name__ + '::execDetails: reqId= %i' % (int(reqId),) + print_contract(contract))
        self.log.debug(__name__ + '::execDetails: %s %s %s %s %s %s'
                       % (str(execution.side), str(execution.shares), str(execution.price),
                          str(execution.orderRef), str(execution.orderId), str(execution.clientId)))
        self.brokerService.setExecDetails(ExecDetailsRecord(reqId, contract, execution))

        # IB will not invoke updateAccountValue immediately after execDetails
        # http://www.ibridgepy.com/knowledge-base/#Q_What_functions_will_be_called_back_from_IB_server_and_what_is_the_sequence_of_call_backs_after_an_order_is_executed
        # To make sure user know the rough cashValue and positionValue.
        # IBridgePy has to simulate them.
        # The accurate value will be updated by IB regular updateAccountValue every 3 minutes.
        accountCode = self.getAccountCodeFromOrderId(execution.orderId)
        currentCashValue = self.brokerService.get_account_info_oneKey(accountCode, 'TotalCashValue')
        currentPositionValue = self.brokerService.get_account_info_oneKey(accountCode, 'GrossPositionValue')
        cashChange = execution.shares * float(execution.price)
        if execution.side == 'BOT':
            currentCashValue -= cashChange
            currentPositionValue += cashChange
        elif execution.side == 'SLD':
            currentCashValue += cashChange
            currentPositionValue -= cashChange
        self.updateAccountValue('GrossPositionValue', currentPositionValue, 'USD', accountCode)
        self.updateAccountValue('TotalCashValue', currentCashValue, 'USD', accountCode)

    def historicalData(self, reqId, timeString, price_open, price_high, price_low, price_close, volume, barCount, WAP,
                       hasGaps):
        """
        call back function from IB C++ API
        return the historical data for requested security
        """
        self.log.debug(__name__ + '::historicalData: reqId=%s timeString=%s barCount=%s WAP=%s hasGap=%s'
                       % (str(reqId), str(timeString), str(barCount), str(WAP), str(hasGaps)))

        # for any reason, the reqId is not in the self.end_check_list,
        # just ignore it. because the returned results must come from the previous request.
        if reqId not in self.end_check_list.index:
            return

        if 'finished' in str(timeString):
            self.end_check_list.loc[reqId, 'status'] = 'Done'

            # prepare to return results by setRequestResults
            self.setRequestResults(reqId, self.end_check_list_result[reqId])
        else:
            if self.end_check_list.loc[reqId, 'reqData'].param['formatDate'] == 1:
                if '  ' in timeString:
                    dateTime = dt.datetime.strptime(timeString, '%Y%m%d  %H:%M:%S')  # change string to datetime
                else:
                    dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
                dateTime = pytz.timezone('UTC').localize(dateTime)
            else:  # formatDate is UTC time in seconds, str type
                # The format in which the incoming bars' date should be presented. Note that for day bars, only yyyyMMdd format is available.
                if len(timeString) > 9:  # return datetime, not date
                    dateTime = dt.datetime.fromtimestamp(float(timeString), tz=pytz.utc)
                else:  # return date, not datetime
                    dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
                dateTime = int(dt_to_utc_in_seconds(dateTime))  # change to int type

            newRow = pd.DataFrame({'open': price_open, 'high': price_high,
                                   'low': price_low, 'close': price_close,
                                   'volume': volume}, index=[dateTime])
            self.end_check_list_result[reqId] = self.end_check_list_result[reqId].append(newRow)

    def nextValidId(self, orderId):
        """
        IB API requires an orderId for every order, and this function obtains
        the next valid orderId. This function is called at the initialization
        stage of the program and results are recorded in startingNextValidIdNumber,
        then the orderId is track by the program when placing orders
        """
        self.log.debug(__name__ + '::nextValidId: Id = ' + str(orderId))
        self.nextId = orderId
        reqId = self.end_check_list[self.end_check_list['reqType'] == 'reqIds']['reqId']
        self.end_check_list.loc[reqId, 'status'] = 'Done'

    def openOrder(self, orderId, contract, order, orderState):
        """
        call back function of IB C++ API which updates the open orders indicated
        by orderId
        """
        self.log.debug(__name__ + '::openOrder: orderId = %i contract = %s order.action = %s order.totalQuantity = %s'
                       % (orderId, print_contract(contract), str(order.action), str(order.totalQuantity)))
        self.orderIdToAccountCode[orderId] = order.account
        if self.brokerService is not None:  # for testing
            self.brokerService.setOpenOrder(OpenOrderRecord(orderId, contract, order, orderState))

    def openOrderEnd(self):
        self.log.debug(__name__ + '::openOrderEnd')
        reqId = self.end_check_list[(self.end_check_list['reqType'] == 'reqAllOpenOrders') |
                                    (self.end_check_list['reqType'] == 'reqOpenOrders') |
                                    (self.end_check_list['reqType'] == 'reqAutoOpenOrders')]['reqId']
        self.end_check_list.loc[reqId, 'status'] = 'Done'

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                    whyHeld):
        """
        call back function of IB C++ API which update status or certain order
        indicated by orderId
        Same orderId may be called back multiple times with status of 'Filled'
        orderStatus is always called back after openOrder
        """
        self.log.debug(__name__ + '::orderStatus: ' + str(orderId) + ", " + str(status) + ", " + str(filled)
                       + ", " + str(remaining) + ", " + str(avgFillPrice))
        if status == OrderStatus.CANCELLED:
            reqId = self.end_check_list[self.end_check_list['reqType'] == 'cancelOrder']['reqId']
            self.end_check_list.loc[reqId, 'status'] = 'Done'
        elif status in [OrderStatus.PRESUBMITTED, OrderStatus.SUBMITTED]:
            reqId = self.end_check_list[self.end_check_list['reqType'] == 'placeOrder']['reqId']
            self.end_check_list.loc[reqId, 'status'] = 'Done'
        if self.brokerService is not None:  # for testing
            self.brokerService.setOrderStatus(
                OrderStatusRecord(orderId, status, filled, remaining, avgFillPrice, permId,
                                  parentId, lastFillPrice, clientId, whyHeld))

    def position(self, accountCode, contract, amount, cost_basis):
        """
        call back function of IB C++ API which updates the position of a security
        of a account
        """
        str_contract = print_contract(contract)
        self.log.debug(
            __name__ + '::position: %s %s %s %s' % (accountCode, str_contract, str(amount), str(cost_basis)))
        # Conclusion: called-back position contract may or may not have exchange info,
        # never see primaryExchange.
        # STK has exchange, CASH does not, FUT does not
        # if contract.exchange != '':
        #    self.log.error(__name__ + '::position: EXIT, contract has exchange=%s' % (print_contract(contract),))
        #    exit()
        security = stripe_exchange_primaryExchange_from_contract(contract)
        self.brokerService.setPosition(PositionRecord(accountCode, security.full_print(), amount, cost_basis, contract))

    def positionEnd(self):
        self.log.debug(__name__ + '::positionEnd: all positions recorded')
        reqId = self.end_check_list[self.end_check_list['reqType'] == 'reqPositions']['reqId']
        self.end_check_list.loc[reqId, 'status'] = 'Done'

    def realtimeBar(self, reqId, time, price_open, price_high, price_low, price_close, volume, wap, count):
        """
        call back function from IB C++ API
        return realTimeBars for requested security every 5 seconds
        """
        self.log.notset(
            __name__ + '::realtimeBar: reqId=%s time=%s price_open=%s price_high=%s price_low=%s price_close=%s volume=%s wap=%s count=%s'
            % (str(reqId), str(time), str(price_open), str(price_high), str(price_low), str(price_close), str(volume),
               str(wap), str(count)))

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        self.log.debug(__name__ + '::scannerData: reqId = %i, rank = %i, contractDetails.summary = %s, distance = %s,\
                benchmark = %s, project = %s, legsStr = %s'
                       % (reqId, rank, print_contract(contractDetails.summary), distance, benchmark,
                          projection, legsStr))
        security = from_contract_to_security(contractDetails.summary)
        newRow = pd.DataFrame({'rank': rank,
                               'contractDetails': contractDetails,
                               'security': security,
                               'distance': distance,
                               'benchmark': benchmark,
                               'projection': projection,
                               'legsStr': legsStr}, index=[len(self.end_check_list_result[reqId])])
        self.end_check_list_result[reqId] = self.end_check_list_result[reqId].append(newRow)

    def scannerDataEnd(self, reqId):
        self.log.debug(__name__ + '::scannerDataEnd:' + str(reqId))
        self.end_check_list.loc[reqId, 'status'] = 'Done'
        self.setRequestResults(reqId, self.end_check_list_result[reqId])

    def scannerParameters(self, xml):
        self.log.debug(__name__ + '::scannerParameters:')
        reqId = self.end_check_list[self.end_check_list['reqType'] == 'reqScannerParameters']['reqId']
        self.end_check_list.loc[reqId, 'status'] = 'Done'
        self.setRequestResults(reqId, xml)

    def tickGeneric(self, reqId, field, value):
        self.log.notset(__name__ + '::tickGeneric: reqId=%i field=%s value=%d' % (reqId, field, value))
        # exit()

    def tickOptionComputation(self, reqId, tickType, impliedVol, delta,
                              optPrice, pvDividend, gamma, vega, theta,
                              undPrice):
        self.log.debug(__name__ + '::tickOptionComputation:\
        reqId=%s %s %s %s %s %s %s %s %s %s' % (
            str(reqId), tickType, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta,
            undPrice))
        security = self.reqDataHist.loc[reqId, 'reqData'].param['security']
        self.brokerService.setTickOptionComputation(
            TickOptionComputationRecord(security, tickType, impliedVol,
                                        delta, optPrice, pvDividend, gamma, vega, theta, undPrice))

    def tickPrice(self, reqId, tickType, price, canAutoExecute):
        """
        call back function of IB C++ API. This function will get tick prices
        """
        self.log.notset(__name__ + '::tickPrice:' + str(reqId) + ' ' + str(tickType) + ' ' + str(price))

        # In order to guarantee valid ask and bid prices, it needs to check if both of ask price and bid price
        # is received.
        if reqId in self.end_check_list.index:
            if tickType == 1:
                if 'Bid' not in self.end_check_list.loc[reqId, 'status']:
                    self.end_check_list.loc[reqId, 'status'] += 'Bid'
            elif tickType == 2:
                if 'Ask' not in self.end_check_list.loc[reqId, 'status']:
                    self.end_check_list.loc[reqId, 'status'] += 'Ask'
            if 'Ask' in self.end_check_list.loc[reqId, 'status'] and 'Bid' in self.end_check_list.loc[reqId, 'status']:
                self.end_check_list.loc[reqId, 'status'] = 'Done'

        str_security = self.realTimePriceRequestedList.findByReqId(reqId)
        self.brokerService.setTickPrice(TickPriceRecord(str_security, tickType, price, canAutoExecute))

    def tickSize(self, reqId, tickType, size):
        """
        call back function of IB C++ API. This function will get tick size
        """
        self.log.notset(__name__ + '::tickSize: ' + str(reqId) + ", " + MSG_TABLE[tickType]
                        + ", size = " + str(size))
        if reqId in self.end_check_list.index:
            self.end_check_list.loc[reqId, 'status'] = 'Done'
        str_security = self.realTimePriceRequestedList.findByReqId(reqId)
        self.brokerService.setTickSize(TickSizeRecord(str_security, tickType, size))

    def tickSnapshotEnd(self, reqId):
        self.log.notset(__name__ + '::tickSnapshotEnd: ' + str(reqId))

    def tickString(self, reqId, field, value):
        """
        IB C++ API call back function. The value variable contains the last
        trade price and volume information. User show define in this function
        how the last trade price and volume should be saved
        RT_volume: 0 = trade timestamp; 1 = price_last,
        2 = size_last; 3 = record_timestamp
        """
        self.log.notset(__name__ + '::tickString: ' + str(reqId)
                        + 'field=' + str(field) + 'value=' + str(value))
        str_security = self.realTimePriceRequestedList.findByReqId(reqId)
        self.brokerService.setTickString(TickStringRecord(str_security, field, value))

    def updateAccountTime(self, tm):
        self.log.notset(__name__ + '::updateAccountTime:' + str(tm))

    def updateAccountValue(self, key, value, currency, accountCode):
        """
        IB callback function
        update account values such as cash, PNL, etc
        !!!!!!!! type(value) is STRING !!!!!!!!
        """
        self.log.notset(__name__ + '::updateAccountValue: key=%s value=%s currency=%s accountCode=%s'
                        % (key, str(value), currency, accountCode))
        if key in ['TotalCashValue', 'UnrealizedPnL', 'NetLiquidation', 'GrossPositionValue']:
            value = float(value)
        self.brokerService.setAccountValue(AccountValueRecord(key, value, currency, accountCode))

    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL,
                        accountCode):
        self.log.notset(
            __name__ + '::updatePortfolio: contract=%s position=%s marketPrice=%s marketValue=%s averageCost=%s unrealizedPNL=%s realizedPNL=%s accountCode=%s'
            % (str(contract), str(position), str(marketPrice), str(marketValue), str(averageCost), str(unrealizedPNL),
               str(realizedPNL), str(accountCode)))

        # Because IB does not callback position and updateAccountValues,
        # it needs to make fake calls to make sure the account info is correct
        # It is not correct, it will be fixed by the real call-backs
        self.position(accountCode, contract, position, averageCost)
