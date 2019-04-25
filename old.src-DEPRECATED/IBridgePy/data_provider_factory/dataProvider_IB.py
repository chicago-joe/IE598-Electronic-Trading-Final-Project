# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""

from .data_provider import DataProvider
from sys import exit
from IBridgePy.quantopian import ReqData
import datetime as dt
import pytz
from BasicPyLib.BasicTools import utc_in_seconds_to_dt


class IB(DataProvider):
    @property
    def name(self):
        return 'InteractiveBroker'

    def ingest_hists(self, loadingPlan):
        self.log.debug(__name__ + '::ingest_hists: loadingPlan=%s client=%s' % (loadingPlan, self.dataProviderClient))
        self.dataProviderClient.connectWrapper()
        for plan in loadingPlan.finalPlan:
            str_security = plan.security.full_print()
            barSize = plan.barSize
            if str_security not in self.hist:
                self.hist[str_security] = {}
            if barSize not in self.hist[str_security]:
                self.hist[str_security][barSize] = {}
            self.hist[str_security][barSize] = self._get_hist_from_IB(plan)
            print('ingested hist of security=%s barSize=%s' % (str_security, barSize))
            print('1st line=%s' % (utc_in_seconds_to_dt(self.hist[str_security][barSize].index[0], timezoneName='US/Eastern')))
            print('last line=%s' % (utc_in_seconds_to_dt(self.hist[str_security][barSize].index[-1], timezoneName='US/Eastern')))

        self.dataProviderClient.disconnectWrapper()
        if len(self.hist) == 0:
            self.log.debug(__name__ + '::ingest_hists: EXIT, loading errors')
            exit()

    def _get_hist_from_IB(self, plan):
        self.log.debug(__name__ + '::_get_hist_from_IB')
        endTime = plan.endTime.astimezone(pytz.timezone('UTC'))
        endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string

        # the return of request_data is reqId.
        # To get the content of hist, call brokerService::request_historical_data
        reqIds = self.dataProviderClient.request_data(30, 0, ReqData.reqHistoricalData(plan.security,
                                                                                       plan.barSize,
                                                                                       plan.goBack,
                                                                                       endTime,
                                                                                       'ASK'))

        # only reqId is returned
        # The content of hist = self.brokerClient.requestResults[]
        return self.dataProviderClient.requestResults[reqIds[0]]
