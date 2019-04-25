from IBridgePy.constants import OrderType, OrderStatus


def print_contract(contract):
    """
    IBCpp.Contract() cannot use __str__ to print so that make a print-function
    :param contract: IBCpp.Contract()
    :return: String
    """
    base = ['secType', 'primaryExchange', 'exchange', 'symbol', 'currency']
    stkCash = base
    fut = base + ['expiry']
    other = fut + ['strike', 'right', 'multiplier']
    ans = ''
    if contract.secType in ['STK', 'CASH']:
        iterator = stkCash
    elif contract.secType in ['FUT', 'BOND']:
        iterator = fut
    else:
        iterator = other
    for para in iterator:
        ans += str(getattr(contract, para)) + ','
    return ans[:-1]


def print_IB_order(order):
    """
    IBCpp.Order() cannot use __str__ to print so that make a print-function
    :param order: IBCpp.Order()
    :return: String
    """
    action = order.action  # BUY, SELL
    amount = order.totalQuantity  # int only
    orderType = order.orderType  # LMT, MKT, STP
    tif = order.tif
    orderRef = order.orderRef

    ans = '%s %s %s %s %s' % (action, orderType, str(amount), str(tif), orderRef)
    if orderType == OrderType.MKT:
        pass
    elif orderType == OrderType.LMT:
        ans += ' limitPrice=' + str(order.lmtPrice)
    elif orderType == OrderType.STP:
        ans += ' stopPrice=' + str(order.auxPrice)
    elif orderType == OrderType.TRAIL_LIMIT:
        if order.auxPrice < 1e+307:
            ans += ' trailingAmount=' + str(order.auxPrice)
        if order.trailingPercent < 1e+307:
            ans += ' trailingPercent=' + str(order.trailingPercent)
        ans += ' trailingStopPrice=' + str(order.trailStopPrice)
    elif orderType == OrderType.TRAIL:
        if order.auxPrice < 1e+307:
            ans += ' trailingAmount=' + str(order.auxPrice)
        if order.trailingPercent < 1e+307:
            ans += ' trailingPercent=' + str(order.trailingPercent)
        if order.trailStopPrice < 1e+307:
            ans += ' trailingStopPrice=' + str(order.trailStopPrice)
    return ans


def print_IB_orderState(orderState):
    return 'status=%s commission=%s warningText=%s' % (orderState.status, orderState.commission, orderState.warningText)


def print_IB_execution(execution):
    return 'orderId=%s clientId=%s time=%s acctNumber=%s exchange=%s side=%s shares=%s price=%s' \
           % (execution.orderId, execution.clientId, execution.time, execution.acctNumber, execution.exchange,
              execution.side, execution.shares, execution.price)


class PositionRecord:
    def __init__(self, accountCode, str_security_no_exchange_no_primaryExchange, amount, cost_basis, contract):
        """
        !!!! str_security does not have primaryExchange and exchange !!!!
        positions are aggregations of a few position that may be traded at different exchange.
        """
        self.accountCode = accountCode
        self.str_security = str_security_no_exchange_no_primaryExchange
        self.amount = amount
        self.cost_basis = cost_basis
        self.contract = contract  # the original contract is documented in case it is needed for some users

    @property
    def price(self):
        return self.cost_basis

    def __str__(self):
        ans = ''''''
        for name in ['accountCode', 'str_security', 'amount', 'cost_basis']:
            ans += name + '=' + str(getattr(self, name)) + ' '
        return ans


class TraderPositionRecords:
    """
    Only store positions when amount > 0
    Delete positions when amount == 0
    1st keyed by accountCode
    2nd keyed by str_security_no_exchange_no_primaryExchange

    """

    def __init__(self):
        self.traderPositionRecords = {}

    def __str__(self):
        if not self.traderPositionRecords:
            return 'EMPTY traderPositionRecords'
        else:
            ans = '''traderPositionRecords'''
            for accountCode in self.traderPositionRecords:
                ans += '''accountCode=%s\n''' % (accountCode,)
                for str_security in self.traderPositionRecords[accountCode]:
                    ans += '''%s: amount=%s price=%s\n''' % (
                        str_security, str(self.traderPositionRecords[accountCode][str_security].amount),
                        str(self.traderPositionRecords[accountCode][str_security].price))
            return ans

    def update(self, positionRecord):
        if positionRecord.accountCode not in self.traderPositionRecords:
            self.traderPositionRecords[positionRecord.accountCode] = {}

        # Only store positions when amount != 0
        # Delete positions when amount == 0
        if positionRecord.amount == 0:
            if positionRecord.str_security in self.traderPositionRecords[positionRecord.accountCode]:
                del self.traderPositionRecords[positionRecord.accountCode][positionRecord.str_security]
        else:
            self.traderPositionRecords[positionRecord.accountCode][positionRecord.str_security] = positionRecord

    def _hasAccountCode(self, accountCode):
        return accountCode in self.traderPositionRecords

    def _hasAccountAndSecurity(self, accountCode, str_security):
        return self._hasAccountCode(accountCode) and (str_security in self.traderPositionRecords[accountCode])

    def getPositionRecord(self, accountCode, security):
        str_security = security.full_print()
        if self._hasAccountAndSecurity(accountCode, str_security):
            return self.traderPositionRecords[accountCode][str_security]
        else:
            return PositionRecord(accountCode, str_security, 0, 0.0, None)

    def hold_any_position(self, accountCode):
        if not self._hasAccountCode(accountCode):
            return False
        return len(self.traderPositionRecords[accountCode]) > 0

    def get_all_positions(self, accountCode):
        """

        :param accountCode:
        :return: dictionary, keyed by str_security, value = PositionRecord
        """
        if not self._hasAccountCode(accountCode):
            return {}
        return self.traderPositionRecords[accountCode]


class OrderStatusRecord:
    def __init__(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                 whyHeld):
        self.orderId = orderId
        self.status = status
        self.filled = filled
        self.remaining = remaining
        self.avgFillPrice = avgFillPrice
        self.permId = permId
        self.parentId = parentId
        self.lastFillPrice = lastFillPrice
        self.clientId = clientId
        self.whyHeld = whyHeld
        self.accountCode = None  # not IB native field. It was added to easily build IbridgePyOrder

    def __str__(self):
        ans = ''''''
        for name in ['orderId', 'status', 'filled', 'remaining', 'avgFillPrice', 'permId', 'parentId',
                     'lastFillPrice', 'clientId', 'whyHeld', 'accountCode']:
            ans += '''%s=%s ''' % (name, getattr(self, name))
        return ans

    def setAccountCode(self, accountCode):
        """
        This function is used in brokerService layer.
        :param accountCode:
        :return: void
        """
        self.accountCode = accountCode


class TraderOrderStatusRecords:
    def __init__(self):
        self.traderOrderStatusRecords = {}

    def __str__(self):
        if not self.traderOrderStatusRecords:
            return 'EMPTY traderOrderStatusRecords'
        else:
            ans = ''''''
            for orderId in self.traderOrderStatusRecords:
                ans += '''%s''' % (str(self.traderOrderStatusRecords[orderId]),)
            return ans

    def update(self, orderStatusRecord):
        self.traderOrderStatusRecords[orderStatusRecord.orderId] = orderStatusRecord

    def getValue(self, orderId, key):
        if orderId in self.traderOrderStatusRecords:
            if hasattr(self.traderOrderStatusRecords[orderId], key):
                return getattr(self.traderOrderStatusRecords[orderId], key)
            else:
                return None
        else:
            return None


class OpenOrderRecord:
    def __init__(self, orderId, contract, order, orderState):
        self.orderId = orderId
        self.contract = contract
        self.order = order
        self.orderState = orderState
        self.accountCode = order.account

    def __str__(self):
        ans = '''orderId=%s ''' % (self.orderId,)
        ans += '''contract=%s ''' % (print_contract(self.contract),)
        ans += '''order=%s ''' % (print_IB_order(self.order),)
        ans += '''orderState=%s ''' % (print_IB_orderState(self.orderState),)
        ans += '''accountCode=%s ''' % (self.accountCode,)
        return ans


class TraderOpenOrderRecords:
    def __init__(self):
        self.traderOpenOrderRecords = {}

    def __str__(self):
        if not self.traderOpenOrderRecords:
            return 'EMPTY traderOpenOrderRecords'
        else:
            ans = ''''''
            for orderId in self.traderOpenOrderRecords:
                ans += '''%s''' % (str(self.traderOpenOrderRecords[orderId]),)
            return ans

    def update(self, openOrderRecord):
        accountCode = openOrderRecord.accountCode
        if accountCode not in self.traderOpenOrderRecords:
            self.traderOpenOrderRecords[accountCode] = {}
        self.traderOpenOrderRecords[accountCode][openOrderRecord.orderId] = openOrderRecord

    def _hasAccountCode(self, accountCode):
        return accountCode in self.traderOpenOrderRecords

    def _hasSecurityAndOrderId(self, accountCode, orderId):
        return self._hasAccountCode(accountCode) and (orderId in self.traderOpenOrderRecords[accountCode])

    def getValue(self, accountCode, orderId, key):
        if self._hasSecurityAndOrderId(accountCode, orderId):
            openOrderRecord = self.traderOpenOrderRecords[accountCode][orderId]
            if hasattr(openOrderRecord, key):
                return getattr(openOrderRecord, key)
            else:
                return None
        else:
            return None

    def get_all_orderId(self, accountCode):
        if not self._hasAccountCode(accountCode):
            return []
        return self.traderOpenOrderRecords[accountCode].keys()


class ExecDetailsRecord:
    def __init__(self, reqId, contract, execution):
        self.reqId = reqId
        self.contract = contract
        self.execution = execution

    def __str__(self):
        ans = '''reqId=%s''' % (self.reqId,)
        ans += '''contract=%s ''' % (print_contract(self.contract),)
        ans += '''execution=%s ''' % (print_IB_execution(self.execution),)
        return ans


class TraderExecDetailsRecords:
    def __init__(self):
        self.traderExecDetailsRecords = {}

    def __str__(self):
        if not self.traderExecDetailsRecords:
            return 'EMPTY traderExecDetailsRecords'
        else:
            ans = ''''''
            for reqId in self.traderExecDetailsRecords:
                ans += '''%s''' % (str(self.traderExecDetailsRecords[reqId]),)
            return ans

    def update(self, execDetailsRecord):
        self.traderExecDetailsRecords[execDetailsRecord.reqId] = execDetailsRecord

    def getValue(self, orderId, key):
        if orderId in self.traderExecDetailsRecords:
            if hasattr(self.traderExecDetailsRecords[orderId], key):
                return getattr(self.traderExecDetailsRecords, key)
            else:
                return None
        else:
            return None


class TickPriceRecord:
    def __init__(self, str_security, tickType, price, canAutoExecute):
        self.str_security = str_security
        self.tickType = tickType
        self.price = price
        self.canAutoExecute = canAutoExecute

    def __str__(self):
        ans = '''str_security=%s ''' % (self.str_security,)
        ans += '''tickType=%s ''' % (self.tickType,)
        ans += '''price=%s ''' % (str(self.price))
        ans += '''canAutoExecute=%s ''' % (str(self.canAutoExecute),)
        return ans


class TraderTickPriceRecords:
    def __init__(self):
        self.traderTickPriceRecords = {}

    def __str__(self):
        if not self.traderTickPriceRecords:
            return 'EMPTY traderTickPriceRecords'
        else:
            ans = ''''''
            for str_security in self.traderTickPriceRecords:
                for key in self.traderTickPriceRecords[str_security]:
                    ans += '''%s\n''' % (str(self.traderTickPriceRecords[str_security][key]),)
            return ans

    def update(self, tickPriceRecord):
        str_security = tickPriceRecord.str_security
        if str_security not in self.traderTickPriceRecords:
            self.traderTickPriceRecords[str_security] = {}
        self.traderTickPriceRecords[str_security][tickPriceRecord.tickType] = tickPriceRecord

    def _hasSecurity(self, str_security):
        return str_security in self.traderTickPriceRecords

    def _hasSecurityAndTickType(self, str_security, tickType):
        return self._hasSecurity(str_security) and (tickType in self.traderTickPriceRecords[str_security])

    def getPrice(self, security, tickType):
        if self._hasSecurityAndTickType(security.full_print(), tickType):
            return self.traderTickPriceRecords[security.full_print()][tickType].price
        else:
            return None


class TickSizeRecord:
    def __init__(self, str_security, tickType, size):
        self.str_security = str_security
        self.tickType = tickType
        self.size = size

    def __str__(self):
        ans = '''str_security=%s ''' % (self.str_security,)
        ans += '''tickType=%s ''' % (self.tickType,)
        ans += '''size=%s ''' % (str(self.size))
        return ans


class TraderTickSizeRecords:
    def __init__(self):
        self.traderTickSizeRecords = {}

    def __str__(self):
        if not self.traderTickSizeRecords:
            return 'EMPTY traderTickSizeRecords'
        else:
            ans = ''''''
            for str_security in self.traderTickSizeRecords:
                for key in self.traderTickSizeRecords[str_security]:
                    ans += '''%s\n''' % (str(self.traderTickSizeRecords[str_security][key]),)
            return ans

    def update(self, tickSizeRecord):
        str_security = tickSizeRecord.str_security
        if str_security not in self.traderTickSizeRecords:
            self.traderTickSizeRecords[str_security] = {}
        self.traderTickSizeRecords[str_security][tickSizeRecord.tickType] = tickSizeRecord

    def _hasSecurity(self, str_security):
        return str_security in self.traderTickSizeRecords

    def _hasSecurityAndTickType(self, str_security, tickType):
        return self._hasSecurity(str_security) and (tickType in self.traderTickSizeRecords[str_security])

    def getSize(self, security, tickType):
        if self._hasSecurityAndTickType(security, tickType):
            return self.traderTickSizeRecords[security.full_print()][tickType].size
        else:
            return None


class TickStringRecord:
    def __init__(self, str_security, field, value):
        self.str_security = str_security
        self.field = field
        self.value = value

    def __str__(self):
        ans = '''str_security=%s ''' % (self.str_security,)
        ans += '''field=%s ''' % (self.field,)
        ans += '''value=%s ''' % (str(self.value))
        return ans


class TraderTickStringRecords:
    def __init__(self):
        self.traderTickStringRecords = {}

    def __str__(self):
        if not self.traderTickStringRecords:
            return 'EMPTY traderTickStringRecords'
        else:
            ans = ''''''
            for str_security in self.traderTickStringRecords:
                for key in self.traderTickStringRecords[str_security]:
                    ans += '''%s\n''' % (str(self.traderTickStringRecords[str_security][key]),)
            return ans

    def update(self, tickStringRecord):
        str_security = tickStringRecord.str_security
        if str_security not in self.traderTickStringRecords:
            self.traderTickStringRecords[str_security] = {}
        self.traderTickStringRecords[str_security][tickStringRecord.field] = tickStringRecord

    def _hasSecurity(self, str_security):
        return str_security in self.traderTickStringRecords

    def _hasSecurityAndField(self, str_security, field):
        return self._hasSecurity(str_security) and (field in self.traderTickStringRecords[str_security])

    def getValue(self, security, field):
        if self._hasSecurityAndField(security, field):
            return self.traderTickStringRecords[security.full_print()][field].value
        else:
            return None


class AccountValueRecord:
    def __init__(self, key, value, currency, accountCode):
        self.key = key
        self.value = value
        self.currency = currency
        self.accountCode = accountCode

    def __str__(self):
        ans = '''accountCode=%s ''' % (self.accountCode,)
        ans += '''key=%s ''' % (self.key,)
        ans += '''value=%s ''' % (str(self.value))
        ans += '''currency=%s ''' % (str(self.currency))
        return ans


class TraderAccountValueRecords:
    def __init__(self):
        self.traderAccountValueRecords = {}

    def __str__(self):
        if not self.traderAccountValueRecords:
            return 'EMPTY traderAccountValueRecords'
        else:
            ans = ''''''
            for accountCode in self.traderAccountValueRecords:
                for key in self.traderAccountValueRecords[accountCode]:
                    ans += '''%s\n''' % (str(self.traderAccountValueRecords[accountCode][key]),)
            return ans

    def update(self, accountValueRecord):
        if accountValueRecord.accountCode not in self.traderAccountValueRecords:
            self.traderAccountValueRecords[accountValueRecord.accountCode] = {}
        self.traderAccountValueRecords[accountValueRecord.accountCode][accountValueRecord.key] = accountValueRecord

    def _hasAccountCode(self, accountCode):
        return accountCode in self.traderAccountValueRecords

    def _hasAccountCodeAndKey(self, accountCode, key):
        if self._hasAccountCode(accountCode):
            return key in self.traderAccountValueRecords[accountCode]
        return False

    def getValue(self, accountCode, key):
        if self._hasAccountCodeAndKey(accountCode, key):
            return self.traderAccountValueRecords[accountCode][key].value
        else:
            return None

    def getCurrency(self, accountCode, key):
        if self._hasAccountCode(accountCode):
            return self.traderAccountValueRecords[accountCode][key].currency
        else:
            return None

    def get_all_active_accountCodes(self):
        return list(self.traderAccountValueRecords.keys())  # Python 2, 3 compatibility


class AccountSummaryRecord:
    def __init__(self, reqId, accountCode, tag, value, currency):
        self.reqId = reqId
        self.accountCode = accountCode
        self.tag = tag
        self.value = value
        self.currency = currency

    def __str__(self):
        ans = '''accountCode=%s ''' % (self.accountCode,)
        ans += '''reqId=%s ''' % (self.reqId,)
        ans += '''tag=%s ''' % (self.tag,)
        ans += '''value=%s ''' % (str(self.value))
        ans += '''currency=%s ''' % (str(self.currency))
        return ans


class TraderAccountSummaryRecords:
    def __init__(self):
        self.traderAccountSummaryRecords = {}  # keyed by accountCode, called back from IB server.

    def __str__(self):
        if not self.traderAccountSummaryRecords:
            return 'EMPTY traderAccountSummaryRecords'
        else:
            ans = ''''''
            for accountCode in self.traderAccountSummaryRecords:
                for key in self.traderAccountSummaryRecords[accountCode]:
                    ans += '''%s\n''' % (str(self.traderAccountSummaryRecords[accountCode][key]),)
            return ans

    def update(self, accountSummaryRecord):
        accountCode = accountSummaryRecord.accountCode
        tag = accountSummaryRecord.tag
        if accountCode not in self.traderAccountSummaryRecords:
            self.traderAccountSummaryRecords[accountCode] = {}
        self.traderAccountSummaryRecords[accountCode][tag] = accountSummaryRecord

    def _hasAccountCode(self, accountCode):
        return accountCode in self.traderAccountSummaryRecords

    def _hasAccountCodeAndKey(self, accountCode, key):
        if self._hasAccountCode(accountCode):
            return key in self.traderAccountSummaryRecords[accountCode]
        return False

    def getValue(self, accountCode, key):
        if self._hasAccountCode(accountCode):
            return self.traderAccountSummaryRecords[accountCode][key].value
        else:
            return None

    def getCurrency(self, accountCode, key):
        if self._hasAccountCodeAndKey(accountCode, key):
            return self.traderAccountSummaryRecords[accountCode][key].currency
        else:
            return None

    def get_all_active_accountCodes(self):
        return list(self.traderAccountSummaryRecords.keys())  # python 2, 3 compatibility


class TickOptionComputationRecord:
    def __init__(self, security, tickType, impliedVol, delta,
                 optPrice, pvDividend, gamma, vega, theta,
                 undPrice):
        self.security = security
        self.tickType = tickType
        self.impliedVol = impliedVol
        self.delta = delta
        self.optPrice = optPrice
        self.pvDividend = pvDividend
        self.gamma = gamma
        self.vega = vega
        self.theta = theta
        self.undPrice = undPrice

    def __str__(self):
        ans = ''''''
        for name in ['str_security', 'tickType', 'impliedVol', 'delta',
                     'optPrice', 'pvDividend', 'gamma', 'vega', 'theta',
                     'undPrice']:
            ans += name + '=' + str(getattr(self, name))
        return ans


class TraderTickOptionComputationRecords:
    def __init__(self):
        self.traderTickOptionComputationRecords = {}

    def __str__(self):
        if not self.traderTickOptionComputationRecords:
            return 'EMPTY traderTickOptionComputationRecords'
        else:
            ans = ''''''
            for str_security in self.traderTickOptionComputationRecords:
                ans += '''%s\n''' % (str(self.traderTickOptionComputationRecords[str_security]),)
            return ans

    def update(self, tickOptionComputationRecord):
        str_security = tickOptionComputationRecord.security.full_print()
        tickType = tickOptionComputationRecord.tickType
        if str_security not in self.traderTickOptionComputationRecords:
            self.traderTickOptionComputationRecords[str_security] = {}
        self.traderTickOptionComputationRecords[str_security][tickType] = tickOptionComputationRecord

    def _hasSecurity(self, str_security):
        return str_security in self.traderTickOptionComputationRecords

    def _hasSecurityAndTickType(self, str_security, tickType):
        return self._hasSecurity(str_security) and (tickType in self.traderTickOptionComputationRecords[str_security])

    def getValue(self, security, tickType, field):
        str_security = security.full_print()
        if self._hasSecurityAndTickType(str_security, tickType):
            return getattr(self.traderTickOptionComputationRecords[str_security][tickType], field)
        else:
            return None


class BrokerServiceOrderStatusBook:
    def __init__(self):
        self.brokerServiceOrderStatusBook = {}  # key=accountCode value= TraderOrderStatusBook

    def __str__(self):
        if not self.brokerServiceOrderStatusBook:
            return 'EMPTY orderStatusBook'
        else:
            ans = '''BrokerServiceOrderStatusBook id=%s \n''' % (id(self),)
            for accountCode in self.brokerServiceOrderStatusBook.keys():
                ans += str(self.brokerServiceOrderStatusBook[accountCode]) + '\n'
            return ans

    def createFromIbridgePyOrder(self, ibridgePyOrder):
        accountCode = ibridgePyOrder.requestedOrder.account
        if accountCode not in self.brokerServiceOrderStatusBook:
            self.brokerServiceOrderStatusBook[accountCode] = TraderOrderStatusBook()
        self.brokerServiceOrderStatusBook[accountCode].createFromIbridgePyOrder(ibridgePyOrder)

    def updateFromOpenOrder(self, openOrderRecord):
        accountCode = openOrderRecord.accountCode
        if accountCode not in self.brokerServiceOrderStatusBook:
            self.brokerServiceOrderStatusBook[accountCode] = TraderOrderStatusBook()
        self.brokerServiceOrderStatusBook[accountCode].updateFromOpenOrder(openOrderRecord)

    def updateFromOrderStatus(self, orderStatusRecord):
        accountCode = orderStatusRecord.accountCode
        if accountCode not in self.brokerServiceOrderStatusBook:
            self.brokerServiceOrderStatusBook[accountCode] = TraderOrderStatusBook()
        self.brokerServiceOrderStatusBook[accountCode].updateFromOrderStatus(orderStatusRecord)

    def updateFromExecDetails(self, execDetailsRecord):
        accountCode = execDetailsRecord.execution.acctNumber
        if accountCode not in self.brokerServiceOrderStatusBook:
            self.brokerServiceOrderStatusBook[accountCode] = TraderOrderStatusBook()
        self.brokerServiceOrderStatusBook[accountCode].updateFromExecDetails(execDetailsRecord)

    def get_all_orderId(self, accountCode):
        if accountCode in self.brokerServiceOrderStatusBook:
            return self.brokerServiceOrderStatusBook[accountCode].get_all_orderId()
        else:
            return []

    def getValues(self, accountCode, orderId, tags):
        ans = []
        for tag in tags:
            ans = self.getValue(accountCode, orderId, tag)
        return ans

    def getValue(self, accountCode, orderId, tag):
        return self.brokerServiceOrderStatusBook[accountCode].getValue(orderId, tag)


class TraderOrderStatusBook:
    def __init__(self):
        self.traderOrderStatusBook = {}  # keyed by orderId, value = IBridgePy::quantopian::IbridgePyOrder

    def __str__(self):
        if not self.traderOrderStatusBook:
            return 'EMPTY traderOrderStatusBook'
        else:
            ans = '''TraderOrderStatusBook id=%s \n''' % (id(self),)
            for orderId in self.traderOrderStatusBook:
                ans += 'orderId=%s' % (orderId,) + str(self.traderOrderStatusBook[orderId]) + '\n'
            return ans

    def createFromIbridgePyOrder(self, ibridgePyOrder):
        orderId = ibridgePyOrder.orderId
        if orderId not in self.traderOrderStatusBook:
            self.traderOrderStatusBook[orderId] = ibridgePyOrder
        else:
            print(__name__ + '::TraderOrderStatusBook::createFromIbridgePyOrder: EXIT, orderId=%s exist' % (orderId,))
            exit()

    def updateFromOpenOrder(self, openOrderRecord):
        orderId = openOrderRecord.orderId
        if orderId not in self.traderOrderStatusBook:
            self.traderOrderStatusBook[orderId] = IbridgePyOrder(orderId)
        self.traderOrderStatusBook[orderId].openOrderRecord = openOrderRecord

    def updateFromOrderStatus(self, orderStatusRecord):
        orderId = orderStatusRecord.orderId
        if orderId not in self.traderOrderStatusBook:
            self.traderOrderStatusBook[orderId] = IbridgePyOrder(orderId)
        self.traderOrderStatusBook[orderId].orderStatusRecord = orderStatusRecord

    def updateFromExecDetails(self, execDetailsRecord):
        orderId = execDetailsRecord.execution.orderId
        if orderId not in self.traderOrderStatusBook:
            self.traderOrderStatusBook[orderId] = IbridgePyOrder(orderId)
        self.traderOrderStatusBook[orderId].execDetailsRecord = execDetailsRecord

    def getValue(self, orderId, tag):
        return self.traderOrderStatusBook[orderId].getValue(tag)

    def get_all_orderId(self):
        return self.traderOrderStatusBook.keys()


class IbridgePyOrder:
    def __init__(self, orderId=None, requestedContract=None, requestedOrder=None, createdTime=None):
        self.orderId = orderId
        self.openOrderRecord = None
        self.orderStatusRecord = None
        self.execDetailsRecord = None
        self.requestedContract = requestedContract
        self.requestedOrder = requestedOrder
        self.created = createdTime  # Quantopian, the time when this order is created by IBridgePy this session

    def __str__(self):
        if self.requestedOrder is not None:  # IBridgePy created orders
            ans = 'orderId=%s status=%s order=%s contract=%s' % (self.orderId, self.status, print_IB_order(self.requestedOrder), print_contract(self.requestedContract))
        else:  # orders are called-back from IB server
            ans = 'orderId=%s status=%s order=%s contract=%s' % (self.orderId, self.status, print_IB_order(self.openOrderRecord.order), print_contract(self.openOrderRecord.contract))
        return ans

    def getValue(self, tag):
        if hasattr(self, tag):
            return getattr(self, tag)
        else:
            if tag in ['orderId', 'status', 'filled', 'remaining', 'avgFillPrice', 'permId', 'parentId',
                       'lastFillPrice', 'clientId', 'whyHeld', 'accountCode']:
                return getattr(self.orderStatusRecord, tag)
            elif tag in ['execution']:
                return getattr(self.execDetailsRecord, tag)
            elif tag in ['orderType', 'orderRef', 'tif', 'ocaGroup', 'ocaType']:
                return getattr(self.openOrderRecord.order, tag)
            elif tag in ['symbol', 'secType', 'exchange', 'primaryExchange', 'expiry', 'multiplier', 'right', 'strike',
                         'localSymbol']:
                return getattr(self.openOrderRecord.contract, tag)
            elif tag == 'IbridgePyOrder':
                return self
            else:
                print(__name__ + '::IbridgePyOrder::getValue: EXIT, cannot find tag=%s' % (tag,))
                exit()

    @property
    def sid(self):  # Quantopian
        raise None

    @property
    def limit_reached(self):  # Quantopian, return bool
        raise NotImplementedError

    @property
    def stop_reached(self):  # Quantopian, return bool
        raise NotImplementedError

    @property
    def filled(self):  # Quantopian, shares that have been filled.
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.filled
        else:
            return None

    @property
    def filledTime(self):  # Quantopian, the time when this order is filled.
        if self.execDetailsRecord is not None:
            return self.execDetailsRecord.execution.time
        else:
            return None

    @property
    def stop(self):  # Quantopian, stop price
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order.auxPrice
        else:
            return None

    @property
    def limit(self):  # Quantopian, limit price
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order.lmtPrice
        else:
            return self.requestedOrder.lmtPrice

    @property
    def commission(self):  # Quantopian, commission
        if self.openOrderRecord is not None:
            return self.openOrderRecord.orderState.commission
        else:
            return None

    @property
    def amount(self):  # Quantopian, number of shares
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order.totalQuantity
        else:
            return None

    @property
    def remaining(self):  # IbridgePyOrder
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.remaining
        else:
            return None

    @property
    def status(self):  # IbridgePyOrder
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.status
        else:
            return OrderStatus.PRESUBMITTED

    @property
    def avgFillPrice(self):  # IbridgePyOrder
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.avgFillPrice
        else:
            return None

    @property
    def contract(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.contract
        else:
            return None

    @property
    def order(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order
        else:
            return None

    @property
    def orderState(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.orderState
        else:
            return None

    @property
    def parentOrderId(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order.parentId
        else:
            return None

    @property
    def action(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order.action
        else:
            return None
