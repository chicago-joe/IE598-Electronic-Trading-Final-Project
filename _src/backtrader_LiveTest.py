# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 01:07:51 2019

@author: 43739
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import pandas as pd
import backtrader as bt  # Import the backtrader platform


class StatisticalArbitrage(bt.Strategy):    # Create a Strategy
    params = (('exitbars', 1950),)
    
    def log(self, txt, dt=None):  # Logging function fot this strategy
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
        
    def notify_data(self, data, status, *args, **kwargs):
        # the data has switched to LIVE data
        if status == data.LIVE:
            pass                # TODO: do something here!
    
    def __init__(self):
        self.dataclose = self.datas[0].close  # Keep a reference to the "close" line in the data[0] dataseries
        self.order = None  # To keep track of pending orders and buy price/commission
        self.buyprice = None
        self.buycomm = None
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:  # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        
        if order.status in [order.Completed]:  # Check if an order has been completed
            if order.isbuy():  # Attention: broker could reject order if not enough cash
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            
            self.bar_executed = len(self)
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
    
    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])  # Simply log the closing price of the series from the reference
        if self.order:  # Check if an order is pending ... if yes, we cannot send a 2nd one
            return
        
        if not self.position:  # Check if we are in the market
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:  # current close less than previous close
                
                if self.dataclose[-1] < self.dataclose[-2]:  # previous close less than the previous close
                    
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])  # BUY, BUY, BUY!!! (with default parameters)
                    
                    self.order = self.buy()  # Keep track of the created order to avoid a 2nd order
        else:
            if len(self) >= (self.bar_executed + self.params.exitbars):  # Already in the market ... we might sell
                self.log('SELL CREATE, %.2f' % self.dataclose[0])  # SELL, SELL, SELL!!! (with all possible default parameters)
                
                self.order = self.sell()  # Keep track of the created order to avoid a 2nd order


# END setup
# -----------------------------------------------------------------------------------------------------------
# BEGIN algo

if __name__ == '__main__':
    cerebro = bt.Cerebro()  # create a Cerebro entity
    ibstore = bt.stores.IBStore(host='127.0.0.1', port=7497, clientId=1)
    cerebro.broker = ibstore.getbroker()
    cerebro.addstrategy(StatisticalArbitrage)  # add a strategy
    
    data1 = ibstore.getdata(dataname = 'RDS.A-STK-SMART-USD')
    data2 = ibstore.getdata(dataname = 'BP-STK-SMART-USD')
  
    # if above doesn't work, try direct usage:
    # data1 = bt.feeds.IBData(dataname = 'RDS.A-STK-SMART-USD')
    # data2 = bt.feeds.IBData(dataname = 'BP-STK-SMART-USD')

    
    #--------------------------------------------------------------------------------------------------------------
    # if we use the "ticks" timeframe (instaneous trading), we need to resample and compress the data
    # due to API limitations. The minimum unit supported by the API is (Seconds / 1) and RealTimeBars = (Seconds / 5)
    
    # data = ibstore.getdata(dataname = 'RDS.A-STK-SMART-USD',                  # If using instaneous tick data:
    #                        timeframe = bt.TimeFrame.Ticks,
    #                        compression = 1,                                   # 1 is the default
    #                        rtbar = True)                                      # use RealTimeBars
    
    #--------------------------------------------------------------------------------------------------------------
    # if using seconds as the timeframe..
    # data = ibstore.getdata(dataname = 'BP-STK-SMART-USD')
    
    # overwrites timeframe and compression of the data:
    # cerebro.resampledata(data, timeframe = bt.TimeFrame.Seconds, compression = 20)
    
    # This means that events to the system from the API will happen at most every 250 milliseconds.
    # This is possibly not important, because the system is only sending a bar to the strategy every 20 seconds
    
    # if our strategy uses any resampling / replaying methods like the above code, we need to adjust for small delays in the timecode
    # data = ibstore.getdata('BP', qcheck = 2.0, ....)        # increasing qcheck from the default 0.5 to 2.0 should solve this.
   
    
    # cerebro.adddata(data)  # add data feed to Cerebro
    
    cerebro.broker.setcash(100000.0)  # set desired cash start
    
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # add FixedSize sizer according to the stake
    
    cerebro.broker.setcommission(commission=0.001)  # set the commision = 0.1%
    
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  # print the starting conditions
    
    cerebro.run()  # Run over everything
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())  # Print out the final result
    
    cerebro.plot(start=datetime.date(2000, 1, 1), end=datetime.date(2020, 1, 31))



