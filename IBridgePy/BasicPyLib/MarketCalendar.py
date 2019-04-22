# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 04:56:16 2018

@author: IBridgePy@gmail.com
"""
import numpy as np
import datetime as dt
import pandas as pd
import pytz
from pandas.tseries.offsets import MonthEnd
import BasicPyLib.pandas_market_calendars as mcal


class MarketCalendar:
    def __init__(self, marketName='NYSE'):
        self.marketCalendarName = marketName
        self.marketName = mcal.get_calendar(marketName)

    # override
    def trading_day(self, aDatetime):
        """
        Check if a datetime is a trading day based on marketName
        output:
            True: It is a trading day.
        """
        # print(__name__ + '::trading_day: %s' % (aDatetime,))
        if isinstance(aDatetime, dt.datetime):
            aDatetime = aDatetime.date()
        if np.is_busday(aDatetime):
            return not (np.datetime64(aDatetime) in self.marketName.holidays().holidays)
        else:
            return False

    # override
    def get_market_open_close_time(self, aDatetime):
        if self.trading_day(aDatetime):
            sch = self.marketName.schedule(start_date=aDatetime, end_date=aDatetime)
            return sch.iloc[0]['market_open'], sch.iloc[0]['market_close']
        else:
            return None, None

    def nth_trading_day_of_month(self, aDay):
        """
        1st trading day of month is 0
        last trading day of month is -1
        @param aDay: dt.date
        @result: list [nth trading day in a month, reverse location in a month]
        """
        if type(aDay) == dt.datetime:
            aDay = aDay.date()
        monthStartDate = aDay.replace(day=1)
        monthEndDate = (aDay+MonthEnd(0)).date()  # change pd.TimeStampe to dt.date
        ls_validDays = self.marketName.valid_days(start_date=monthStartDate, end_date=monthEndDate)
        if pd.Timestamp(aDay) in ls_validDays:
            x = ls_validDays.get_loc(pd.Timestamp(aDay))
            return [x, x - len(ls_validDays)]
        else:
            return None

    def nth_trading_day_of_week(self, aDay):
        """
        1st trading day of week is 0
        last trading day of week is -1
        @param aDay: dt.date
        @result: list [nth trading day in a week, reverse location in a week]
        """
        if type(aDay) == dt.datetime:
            aDay = aDay.date()
        tmp = aDay.weekday()
        weekStartDate = aDay - dt.timedelta(days=tmp)
        weekEndDate = weekStartDate + dt.timedelta(days=4)
        ls_validDays = self.marketName.valid_days(start_date=weekStartDate, end_date=weekEndDate)
        if pd.Timestamp(aDay) in ls_validDays:
            x = ls_validDays.get_loc(pd.Timestamp(aDay))
            return [x, x - len(ls_validDays)]
        else:
            return None

    def get_params_of_a_daytime(self, dateTime):
        """
        return 4 parameters to fit IBrigePy requirments
            1. nth_trading_day_of_month, two int, for example [21,-1]
            2. nth_trading_day_of_week, two int, for example [3, -2]
            3. int the hour of the dayTime
            4. int the minute of the dayTime
        """
        return (self.nth_trading_day_of_month(dateTime),
                self.nth_trading_day_of_week(dateTime),
                dateTime.hour,
                dateTime.minute)

    def get_early_closes(self, start_date, end_date):
        sch = self.marketName.schedule(start_date=start_date, end_date=end_date)
        return self.marketName.early_closes(sch)


if __name__ == '__main__':
    #print ('start')
    #print(get_trading_close_holidays(dt.date(2017,4,1), dt.date(2017,4,30)))
    #print(trading_day(dt.date(2017,9,1)))
    #print (nth_trading_day_of_week(dt.date(2017,11,30)))
    #print (nth_trading_day_of_month(dt.date(2017,9,1)))
    #print (count_trading_days(dt.date(2017,5,1), dt.date(2017,5,31)))
    #print (dt.date(2017,4,13)+MonthEnd(1))
    #print (count_trading_days(dt.date(2017,4,1), dt.date(2017,4,13)+MonthEnd(1)))
    #print (count_trading_days_in_a_month(dt.date(2017,5,13)))
    #print (count_trading_days_in_a_week(dt.date(2017,6,1)))
    #print (get_params_of_a_daytime(dt.datetime.now()))
    #print (get_params_of_a_daytime(dt.datetime(2017,5,30,12,30)))

    a = pytz.timezone('US/Eastern').localize(dt.datetime(2017, 11, 30, 17, 0))
    c = MarketCalendar('ICE')
    #print(c.trading_day(dt.date(2017, 8, 1)))
    #print(c.trading_day(dt.datetime(2017, 8, 1)))
    print(c.get_market_open_close_time(a))
    #print (c.nth_trading_day_of_month(dt.date(2017,11,30)))
    #print (c.nth_trading_day_of_week(dt.date(2017,11,30)))
    print(c.get_params_of_a_daytime(a))

    #d = pytz.timezone('US/Eastern').localize(dt.datetime(2018, 1, 1, 9, 0))
    #e = pytz.timezone('US/Eastern').localize(dt.datetime(2020, 12, 31, 17, 0))
    #print(c.get_early_closes(d, e))
