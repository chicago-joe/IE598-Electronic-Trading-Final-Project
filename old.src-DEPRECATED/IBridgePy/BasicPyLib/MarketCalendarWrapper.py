# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 00:24:07 2018

@author: IBridgePy@gmail.com
"""

if __name__ == '__main__':
    from FakeMarketCalendar import FakeMarketCalendar
    from MarketCalendar import MarketCalendar
else:
    from BasicPyLib.FakeMarketCalendar import FakeMarketCalendar
    from BasicPyLib.MarketCalendar import MarketCalendar


class MarketCalendarWrapper:
    def __init__(self, marketName='NYSE'):
        if marketName == 'Fake':
            self.marketCalendar = FakeMarketCalendar()
        else:
            self.marketCalendar = MarketCalendar(marketName)

    def getMarketCalendar(self):
        return self.marketCalendar

