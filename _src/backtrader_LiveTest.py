# -*- coding: utf-8 -*-
"""
Statistical Arbitrage Trading via InteractiveBrokers API
An Algorithmic Trading Implementation in Python

Created by Ruozhong Yang and Joseph Loss on 4/25/2019

MS Financial Engineering at the University of Illinois, Urbana-Champaign
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)
import argparse, datetime, itertools
import backtrader as bt  # Import the backtrader platform
# import bt.utils import flushfile 
import pandas as pd
import numpy as np

# -------------------------------------------------------------------------------------------------------------------
# EXTREMELY IMPORTANT!!!! BROKER AND API RESTRICTIONS ARE LISTED BELOW!!!!

"""
RESTRICTIONS:
1. Cash and Value Reporting
    - Where the internal backtrader broker simulation makes a calculation of value (net liquidation value)
      and cash before calling the strategy next method, the same cannot be guaranteed with a live broker.
      
    - If the values were requested, the execution of next could be delayed until the answers arrive
    
    - The broker may not yet have calculated the values
    
    - Backtrader tells TWS to provide the updated values as soon as they are changed,
      but it doesn’t know when the messages will arrive.
    
    - The values reported by the getcash and getvalue methods of IBBroker
      are always the latest values received from IB.

2. Position Restrictions
    - Backtrader uses the Position (price and size) of an asset reported by TWS.
      Internal calculations could be used following order execution and order status messages,
      but if some of these messages were missed (sockets sometimes lose packets) the calculations would NOT follow.

3. Trading Strategy Must Account for ALL Open Positions from the previous trading period.
    - If upon connecting to TWS, the asset on which trades will be executed already has an open position,
      the calculation of trades made by the strategy will NOT WORK as usual because of the initial offset.
    - The mathematical model of the strategy must account for any previously-opened positions from prior trading days.

4. Portfolio Value is Reported in Domestic Currency ONLY.
    - A further restriction is that the values are reported in the base currency of the account,
      even if values for more currencies are available. This is a design choise.
"""

# -------------------------------------------------------------------------------------------------------------------
# BEGIN STRATEGY DESIGN:

class StatisticalArbitrage(bt.Strategy):  # Create a Strategy
    params = (('exitbars', 1950),)
    
    def log(self, txt, dt=None):  # Logging function fot this strategy
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
    
    def notify_data(self, data, status, *args, **kwargs):
        # the data has switched to LIVE data
        if status == data.LIVE:
            pass  # TODO: do something here!
    
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
# ----------------------------------------------------------------------------------------------------------------

# RUN TRADING STRATEGY:
if __name__ == '__main__':
    cerebro = bt.Cerebro()  # create a Cerebro entity
    ibstore = bt.stores.IBStore(host='127.0.0.1', port=7497, clientId=1)
    cerebro.broker = ibstore.getbroker()
    
    data1 = ibstore.getdata(dataname='RDS.A-STK-SMART-USD')
    data2 = ibstore.getdata(dataname='BP-STK-SMART-USD')
    # cerebro.adddata(data)  # add data feed to Cerebro
    
    
    # if above doesn't work, try direct usage:
    # data1 = bt.feeds.IBData(dataname = 'RDS.A-STK-SMART-USD')
    # data2 = bt.feeds.IBData(dataname = 'BP-STK-SMART-USD')
    
    # --------------------------------------------------------------------------------------------------------------
    # if we use the "ticks" timeframe (instaneous trading), we need to resample and compress the data
    # due to API limitations. The minimum unit supported by the API is (Seconds / 1) and RealTimeBars = (Seconds / 5)
    
    # data = ibstore.getdata(dataname = 'RDS.A-STK-SMART-USD',                  # If using instaneous tick data:
    #                        timeframe = bt.TimeFrame.Ticks,
    #                        compression = 1,                                   # 1 is the default
    #                        rtbar = True)                                      # use RealTimeBars
    
    # --------------------------------------------------------------------------------------------------------------
    # if using seconds as the timeframe..
    # data = ibstore.getdata(dataname = 'BP-STK-SMART-USD')
    
    # overwrites timeframe and compression of the data:
    # cerebro.resampledata(data, timeframe = bt.TimeFrame.Seconds, compression = 20)
    
    # This means that events to the system from the API will happen at most every 250 milliseconds.
    # This is possibly not important, because the system is only sending a bar to the strategy every 20 seconds
    
    # if our strategy uses any resampling / replaying methods like the above code, we need to adjust for small delays in the timecode
    # data = ibstore.getdata('BP', qcheck = 2.0, ....)        # increasing qcheck parameter from 0.5 to 2.0 should solve issue

    
    cerebro.addstrategy(StatisticalArbitrage)  # add a strategy
    
    cerebro.broker.setcash(100000.0)  # set desired cash start
    
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # add FixedSize sizer according to the stake
    
    cerebro.broker.setcommission(commission=0.001)  # set the commision = 0.1%
    
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  # print the starting conditions
    
    cerebro.run()  # Run over everything
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())  # Print out the final result
    
    cerebro.plot(start=datetime.date(2000, 1, 1), end=datetime.date(2020, 1, 31))



# ----------------------------------------------------------------------------------------------------------------


"""
NOTE ON ORDER TYPES:

Stop triggering is done following different strategies by IB. backtrader does not modify the default setting which is 0:

0 - the default value. The "double bid/ask" method will be used for orders for OTC stocks and US options.
All other orders will use the "last" method.

If the user wishes to modify this, extra **kwargs can be supplied to buy and sell following the IB documentation.
For example inside the next method of a strategy:
    
    def next(self):
        # some logic before
        self.buy(data, m_triggerMethod=2)

*This has changed the policy to 2, the “last” method, where stop orders are triggered based on the last price.

Please consult the IB API docs for any further clarification on stop triggering
"""


