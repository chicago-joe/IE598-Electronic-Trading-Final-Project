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

from broker_client_factory.RequestWrapper import RequestWrapper
import pandas as pd
import datetime as dt
import time
from IBridgePy.quantopian import from_security_to_contract
from IBridgePy.IbridgepyTools import from_arg_to_pandas_endCheckList
from IBridgePy.constants import LiveBacktest
from broker_factory.records_def import print_contract, print_IB_order
from sys import exit


class RequestImpl(RequestWrapper):
    def use_next_id(self):
        nextId = self.nextId
        self.nextId += 1
        return nextId

    def set_timer(self):
        """
        set self.timer_start to current time so as to start the timer
        """
        self.timer_start = dt.datetime.now()
        self.log.notset(__name__ + "::set_timer: " + str(self.timer_start))

    def check_timer(self, limit=1):
        """
        check_timer will check if time limit exceeded for certain
        steps, including: updated positions, get nextValidId, etc
        """
        self.log.notset(__name__ + '::check_timer:')
        timer_now = dt.datetime.now()
        change = (timer_now - self.timer_start).total_seconds()
        if change > limit:  # if time limit exceeded
            self.log.error(__name__ + '::check_timer: _request_data failed after ' + str(limit) + ' seconds')
            self.log.error(__name__ + '::check_timer: notDone items in self.end_check_list')
            tp = self.end_check_list[self.end_check_list['status'] != 'Done']
            self.log.error(str(tp))
            return True  # it is time to stop
        else:
            return False

    def check_if_real_time_price_requested(self, security):
        self.log.notset(__name__ + '::check_if_real_time_price_requested: security=%s' % (str(security),))
        return self.realTimePriceRequestedList.checkIfRequestedByStrSecurity(security.full_print())

    def _prepare_nextId(self, reqList):
        """
        !! index must be equal to reqID because it is easier to search reqId later
        Do NOT combine this function with from_arg_to_pandas_endCheckList because this function will be used again in
        _request_data when request fails
        TODO should not create a new reqList !!!
        """
        self.log.notset(__name__ + '::_prepare_nextId')
        newList = pd.DataFrame()
        for idx, row in reqList.iterrows():

            # when place a new order, the request does not have an orderId
            # Then, use nextId as orderId
            # When modify an existing order, orderId must be provided.
            if row['reqType'] == 'placeOrder':
                if row['reqData'].param['orderId'] is None:
                    row['reqData'].param['orderId'] = self.nextId
            newRow = pd.DataFrame({'reqId': self.nextId, 'status': row['status'],
                                   'followUp': bool(row['followUp']), 'reqData': row['reqData'],
                                   'reqType': row['reqType'], 'resendOnFailure': row['resendOnFailure']},
                                  index=[self.nextId])
            self.nextId += 1
            newList = newList.append(newRow)
        return newList

    def req_info_from_server_if_all_completed(self):
        self.log.notset(__name__ + '::req_info_from_server_if_all_completed')
        for idx in self.end_check_list.index:
            if self.end_check_list.loc[idx, 'status'] != 'Done':
                if self.end_check_list.loc[idx, 'followUp']:
                    return False
        return True

    def request_data(self, waitForFeedbackInSeconds, repeat, *args):
        """
        TODO: do not repeat 20181114
        input:
        request_data(
                     ReqData.reqPositions(),
                     ReqData.reqAccountUpdates(True, 'test'),
                     ReqData.reqAccountSummary(),
                     ReqData.reqIds(),
                     ReqData.reqHistoricalData(self.sybmol('SPY'),
                                               '1 day', '10 D', dt.datetime.now()),
                     ReqData.reqMktData(self.sybmol('SPY')),
                     ReqData.reqRealTimeBars(self.symbol('SPY')),
                     ReqData.reqContractDetails(self.symbol('SPY')),
                     ReqData.calculateImpliedVolatility(self.symbol('SPY'), 99.9, 11.1),
                     ReqData.reqAllOpenOrders(),
                     ReqData.cancelMktData(1),
                     ReqData.reqCurrentTime())
        """
        self.log.notset(__name__ + '::request_data: repeat=%s' % (str(repeat),))

        # Reset self.requestResults
        self.resetRequestResults()

        # change args to a pandas dataFrame
        reqList = from_arg_to_pandas_endCheckList(args)  # reqList is a pandas dataFrame, no real index yet
        reqList = self._prepare_nextId(reqList)  # reqList is a pandas dataFrame, indexed by reqId

        # send request to IB server
        self.req_info_from_server(reqList)

        # continuously check if all requests have received responses
        while not self.req_info_from_server_if_all_completed():
            if self.getRunningMode() == LiveBacktest.LIVE:
                self.log.debug(__name__ + '::request_data: sleep')
                time.sleep(0.5)
            self.processMessages()
            if self.check_timer(waitForFeedbackInSeconds):
                self.log.error(__name__ + '::request_data: Failed')
                for idx in reqList.index:
                    if reqList.loc[idx]['reqType'] == 'reqMktData':
                        self.log.error(__name__ + '::_request_data: reqData is not successful')
                        self.log.error(__name__ + '::_request_data: request market data failed for ' + str(
                            reqList.loc[idx]['reqData'].param['security']))
                        self.log.error(__name__ + '::_request_data: Market is not open??? EXIT')
                exit()
        self.log.debug(__name__ + '::request_data: All responses are received')
        self.log.debug(__name__ + '::request_data: COMPLETED')
        return list(reqList.index)  # a list of reqId

    def req_info_from_server(self, reqData):
        """
        pandas dataFrame: reqData
        """
        self.log.debug(__name__ + '::req_info_from_server: Request the following info to server')
        self.end_check_list = reqData
        # Because self.end_check_list is a pandas dataFrame, it cannot contain non-primitive values
        # so that self.end_check_list is needed to record call-back results, keyed by reqId.
        self.end_check_list_result = {}

        for idx in self.end_check_list.index:
            # Mark the request as Submitted
            self.end_check_list.loc[idx, 'status'] = 'Submitted'

            # Record all requests of this session to reqDataHist for further debug
            self.reqDataHist = self.reqDataHist.append(self.end_check_list.loc[idx])

            reqId = int(self.end_check_list.loc[idx, 'reqId'])
            followUp = self.end_check_list.loc[idx, 'followUp']
            reqType = self.end_check_list.loc[idx, 'reqType']
            self.log.debug(__name__ + '::req_info_from_server: reqId=%s followUp=%s reqType=%s' % (reqId, followUp, reqType))

            if self.end_check_list.loc[idx, 'reqType'] == 'reqPositions':
                self.log.debug(__name__ + '::req_info_from_server: requesting open positions info from IB')
                self.reqPositionsWrapper()  # request open positions

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqCurrentTime':
                self.log.debug(__name__ + '::req_info_from_server: requesting IB server time')
                self.reqCurrentTimeWrapper()  # request open positions

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqAllOpenOrders':
                self.log.debug(__name__ + '::req_info_from_server: requesting reqAllOpenOrders from IB')
                self.reqAllOpenOrdersWrapper()  # request all open orders

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqAccountUpdates':
                accountCode = self.end_check_list.loc[idx, 'reqData'].param['accountCode']
                subscribe = self.end_check_list.loc[idx, 'reqData'].param['subscribe']
                self.log.debug(
                    __name__ + '::req_info_from_server: requesting to update account=%s info from IB' % (accountCode,))
                self.reqAccountUpdatesWrapper(subscribe, accountCode)  # Request to update account info

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqAccountSummary':
                group = self.end_check_list.loc[idx, 'reqData'].param['group']
                tag = self.end_check_list.loc[idx, 'reqData'].param['tag']
                self.log.debug(
                    __name__ + '::req_info_from_server: reqAccountSummary account=%s, reqId=%i' % (group, reqId))
                self.reqAccountSummaryWrapper(reqId, group, tag)

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqIds':
                self.log.debug(__name__ + '::req_info_from_server: requesting reqIds')
                self.reqIdsWrapper()

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqHistoricalData':
                security = self.end_check_list.loc[idx, 'reqData'].param['security']
                endTime = self.end_check_list.loc[idx, 'reqData'].param['endTime']
                goBack = self.end_check_list.loc[idx, 'reqData'].param['goBack']
                barSize = self.end_check_list.loc[idx, 'reqData'].param['barSize']
                whatToShow = self.end_check_list.loc[idx, 'reqData'].param['whatToShow']
                useRTH = self.end_check_list.loc[idx, 'reqData'].param['useRTH']
                formatDate = self.end_check_list.loc[idx, 'reqData'].param['formatDate']
                self.log.debug(__name__ + '::req_info_from_server:%s %s %s %s %s %s %s %s' % (str(reqId),
                                                                                              security.full_print(),
                                                                                              str(endTime), str(goBack),
                                                                                              str(barSize),
                                                                                              str(whatToShow),
                                                                                              str(useRTH),
                                                                                              str(formatDate)))
                self.end_check_list_result[reqId] = pd.DataFrame()
                self.reqHistoricalDataWrapper(reqId,
                                              from_security_to_contract(security),
                                              endTime,
                                              goBack,
                                              barSize,
                                              whatToShow,
                                              useRTH,
                                              formatDate)
                if self.getRunningMode() == LiveBacktest.LIVE:
                    self.log.debug(__name__ + '::req_info_from_server: sleep')
                    time.sleep(0.1)

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqMktData':
                security = self.end_check_list.loc[idx, 'reqData'].param['security']
                genericTickList = self.end_check_list.loc[idx, 'reqData'].param['genericTickList']
                snapshot = self.end_check_list.loc[idx, 'reqData'].param['snapshot']
                self.log.debug(__name__ + '::req_info_from_server: Request realTimePrice %s %s %s %s'
                               % (str(reqId), security.full_print(), str(genericTickList), str(snapshot)))

                # put security and reqID in dictionary for fast access
                # it is keyed by both security and reqId
                self.realTimePriceRequestedList.addReqIdAndStrSecurity(reqId, security.full_print())

                self.reqMktDataWrapper(reqId, from_security_to_contract(security),
                                       genericTickList, snapshot)  # Send market data request to IB server

            elif self.end_check_list.loc[idx, 'reqType'] == 'cancelMktData':
                security = self.end_check_list.loc[idx, 'reqData'].param['security']
                reqId = self.realTimePriceRequestedList.findByStrSecurity(security.full_print())
                self.log.debug(__name__ + '::req_info_from_server: cancelMktData: '
                               + str(security) + ' '
                               + 'reqId=' + str(reqId))
                self.cancelMktDataWrapper(reqId)
                self.realTimePriceRequestedList.deleteReqIdAndStrSecurity(reqId, security.full_print())

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqRealTimeBars':
                security = self.end_check_list.loc[idx, 'reqData'].param['security']
                barSize = self.end_check_list.loc[idx, 'reqData'].param['barSize']
                whatToShow = self.end_check_list.loc[idx, 'reqData'].param['whatToShow']
                useRTH = self.end_check_list.loc[idx, 'reqData'].param['useRTH']
                self.realTimePriceRequestedList.addReqIdAndStrSecurity(reqId, security.full_print())
                self.log.debug(__name__ + '::req_info_from_server:requesting realTimeBars: '
                               + str(security) + ' '
                               + 'reqId=' + str(reqId))
                self.reqRealTimeBarsWrapper(reqId,
                                            from_security_to_contract(security),
                                            barSize, whatToShow, useRTH)  # Send market data request to IB server

            elif self.end_check_list.loc[idx, 'reqType'] == 'placeOrder':
                """
                Ending label is IBCpp::callBacks::orderStatus
                """
                orderId = int(self.end_check_list.loc[idx, 'reqData'].param['orderId'])
                contract = self.end_check_list.loc[idx, 'reqData'].param['contract']
                order = self.end_check_list.loc[idx, 'reqData'].param['order']
                self.log.info('PlaceOrder orderId = %s;\n'
                              'accountCode = %s;\n'
                              'security = %s;\n'
                              'order = %s'
                              % (str(orderId), order.account, print_contract(contract), print_IB_order(order)))
                self.placeOrderWrapper(orderId, contract, order)

                # Record orderId <--> accountCode,
                self.orderIdToAccountCode[orderId] = order.account

                self.setRequestResults(reqId, orderId)

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqContractDetails':
                security = self.end_check_list.loc[idx, 'reqData'].param['security']
                self.reqContractDetailsWrapper(reqId, from_security_to_contract(security))
                self.end_check_list_result[reqId] = pd.DataFrame()  # prepare for the return results
                self.log.debug(__name__ + '::req_info_from_server: requesting contractDetails '
                               + str(security) + ' reqId=' + str(reqId))

            elif self.end_check_list.loc[idx, 'reqType'] == 'calculateImpliedVolatility':
                security = float(self.end_check_list.loc[idx, 'reqData'].param['security'])
                optionPrice = float(self.end_check_list.loc[idx, 'reqData'].param['optionPrice'])
                underPrice = float(self.end_check_list.loc[idx, 'reqData'].param['underPrice'])

                # put security and reqID in dictionary for fast access
                # it is keyed by both security and reqId
                self.realTimePriceRequestedList.addReqIdAndStrSecurity(reqId, security.full_print())

                self.calculateImpliedVolatilityWrapper(reqId,
                                                       from_security_to_contract(security),
                                                       optionPrice,
                                                       underPrice)
                self.log.debug(__name__ + '::req_info_from_server: calculateImpliedVolatility: '
                               + str(security) + ' reqId=' + str(reqId)
                               + ' optionPrice=' + str(optionPrice)
                               + ' underPrice=' + str(underPrice))

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqScannerSubscription':
                subscription = self.end_check_list.loc[idx, 'reqData'].param['subscription']
                self.end_check_list_result[reqId] = pd.DataFrame()  # prepare for the return results
                self.reqScannerSubscriptionWrapper(reqId, subscription)
                self.log.debug(__name__ + '::req_info_from_server:reqScannerSubscription: %s %s % s'
                               % (subscription.instrument, subscription.locationCode, subscription.scanCode))

                # Need to upgrade IBCpp
                # tagValueList = self.end_check_list.loc[idx, 'reqData'].param['tagValueList']
                # self.reqScannerSubscription(reqId, subscription, tagValueList)
                # self.log.debug(__name__ + '::req_info_from_server:reqScannerSubscription:'
                #               + ' subscription=' + subscription.full_print() + ' tagValueList=' + str(tagValueList))

            elif self.end_check_list.loc[idx, 'reqType'] == 'cancelScannerSubscription':
                tickerId = self.end_check_list.loc[idx, 'reqData'].param['tickerId']
                self.cancelScannerSubscriptionWrapper(tickerId)
                self.log.debug(
                    __name__ + '::req_info_from_server:cancelScannerSubscription: request to cancel scannerReqId = %s'
                    % (tickerId,))

            elif self.end_check_list.loc[idx, 'reqType'] == 'cancelOrder':
                """
                Ending label is IBCpp::callBacks::error: errorCode = 10148
                """
                orderId = self.end_check_list.loc[idx, 'reqData'].param['orderId']
                self.cancelOrderWrapper(orderId)
                self.log.debug(
                    __name__ + '::req_info_from_server:cancelOrder: request to cancel orderId = %s' % (orderId,))
                self.log.info('cancelOrder orderId=%s' % (orderId,))

            elif self.end_check_list.loc[idx, 'reqType'] == 'reqScannerParameters':
                self.reqScannerParametersWrapper()
                self.log.debug(__name__ + '::req_info_from_server:reqScannerParameters')
            else:
                self.log.error(
                    __name__ + '::req_info_from_server: EXIT, cannot handle reqType=' + self.end_check_list.loc[
                        idx, 'reqType'])
                self.end()
        self.set_timer()
