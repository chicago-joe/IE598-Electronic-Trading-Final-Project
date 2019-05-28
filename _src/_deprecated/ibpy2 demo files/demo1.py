# from the tutorial located at:
# https://www.youtube.com/watch?v=Bu0kpU-ozaw


from ib.opt import Connection, message
from ib.ext.Contract import Contract
from ib.ext.Order import Order


def make_contract(symbol, sec_type, exch, prim_exch, curr):
    Contract.m_symbol = symbol
    Contract.m_secType = sec_type
    Contract.m_exchange = exch
    Contract.m_primaryExch = prim_exch
    Contract.m_currency = curr
    return Contract     # Pass some variables through the already created "Contract" class:

def make_order(action, quantity, price = None):
    if price is not None:     # If a price is entered, the order is a limit order.
        order = Order()
        order.m_orderType = 'LMT'
        order.m_totalQuantity = quantity
        order.m_action = action
        order.m_lmtPrice = price
    else:                      # If no price, then mkt order
        order = Order()
        order.m_orderType = 'MKT'
        order.m_totalQuantity = quantity
        order.m_action = action
    return order



cid = 4721   # pick a starting order number
# need to make a for-loop of a counter, adding +1 to oid every time it makes a trade

while __name__ == "__main__":
    conn = Connection.create(port = 7497, clientId = 1)
    conn.connect()

    oid = cid

    test_contract = make_contract('EUR.USD', 'CASH', 'IDEALPRO', 'IDEALPRO', 'USD')
    test_order = make_order('BUY', 200)

    conn.placeOrder(cid, test_contract, test_order)
    conn.disconnect()

    x = input('enter to resend')
    cid += 1

