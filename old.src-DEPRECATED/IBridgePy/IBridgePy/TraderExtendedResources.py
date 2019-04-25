from IBridgePy.TraderBasicResources import TraderBasicResources
from sys import exit
from IBridgePy.quantopian import MarketOrder, LimitOrder, StopOrder
import math
from IBridgePy.constants import OrderStatus
from IBridgePy.IbridgepyTools import from_contract_to_security, check_same_security, \
    create_order, add_exchange_primaryExchange_to_security, superSymbol
import datetime as dt
from BasicPyLib.BasicTools import utc_in_seconds_to_dt


class Trader(TraderBasicResources):
    def count_positions(self, security, accountCode='default'):
        self.log.debug(__name__ + '::count_positions:security=%s' % (security.full_print(),))
        adj_accountCode = self.adjust_accountCode(accountCode)
        positionRecord = self.get_position(security, adj_accountCode)
        return positionRecord.amount

    def close_all_positions(self, orderStatusMonitor=True, accountCode='default'):
        self.log.debug(__name__ + '::close_all_positions:')
        adj_accountCode = self.adjust_accountCode(accountCode)
        positions = self.get_all_positions(adj_accountCode)  # return a dictionary
        orderIdList = []

        # !!! cannot iterate positions directly because positions can change during the iteration if any orders are
        # executed.
        # The solution is to use another list to record all security to be closed.
        adj_securities = list(positions.keys())

        # place close orders
        for security in adj_securities:
            orderId = self.order_target(security, 0, accountCode=adj_accountCode)
            orderIdList.append(orderId)

        # Monitor status
        if orderStatusMonitor:
            for orderId in orderIdList:
                self.order_status_monitor(orderId, OrderStatus.FILLED)

    def close_all_positions_except(self, a_security, accountCode='default'):
        self.log.debug(__name__ + '::close_all_positions_except:' + str(a_security))
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderIdList = []
        for security in self.get_all_positions(adj_accountCode):
            if not check_same_security(a_security, security):
                orderId = self.order_target(security, 0, accountCode=adj_accountCode)
                orderIdList.append(orderId)
        for orderId in orderIdList:
            self.order_status_monitor(orderId, OrderStatus.FILLED)

    def cancel_all_orders(self, accountCode='default'):
        self.log.debug(__name__ + '::cancel_all_orders')
        """
        TODO: cancel_all_orders is not batch requests. If any cancel-request fails, the code will terminate. 
        Maybe change it to batch requests.
        """
        for orderId in self.get_portfolio(accountCode).orderStatusBook:
            if self.get_portfolio(accountCode).orderStatusBook[orderId].status not \
                    in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.INACTIVE, OrderStatus.PENDINGCANCEL]:
                self.cancel_order(orderId)

    def get_contract_details(self, secType, symbol, field, currency='USD', exchange='', primaryExchange='', expiry='',
                             strike=0.0, right='', multiplier='', localSymbol=''):
        security = superSymbol(secType=secType, symbol=symbol, currency=currency, exchange=exchange,
                               primaryExchange=primaryExchange, expiry=expiry, strike=strike, right=right,
                               multiplier=multiplier, localSymbol=localSymbol)
        return self.brokerService.get_contract_details(security, field)

    def get_scanner_results(self, **kwargs):
        return self.brokerService.get_scanner_results(kwargs)

    def get_option_greeks(self, security, tickType, fields):
        self.log.debug(__name__ + '::get_option_greeks: security=%s tickType=%s fields=%s'
                       % (security.full_print(), str(tickType), str(fields)))
        return self.brokerService.get_option_greeks(security, tickType, fields)

    def order_percent(self, security, percent, style=MarketOrder(), orderRef='',
                      accountCode='default'):
        self.log.notset(__name__ + '::order_percent')
        if percent > 1.0 or percent < -1.0:
            self.log.error(__name__ + '::order_percent: EXIT, percent=%s [-1.0, 1.0]' % (str(percent),))
            exit()
        targetShare = int(
            self.get_portfolio(accountCode).portfolio_value / self.show_real_time_price(security, 'ask_price'))
        return self.order(security, amount=int(targetShare * percent), style=style,
                          orderRef=orderRef, accountCode=accountCode)

    def order_target(self, security, amount, style=MarketOrder(), orderRef='',
                     accountCode='default'):
        self.log.notset(__name__ + '::order_target')
        position = self.get_position(security, accountCode=accountCode)
        hold = position.amount
        if amount != hold:
            # amount - hold is correct, confirmed
            return self.order(security, amount=int(amount - hold), style=style,
                              orderRef=orderRef, accountCode=accountCode)
        else:
            self.log.debug(__name__ + '::order_target: %s No action is needed' % (str(security),))
            return 0

    def order_target_percent(self, security, percent, style=MarketOrder(),
                             orderRef='', accountCode='default'):
        self.log.notset(__name__ + '::order_percent')
        if percent > 1.0 or percent < -1.0:
            self.log.error(__name__ + '::order_target_percent: EXIT, percent=%s [-1.0, 1.0]' % (str(percent),))
            exit()
        a = self.get_portfolio(accountCode).portfolio_value
        b = self.show_real_time_price(security, 'ask_price')
        if math.isnan(b):
            self.log.error(__name__ + '::order_target_percent: EXIT, real_time_price is NaN')
            exit()
        if b <= 0.0:
            self.log.error(__name__ + '::order_target_percent: EXIT, real_time_price <= 0.0')
            exit()
        targetShare = int(a * percent / b)
        return self.order_target(security, amount=targetShare, style=style,
                                 orderRef=orderRef, accountCode=accountCode)

    def order_target_value(self, security, value, style=MarketOrder(),
                           orderRef='', accountCode='default'):
        self.log.notset(__name__ + '::order_target_value')
        targetShare = int(value / self.show_real_time_price(security, 'ask_price'))
        return self.order_target(security, amount=targetShare, style=style,
                                 orderRef=orderRef, accountCode=accountCode)

    def order_value(self, security, value, style=MarketOrder(), orderRef='',
                    accountCode='default'):
        self.log.notset(__name__ + '::order_value')
        targetShare = int(value / self.show_real_time_price(security, 'ask_price'))
        return self.order(security, amount=targetShare, style=style,
                          orderRef=orderRef, accountCode=accountCode)

    def place_order_with_stoploss(self, security, amount, stopLossPrice, style=MarketOrder(), tif='DAY', accountCode='default'):
        """
        return orderId of the parentOrder only
        """
        ocaGroup = str(dt.datetime.now())
        adj_accountCode = self.adjust_accountCode(accountCode)
        parentOrderId = self.brokerService.use_next_id()
        parentOrder = create_order(parentOrderId, adj_accountCode, security, amount, style, self.get_datetime(),
                                   ocaGroup=ocaGroup)
        slOrderId = self.brokerService.use_next_id()
        slOrder = create_order(slOrderId, adj_accountCode, security, -amount, StopOrder(stopLossPrice, tif=tif),
                               self.get_datetime(),
                               ocaGroup=ocaGroup)
        # IB recommends this way to place takeProfitOrder and stopLossOrder
        # with main order.
        parentOrder.requestedOrder.transmit = False
        slOrder.requestedOrder.parentId = parentOrderId
        slOrder.requestedOrder.transmit = True  # only transmit slOrder to avoid inadvertent actions

        # request_data does not follow up on place_order(parentOrder) because it is a partial order
        orderId = self.brokerService.place_order(parentOrder, followUp=False)
        slOrderId = self.brokerService.place_order(slOrder)
        return orderId, slOrderId

    def place_order_with_takeprofit(self, security, amount, takeProfitPrice, style=MarketOrder(), tif='DAY',
                                    accountCode='default'):
        """
        return orderId of the parentOrder only
        """
        ocaGroup = str(dt.datetime.now())
        adj_accountCode = self.adjust_accountCode(accountCode)
        parentOrderId = self.brokerService.use_next_id()
        parentOrder = create_order(parentOrderId, adj_accountCode, security, amount, style, self.get_datetime(),
                                   ocaGroup=ocaGroup)
        tpOrderId = self.brokerService.use_next_id()
        tpOrder = create_order(tpOrderId, adj_accountCode, security, -amount, LimitOrder(takeProfitPrice, tif=tif),
                               self.get_datetime(),
                               ocaGroup=ocaGroup)
        # IB recommends this way to place takeProfitOrder and stopLossOrder
        # with main order.
        parentOrder.requestedOrder.transmit = False
        tpOrder.requestedOrder.parentId = parentOrderId
        tpOrder.requestedOrder.transmit = True
        # request_data does not follow up on place_order(parentOrder) because it is a partial order
        orderId = self.brokerService.place_order(parentOrder, followUp=False)
        tpOrderId = self.brokerService.place_order(tpOrder)
        return orderId, tpOrderId

    def place_order_with_stoploss_takeprofit(self, security, amount, stopLossPrice, takeProfitPrice,
                                             style=MarketOrder(), tif='DAY', accountCode='default'):
        """
        return orderId of the parentOrder only
        """
        ocaGroup = str(dt.datetime.now())
        adj_accountCode = self.adjust_accountCode(accountCode)
        parentOrderId = self.brokerService.use_next_id()
        parentOrder = create_order(parentOrderId, adj_accountCode, security, amount, style, self.get_datetime(),
                                   ocaGroup=ocaGroup)
        tpOrderId = self.brokerService.use_next_id()
        tpOrder = create_order(tpOrderId, adj_accountCode, security, -amount, LimitOrder(takeProfitPrice, tif=tif),
                               self.get_datetime(),
                               ocaGroup=ocaGroup)
        slOrderId = self.brokerService.use_next_id()
        slOrder = create_order(slOrderId, adj_accountCode, security, -amount, StopOrder(stopLossPrice, tif=tif),
                               self.get_datetime(),
                               ocaGroup=ocaGroup)
        # IB recommends this way to place takeProfitOrder and stopLossOrder
        # with main order.
        parentOrder.requestedOrder.transmit = False
        tpOrder.requestedOrder.parentId = parentOrderId
        slOrder.requestedOrder.parentId = parentOrderId
        tpOrder.requestedOrder.transmit = False
        slOrder.requestedOrder.transmit = True  # only transmit slOrder to avoid inadvertent actions
        orderId = self.brokerService.place_order(parentOrder, followUp=False)
        tpOrderId = self.brokerService.place_order(tpOrder, followUp=False)
        slOrderId = self.brokerService.place_order(slOrder)
        return orderId, slOrderId, tpOrderId

    def create_order(self, action, amount, security, orderDetails, ocaGroup=None, ocaType=None, transmit=None,
                     parentId=None, orderRef='', outsideRth=False, hidden=False, accountCode='default'):
        orderId = self.brokerService.use_next_id()
        adj_accountCode = self.adjust_accountCode(accountCode)
        if action == 'BUY':
            amount = abs(amount)
        else:
            amount = -1 * abs(amount)
        ans = create_order(orderId, adj_accountCode, security, amount, orderDetails, self.get_datetime(),
                           ocaGroup=ocaGroup, ocaType=ocaType, transmit=transmit, parentId=parentId,
                           orderRef=orderRef, outsideRth=outsideRth, hidden=hidden)
        return ans

    def place_combination_orders(self, legList):
        ans = []
        for order in legList:
            orderId = self.brokerService.place_order(order, followUp=False)
            ans.append(orderId)
        return ans
