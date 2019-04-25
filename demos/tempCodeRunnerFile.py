#
#
#
#
from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime     # for datetime objects
import os.path      # manage paths
import sys          # to find out the script name
import backtrader as bt


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
        # simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        if self.dataclose[0] < self.dataclose[-1]:
            # previous close less than the previous close
            # BUY BUY BUY!!! (with all possible default params)
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.buy()



if __name__ == '__main__':
    # create a cerebro entity
    cerebro = bt.Cerebro()

    # add a strategy
    cerebro.addstrategy(TestStrategy)

    # data paths
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'C:/Users/jloss/Downloads/AAPL.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2018, 1, 1),
        # Do not pass values after this date
        todate=datetime.datetime(2020, 1, 1),
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