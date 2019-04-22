# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 00:03:22 2018

@author: IBridgePy@gmail.com
"""


class FakeMarketCalendar:
    def __init__(self):
        self.marketCalendarName = 'fakeMarketCalendar'

    def trading_day(self, timeNow):
        """
        return True if day is a trading day
        """
        return True

    def get_market_open_close_time(self, aDateTime):
        open = aDateTime.replace(hour=0, minute=0, second=0)
        close = aDateTime.replace(hour=23, minute=59, second=59)
        return open, close

    def nth_trading_day_of_month(self, aDay):
        return aDay.day, aDay.day - 30

    def nth_trading_day_of_week(self, aDay):
        return aDay.weekday(), aDay.weekday() - 7


if __name__ == '__main__':
    import datetime as dt
    c = FakeMarketCalendar()
    print(c.get_market_open_close_time(dt.datetime.now()))