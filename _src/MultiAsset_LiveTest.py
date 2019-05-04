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

class TestStrategy(bt.Strategy):
    params = dict(
            smaperiod = 5,
            trade = True,
            stake = 10,
            exectype = bt.Order.Market,
            stopafter = 0,
            valid = 0,
            cancel = 0,
            donotsell = False,

    )

    def __init__(self):
        # To control operation entries
        self.orderid = list()
        self.order = None

        self.counttostop = 0
        self.datastatus = 0

        # Create SMA on 2nd data
        self.sma = bt.indicators.MovAv.SMA(self.data, period = self.p.smaperiod)

        print('--------------------------------------------------')
        print('Strategy Created')
        print('--------------------------------------------------')

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE:
            self.counttostop = self.p.stopafter
            self.datastatus = 1

    def notify_store(self, msg, *args, **kwargs):
        print('*' * 5, 'STORE NOTIF:', msg)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Cancelled, order.Rejected]:
            self.order = None

        print('-' * 50, 'ORDER BEGIN', datetime.datetime.now())
        print(order)
        print('-' * 50, 'ORDER END')

    def notify_trade(self, trade):
        print('-' * 50, 'TRADE BEGIN', datetime.datetime.now())
        print(trade)
        print('-' * 50, 'TRADE END')

    def prenext(self):
        self.next(frompre = True)

    def next(self, frompre = False):
        txt = list()
        txt.append('%04d' % len(self))
        dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
        txt.append('%s' % self.data.datetime.datetime(0).strftime(dtfmt))
        txt.append('{}'.format(self.data.open[0]))
        txt.append('{}'.format(self.data.high[0]))
        txt.append('{}'.format(self.data.low[0]))
        txt.append('{}'.format(self.data.close[0]))
        txt.append('{}'.format(self.data.volume[0]))
        txt.append('{}'.format(self.data.openinterest[0]))
        txt.append('{}'.format(self.sma[0]))
        print(', '.join(txt))

        if len(self.datas) > 1:
            txt = list()
            txt.append('%04d' % len(self))
            dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
            txt.append('%s' % self.data1.datetime.datetime(0).strftime(dtfmt))
            txt.append('{}'.format(self.data1.open[0]))
            txt.append('{}'.format(self.data1.high[0]))
            txt.append('{}'.format(self.data1.low[0]))
            txt.append('{}'.format(self.data1.close[0]))
            txt.append('{}'.format(self.data1.volume[0]))
            txt.append('{}'.format(self.data1.openinterest[0]))
            txt.append('{}'.format(float('NaN')))
            print(', '.join(txt))

        if self.counttostop:  # stop after x live lines
            self.counttostop -= 1
            if not self.counttostop:
                self.env.runstop()
                return

        if not self.p.trade:
            return

        if self.datastatus and not self.position and len(self.orderid) < 1:
            self.order = self.buy(size = self.p.stake,
                                  exectype = self.p.exectype,
                                  price = round(self.data0.close[0] * 0.90, 2),
                                  valid = self.p.valid)

            self.orderid.append(self.order)
        elif self.position.size > 0 and not self.p.donotsell:
            if self.order is None:
                self.order = self.sell(size = self.p.stake // 2,
                                       exectype = bt.Order.Market,
                                       price = self.data0.close[0])

        elif self.order is not None and self.p.cancel:
            if self.datastatus > self.p.cancel:
                self.cancel(self.order)

        if self.datastatus:
            self.datastatus += 1

    def start(self):
        if self.data0.contractdetails is not None:
            print('Timezone from ContractDetails: {}'.format(
                    self.data0.contractdetails.m_timeZoneId))

        header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume',
                  'OpenInterest', 'SMA']
        print(', '.join(header))

        self.done = False


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()

    storekwargs = dict(
            host = args.host, port = args.port,
            clientId = args.clientId, timeoffset = not args.no_timeoffset,
            reconnect = args.reconnect, timeout = args.timeout,
            notifyall = args.notifyall, _debug = args.debug
    )

    if args.usestore:
        ibstore = bt.stores.IBStore(**storekwargs)

    if args.broker:
        if args.usestore:
            broker = ibstore.getbroker()
        else:
            broker = bt.brokers.IBBroker(**storekwargs)

        cerebro.setbroker(broker)

    timeframe = bt.TimeFrame.TFrame(args.timeframe)
    if args.resample or args.replay:
        datatf = bt.TimeFrame.Ticks
        datacomp = 1
    else:
        datatf = timeframe
        datacomp = args.compression

    fromdate = None
    if args.fromdate:
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in args.fromdate))
        fromdate = datetime.datetime.strptime(args.fromdate, dtformat)

    IBDataFactory = ibstore.getdata if args.usestore else bt.feeds.IBData

    datakwargs = dict(
            timeframe = datatf, compression = datacomp,
            historical = args.historical, fromdate = fromdate,
            rtbar = args.rtbar,
            qcheck = args.qcheck,
            what = args.what,
            backfill_start = not args.no_backfill_start,
            backfill = not args.no_backfill,
            latethrough = args.latethrough,
            tz = args.timezone
    )

    if not args.usestore and not args.broker:  # neither store nor broker
        datakwargs.update(storekwargs)  # pass the store args over the data

    data0 = IBDataFactory(dataname = args.data0, **datakwargs)

    data1 = None
    if args.data1 is not None:
        data1 = IBDataFactory(dataname = args.data1, **datakwargs)

    rekwargs = dict(
            timeframe = timeframe, compression = args.compression,
            bar2edge = not args.no_bar2edge,
            adjbartime = not args.no_adjbartime,
            rightedge = not args.no_rightedge,
            takelate = not args.no_takelate,
    )

    if args.replay:
        cerebro.replaydata(dataname = data0, **rekwargs)

        if data1 is not None:
            cerebro.replaydata(dataname = data1, **rekwargs)

    elif args.resample:
        cerebro.resampledata(dataname = data0, **rekwargs)

        if data1 is not None:
            cerebro.resampledata(dataname = data1, **rekwargs)

    else:
        cerebro.adddata(data0)
        if data1 is not None:
            cerebro.adddata(data1)

    if args.valid is None:
        valid = None
    else:
        datetime.timedelta(seconds = args.valid)
    # Add the strategy
    cerebro.addstrategy(TestStrategy,
                        smaperiod = args.smaperiod,
                        trade = args.trade,
                        exectype = bt.Order.ExecType(args.exectype),
                        stake = args.stake,
                        stopafter = args.stopafter,
                        valid = args.valid,
                        cancel = args.cancel,
                        donotsell = args.donotsell)

    # Live data ... avoid long data accumulation by switching to "exactbars"
    cerebro.run(exactbars = args.exactbars)

    if args.plot and args.exactbars < 1:  # plot if possible
        cerebro.plot()


def parse_args():
    parser = argparse.ArgumentParser(
            formatter_class = argparse.ArgumentDefaultsHelpFormatter,
            description = 'Test Interactive Brokers integration')

    parser.add_argument('--exactbars', default = 0, type = int,
                        required = False, action = 'store',
                        help = 'exactbars level, use 0/-1/-2 to enable plotting')

    parser.add_argument('--plot',
                        required = False, action = 'store_true',
                        help = 'Plot if possible')

    parser.add_argument('--stopafter', default = 0, type = int,
                        required = False, action = 'store',
                        help = 'Stop after x lines of LIVE data')

    parser.add_argument('--usestore',
                        required = False, action = 'store_true',
                        help = 'Use the store pattern')

    parser.add_argument('--notifyall',
                        required = False, action = 'store_true',
                        help = 'Notify all messages to strategy as store notifs')

    parser.add_argument('--debug',
                        required = False, action = 'store_true',
                        help = 'Display all info received form IB')

    parser.add_argument('--host', default = '127.0.0.1',
                        required = False, action = 'store',
                        help = 'Host for the Interactive Brokers TWS Connection')

    parser.add_argument('--qcheck', default = 0.5, type = float,
                        required = False, action = 'store',
                        help = ('Timeout for periodic '
                                'notification/resampling/replaying check'))

    parser.add_argument('--port', default = 7497, type = int,
                        required = False, action = 'store',
                        help = 'Port for the Interactive Brokers TWS Connection')

    parser.add_argument('--clientId', default = 1, type = int,
                        required = False, action = 'store',
                        help = 'Client Id to connect to TWS (default: random)')

    parser.add_argument('--no-timeoffset',
                        required = False, action = 'store_true',
                        help = ('Do not Use TWS/System time offset for non '
                                'timestamped prices and to align resampling'))

    parser.add_argument('--reconnect', default = -1, type = int,
                        required = False, action = 'store',
                        help = 'Number of recconnection attempts to TWS')

    parser.add_argument('--timeout', default = 5.0, type = float,
                        required = False, action = 'store',
                        help = 'Timeout between reconnection attempts to TWS')

    parser.add_argument('--data0', default = 'RDS A-STK-SMART-USD',
                        required = False, action = 'store',
                        help = 'data 0 into the system')

    parser.add_argument('--data1', default = 'BP-STK-SMART-USD',
                        required = False, action = 'store',
                        help = 'data 1 into the system')

    parser.add_argument('--timezone', default = None,
                        required = False, action = 'store',
                        help = 'timezone to get time output into (pytz names)')

    parser.add_argument('--what', default = None,
                        required = False, action = 'store',
                        help = 'specific price type for historical requests')

    parser.add_argument('--no-backfill_start',
                        required = False, action = 'store_true',
                        help = 'Disable backfilling at the start')

    parser.add_argument('--latethrough',
                        required = False, action = 'store_true',
                        help = ('if resampling replaying, adjusting time '
                                'and disabling time offset, let late samples '
                                'through'))

    parser.add_argument('--no-backfill',
                        required = False, action = 'store_true',
                        help = 'Disable backfilling after a disconnection')

    parser.add_argument('--rtbar', default = False,
                        required = False, action = 'store_true',
                        help = 'Use 5 seconds real time bar updates if possible')

    parser.add_argument('--historical',
                        required = False, action = 'store_true',
                        help = 'do only historical download')

    parser.add_argument('--fromdate',
                        required = False, action = 'store',
                        help = ('Starting date for historical download '
                                'with format: YYYY-MM-DD[THH:MM:SS]'))

    parser.add_argument('--smaperiod', default = 5, type = int,
                        required = False, action = 'store',
                        help = 'Period to apply to the Simple Moving Average')

    pgroup = parser.add_mutually_exclusive_group(required = False)

    pgroup.add_argument('--replay',
                        required = False, action = 'store_true',
                        help = 'replay to chosen timeframe')

    pgroup.add_argument('--resample',
                        required = False, action = 'store_true',
                        help = 'resample to chosen timeframe')

    parser.add_argument('--timeframe', default = 'Minutes',
                        choices = bt.TimeFrame.Names,
                        required = False, action = 'store',
                        help = 'TimeFrame for Resample/Replay')

    parser.add_argument('--compression', default = 120, type = int,
                        required = False, action = 'store',
                        help = 'Compression for Resample/Replay')

    parser.add_argument('--no-takelate',
                        required = False, action = 'store_true',
                        help = ('resample/replay, do not accept late samples '
                                'in new bar if the data source let them through '
                                '(latethrough)'))

    parser.add_argument('--no-bar2edge',
                        required = False, action = 'store_true',
                        help = 'no bar2edge for resample/replay')

    parser.add_argument('--no-adjbartime',
                        required = False, action = 'store_true',
                        help = 'no adjbartime for resample/replay')

    parser.add_argument('--no-rightedge',
                        required = False, action = 'store_true',
                        help = 'no rightedge for resample/replay')

    parser.add_argument('--broker',
                        required = False, action = 'store_true',
                        help = 'Use IB as broker')

    parser.add_argument('--trade',
                        required = False, action = 'store_true',
                        help = 'Do Sample Buy/Sell operations')

    parser.add_argument('--donotsell',
                        required = False, action = 'store_true',
                        help = 'Do not sell after a buy')

    parser.add_argument('--exectype', default = bt.Order.ExecTypes[0],
                        choices = bt.Order.ExecTypes,
                        required = False, action = 'store',
                        help = 'Execution to Use when opening position')

    parser.add_argument('--stake', default = 10, type = int,
                        required = False, action = 'store',
                        help = 'Stake to use in buy operations')

    parser.add_argument('--valid', default = 0, type = int,
                        required = False, action = 'store',
                        help = 'Seconds to keep the order alive (0 means DAY)')

    parser.add_argument('--cancel', default = 0, type = int,
                        required = False, action = 'store',
                        help = ('Cancel a buy order after n bars in operation,'
                                ' to be combined with orders like Limit'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()

# END setup
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
