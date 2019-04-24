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


# add a data feed
ibstore = bt.stores.IBStore(port=7496, clientId = 1)
#data = ibstore.getdata(dataname='EUR.USD-CASH-IDEALPRO')
data = ibstore.reqMktData(dataname='AAPL-STK-SMART')

if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # add a strategy
    cerebro.addstrategy(TestStrategy)



    #add the data feed to cerebro
    cerebro.adddata(data)

    cerebro.broker.set_cash(100000.0)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())