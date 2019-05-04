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

# run the download and merge program
os.system("C:\\Users\\jloss\\PyCharmProjects\\IE598_Final_Project\\_src\\download_merge_output_tiingo_v4.0.py")


class TestStrategy(bt.Strategy):    # Create a Strategy
    params = (('exitbars', 1950),)
    
    def log(self, txt, dt=None):  # Logging function fot this strategy
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
    
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


# -----------------------------------------------------------------------------------------
if __name__ == '__main__':
    cerebro = bt.Cerebro()  # create a Cerebro entity
    
    cerebro.addstrategy(TestStrategy)  # add a strategy
    
    # Datas are in a subfolder of the samples.
    # Need to find where the script is because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    csv = '$C:\\Users\\43739\\OneDrive\\us\\2019 spring\\paper trading\\intra_aapl_2018_1min.csv$'
    datapath = os.path.join(modpath, csv)
    dataframe = pd.read_csv(datapath, parse_dates=True, index_col=0)
    
    data = bt.feeds.PandasData(dataname=dataframe)  # create a data feed
    
    cerebro.adddata(data)  # add data feed to Cerebro
    
    cerebro.broker.setcash(100000.0)  # set desired cash start
    
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # add FixedSize sizer according to the stake
    
    cerebro.broker.setcommission(commission=0.001)  # set the commision = 0.1%
    
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  # print the starting conditions
    
    cerebro.run()  # Run over everything
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())  # Print out the final result
    
    cerebro.plot(start=datetime.date(2000, 1, 1), end=datetime.date(2020, 1, 31))



