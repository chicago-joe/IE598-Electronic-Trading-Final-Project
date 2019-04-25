# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""

import bisect
from sys import exit

import pandas as pd
import pytz

from BasicPyLib.BasicTools import dt_to_utc_in_seconds, utc_in_seconds_to_dt
from IBridgePy.IbridgepyTools import calculate_startTimePosition


class DataProvider:
    def __init__(self, userConfig):
        # these are needed to construct an instance
        self.log = userConfig.log
        self.dataProviderClient = userConfig.dataProviderClient
        self.showTimeZone = pytz.timezone(userConfig.showTimeZoneName)

        # The format of self.hist should be self.hist[str_security][barSize]
        # self.hist should be loaded by self.dataProvider.get_historical_data()
        self.hist = {}

    @property
    def name(self):
        """
        Name of the data provider

        :return: string name
        """
        raise NotImplementedError()

    def ingest_hists(self, loadingPlan):
        # loadingPlan Must be data_provider_factor::data_loading_plan::LoadingPlan
        raise NotImplementedError

    def get_one_real_time_price(self, str_security, timeNow, tickType, freq='1 min'):
        """

        :param freq:
        :param str_security:
        :param timeNow:
        :param tickType: string ONLY
        :return:
        """
        # broker_client_factory::ClientLocalBroker::processMessagesWrapper use str_security
        self.log.debug(__name__ + '::get_one_real_time_price: str_security=%s timeNow=%s' % (str_security, timeNow))

        if str_security not in self.hist:
            self.log.error(__name__ + '::get_one_real_time_prices: EXIT, Do not have hist data for str_security=%s '
                                      'dataProvider=%s' % (str_security, self))
            for ct in self.hist:
                print(ct)
            exit()
        if freq not in self.hist[str_security]:
            self.log.error(__name__ + '::get_one_real_time_price: EXIT, hist of %s does not have freq=%s'
                           % (str_security, freq))
            exit()
        timeNow = int(dt_to_utc_in_seconds(timeNow))
        # print(timeNow)
        if timeNow in self.hist[str_security][freq].index:
            # time1st = utc_in_seconds_to_dt(self.hist[str_security]['1 min'].index[0]).astimezone(pytz.timezone('UTC'))
            # timeLast = utc_in_seconds_to_dt(self.hist[str_security]['1 min'].index[-1]).astimezone(pytz.timezone('UTC'))
            # print(utc_in_seconds_to_dt(timeNow).astimezone(pytz.timezone('US/Eastern')), time1st, timeLast)
            return self.hist[str_security][freq].loc[timeNow, 'open']
        else:
            timeNow = utc_in_seconds_to_dt(timeNow).astimezone(self.showTimeZone)  # default is UTC
            time1st = utc_in_seconds_to_dt(self.hist[str_security][freq].index[0]).astimezone(self.showTimeZone)
            timeLast = utc_in_seconds_to_dt(self.hist[str_security][freq].index[-1]).astimezone(self.showTimeZone)
            self.log.error(__name__ + '::get_one_real_time_prices: loaded hist does not have timeNow=%s' % (str(timeNow),))
            self.log.error(__name__ + '::get_one_real_time_prices: loaded hist of security=%s from %s to %s'
                           % (str_security,  time1st, timeLast))
            raise AssertionError  # AssertionError will be caught by broker_client_factory::ClientLocalBroker.py::processMessagesWrapper

    def get_real_time_price(self, str_security, timeNow, tickType):
        self.log.notset(__name__ + '::get_real_time_price: str_security=%s timeNow=%s tickType=%s' % (
            str_security, str(timeNow), str(tickType)))
        if isinstance(tickType, list):
            ans = []
            for ct in tickType:
                ans.append(self.get_one_real_time_price(str_security, timeNow, ct))
            return ans
        else:
            return self.get_one_real_time_price(str_security, timeNow, tickType)

    # !!! the returned hist will only be used for backtester.!!!
    def get_historical_data(self, security, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        """

        :param security: IBridgePy::quantopian::Security
        :param endTime: request's ending time with format yyyyMMdd HH:mm:ss {TMZ} ---from IB api doc
        :param goBack:
        :param barSize: string 1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins,
                                30 mins, 1 hour, 1 day
        :param whatToShow:
        :param useRTH:
        :param formatDate:
        :return:
        """
        global endTimePosition, startTimePosition
        self.log.debug(__name__ + '::get_historical_data: endTime=%s goBack=%s barSize=%s' % (endTime, goBack, barSize))
        hist = self.hist[security.full_print()][barSize]
        if not isinstance(hist, pd.DataFrame):
            self.log.error(__name__ + '::get_historical_data: EXIT, hist is empty')
            exit()

        startTimePositionDelta, endTime = calculate_startTimePosition(endTime, goBack, barSize)

        # look for the location of endTime in hist.index
        if endTime not in hist.index:
            endTimePosition = bisect.bisect_left(hist.index, endTime)
            if endTimePosition >= len(hist.index):
                endTimePosition -= 1

        startTimePosition = max(endTimePosition - startTimePositionDelta, 0)
        if startTimePosition < endTimePosition:
            return hist.iloc[startTimePosition:endTimePosition]
        else:
            self.log.error(__name__ + '::get_historical_data: Incorrect endTime=%s or goBack=%s when barSize=%s'
                           % (endTime, goBack, barSize))
            exit()
