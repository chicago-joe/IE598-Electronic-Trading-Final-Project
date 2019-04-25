#
#
#
#
from __future__ import (absolute_import, division, print_function, unicode_literals)

import datetime     # for datetime objects
import os.path      # manage paths
import sys          # to find out the script name
import backtrader as bt
import pandas as pd
from iexfinance.stocks import get_historical_intraday
import tiingo


# import requests
# headers = {
#     'Content-Type': 'application/json'
# }
# requestResponse = requests.get("https://api.tiingo.com/iex/?tickers=rsd-a,bpl&token=c552a39f0066da5ba3fa00fc31dcd39e9528a33f&startDate=2017-01-01&endDate=2018-04-23&resampleFreq=60min", headers=headers)
# RDSA_1y60m = pd.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/rdsa-1yr-60min-intraday.json')
# RDSA_1y60m = pd.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/rdsa-1yr-60min-intraday.json')
# import json
# json.load(RDSA_1y60m)
# print(RDSA_1y60m)
# print(requestResponse.json())

# API Data Feeds: 
# https://api.tiingo.com/iex/BP/prices?token=pk_bcc0fe04ded749a4a0693e4ffd87ad16&startDate=2017-01-01&endDate=2018-04-23&resampleFreq=60min


# import JSON Data
RDSA_1y60m = pd.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/rdsa-1yr-60min-intraday.json')
RDSA_2y240m = pd.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/rdsa-2yr-240min-intraday.json')
BP_1y60m = pd.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/bp-1yr-60min-intraday.json')
BP_2y240m = pd.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/bp-2yr-240min-intraday.json')
print(BP_1y60m)

# from iexfinance import reference
# reference.output_format = 'json'

# create a strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        '''logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        if self.dataclose[0] < self.dataclose[-1]:
            # current close less than previous close

            if self.dataclose[-1] < self.dataclose[-2]:
                # previous close less than the previous close

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.buy()



if __name__ == '__main__':
    # create a cerebro entity
    cerebro = bt.Cerebro()

    # add a strategy
    cerebro.addstrategy(TestStrategy)

    # data paths
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # datapath = os.path.join(modpath, 'C:/Users/jloss/Downloads/AAPL.csv')
    datapath = os.path.join(modpath, 'C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/rdsa-1yr-60min-intraday.json')
    

    # Create a Data Feed
    data = bt.feeds.GenericCSV(
        dataname = RDSA_1y60m,
        fromdate = datetime.datetime(2018,4,23))


    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2018, 4, 23),
        # Do not pass values after this date
        todate=datetime.datetime(2019, 4, 23),
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    