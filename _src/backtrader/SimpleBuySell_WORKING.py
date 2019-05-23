from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt



class St(bt.Strategy):
    def logdata(self):                     # list tick info
        txt = []
        txt.append('{}'.format(len(self)))
        txt.append('{}'.format(self.data.datetime.datetime(0))
                   )
        # txt.append('{:.2f}'.format(self._data.open[0]))
        # txt.append('{:.2f}'.format(self._data.high[0]))
        # txt.append('{:.2f}'.format(self._data.low[0]))
        txt.append('{:.2f}'.format(self.data.bid[0]))
        txt.append('{:.2f}'.format(self.data.volume[0]))
        print("Tick     Date      Time      Price   Volume")
        print('   '.join(txt))


    def notify_order(self, order):
        if order.status == order.Completed:
            buysell = 'BUY' if order.isbuy() else 'SELL'
            txt = '{} {}@{}'.format(buysell, order.executed.size,
                                    order.executed.price)
            print(txt)


    bought = 0
    sold = 0


    def next(self):
        self.logdata()
        if not self.data_live:
            return
        if not self.bought:
            self.bought = len(self)     # keep entry bar
            self.buy()
        elif not self.sold:
            if len(self) == (self.bought + 3):
                self.sell()


    data_live = True

    def notify_data(self, data, status, *args, **kwargs):        # notify when live _data
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status),
              *args)
        if status == data.LIVE:
            self.data_live = True



def run(args=None):
    cerebro = bt.Cerebro(stdstats=False)
    store = bt.stores.IBStore(port=7497)

    # _data = store.getdata(dataname='EUR.USD-CASH-IDEALPRO',
    data = store.getdata(dataname='EUR.USD-CASH-IDEALPRO',
                         timeframe=bt.TimeFrame.Ticks)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds,
                         compression=1),
                         # compression=10)              # list every 10 seconds

    cerebro.broker = store.getbroker()

    cerebro.addstrategy(St)

    cerebro.run()


if __name__ == '__main__':
    run()



