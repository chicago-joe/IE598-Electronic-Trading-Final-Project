from IBridgePy.constants import SecType
from IBridgePy import IBCpp
from sys import exit


class ShowRealTimePriceValidator:
    # https://interactivebrokers.github.io/tws-api/historical_bars.html#hd_request
    def __init__(self):
        self.rules = set()
        for ct in [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.LAST,
                   IBCpp.TickType.OPEN, IBCpp.TickType.HIGH, IBCpp.TickType.HIGH, IBCpp.TickType.LOW, IBCpp.TickType.CLOSE]:
            for secType in [SecType.CASH, SecType.STK, SecType.FUT, SecType.OPT, SecType.CFD, SecType.IND]:
                self.rules.add((secType, ct))
        self.rules.remove((SecType.CASH, IBCpp.TickType.LAST))

    def validate(self, security, param):
        if (security.secType, param) not in self.rules:
            print('ShowRealTimePriceValidator::validate: EXIT, security=%s param=%s fails validation' % (str(security), str(param)))
            exit()


class Validator:
    def __init__(self):
        self.showRealTimePriceValidator = ShowRealTimePriceValidator()



