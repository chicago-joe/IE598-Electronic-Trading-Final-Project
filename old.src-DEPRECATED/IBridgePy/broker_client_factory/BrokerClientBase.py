from IBridgePy import IBCpp
import os
import pandas as pd
from IBridgePy.IbridgepyTools import read_hash_config
import pytz
import datetime as dt
from broker_factory.interactiveBrokers import InteractiveBrokers
from broker_factory.local_broker import LocalBroker
from IBridgePy.constants import BrokerName, LiveBacktest
from sys import exit


class CollectionRealTimePriceRequested:
    def __init__(self):
        self.realTimePriceRequestById = {}

        # keyed by str_security that include exchange and primaryExchange, value = reqId
        # Use str_security to deduplicate
        self.realTimePriceRequestByStrSecurity = {}

    def addReqIdAndStrSecurity(self, reqId, str_security):
        self.realTimePriceRequestById[reqId] = str_security
        self.realTimePriceRequestByStrSecurity[str_security] = reqId

    def deleteReqIdAndStrSecurity(self, reqId, str_security):
        del self.realTimePriceRequestById[reqId]
        del self.realTimePriceRequestByStrSecurity[str_security]

    def findByReqId(self, reqId):
        return self.realTimePriceRequestById[reqId]

    def findByStrSecurity(self, str_security):
        return self.realTimePriceRequestByStrSecurity[str_security]

    def getAllStrSecurity(self):
        return self.realTimePriceRequestByStrSecurity

    def checkIfRequestedByStrSecurity(self, str_security):
        return str_security in self.realTimePriceRequestByStrSecurity


class BrokerClientBase(IBCpp.IBClient):
    """
    !!!! Do not implement __init__, otherwise it will supersede IBCpp.__init__ and cause errors
    """
    versionNumber = '4.4.1'

    # Avoid PEP8 warning of no __init__
    brokerService = None  # So that all clients can pass called-back info to brokerService
    userConfig = None
    log = None
    accountCode = None
    localServerTimeDiff = None
    nextId = None
    connectionGatewayToServer = None
    end_check_list = None
    end_check_list_result = None
    reqDataHist = None
    realTimePriceRequestedList = None
    orderIdToAccountCode = None
    requestResults = None
    timer_start = None
    rootFolderPath = None
    host = None
    port = None
    clientId = None

    # !!!! Do not implement __init__, otherwise it will supersede IBCpp.__init__ and cause errors
    def setup(self, userConfig):
        # these are needed to construct an instance
        self.log = userConfig.log
        self.accountCode = userConfig.accountCode
        self.rootFolderPath = userConfig.rootFolderPath

        self.log.debug(__name__ + '::setup')

        # The time difference between localMachineTime and IB server Time
        # It will be used in get_datetime()
        self.localServerTimeDiff = 0

        self.nextId = 0  # nextValidId, all request will use the same series

        # a flag to show if the connection between IB Gateway/TWS and IB server
        # is good or not
        # The most important usage is to ignore the connection check between
        # IBridgePy and IB Gateway/TWS
        # Must stay here because errorCode will change it
        self.connectionGatewayToServer = False

        # Whenever there is a new request/requests, _request_data() will create
        # a new dataFrame filled by information. Then the newly created dataFrame
        # is passed to self.end_check_list in req_info_from_server() to submit
        # them to IB. The callback information will check self.end_check_list first
        # then, save results as instruction.
        # IbridgepyTools.from_arg_to_pandas_endCheckList defines the
        # the columns of self.end_check_list
        # columns:
        #      str reqId
        #      str status
        #      bool followUp
        #      ReqData reqData
        #      str reqType
        #      bool resendOnFailure
        # pandas dataFrame is used here because it is easier to filter
        # self.end_check_list and self.end_check_list_result will be
        # initialized whenever IBAccountManager.req_info_from_server is called.
        # After prepare_reqId(), the self.end_check_list is keyed by real reqId
        self.end_check_list = pd.DataFrame()

        # self.end_check_list_result is to save callback information
        self.end_check_list_result = {}

        # self.reqDataHist is used to store past ReqData info, same columns as end_check_list
        # so that it is easier to debug.
        self.reqDataHist = pd.DataFrame()

        # record all realTimeRequests to avoid repeat calls
        # Support findByReqId, findByStrSecurity, getAllStrSecurity
        self.realTimePriceRequestedList = CollectionRealTimePriceRequested()

        # Record orderId to accountCode
        self.orderIdToAccountCode = {}

        # Save organized request results here
        # Keyed by reqId, value = result
        # Reset it to {} when request_data makes a new request
        self.requestResults = {}

        self.timer_start = None  # To record response time from sending requests to receiving responses

        # IBCpp function
        # For single account, just input accountCode
        # For multi account, input "All" --- TODO: need to verify it 20181114
        if userConfig.multiAccountFlag:
            self.setAuthedAcctCode('All')
        else:
            self.setAuthedAcctCode(self.accountCode)

        # IBCpp function
        path = os.path.join(self.rootFolderPath, 'IBridgePy', 'hash.conf')
        self.setHashConfig(read_hash_config(path))

    @property
    def localMachineTime(self):
        self.log.debug(__name__ + '::localMachineTime')
        # LocalBroker is inherited from InteractiveBrokers
        # !!! Must be checked at the first place
        if isinstance(self.brokerService, LocalBroker):
            self.log.debug(__name__ + '::localMachineTime: return simulated time')
            return self.brokerService.get_datetime()

        # Even if LocalBroker is inherited from InteractiveBrokers
        # It is better off to explicitly check
        # TODO: integrate other brokers
        elif isinstance(self.brokerService, InteractiveBrokers):
            self.log.debug(__name__ + '::localMachineTime: return real local time')
            return pytz.timezone('UTC').localize(dt.datetime.now())
        else:
            self.log.error(__name__ + '::localMachineTime: EXIT, cannot handle self.brokerService=%s' % (self.brokerService,))
            exit()

    def getAccountCodeFromOrderId(self, orderId):
        self.log.debug(__name__ + '::getAccountCodeFromOrderId: orderId=%s' % (orderId,))
        if orderId in self.orderIdToAccountCode:
            return self.orderIdToAccountCode[orderId]
        else:
            self.log.error(__name__ + '::getAccountCodeFromOrderId: EXIT, orderId=%s does not exist')
            exit()

    def setRequestResults(self, reqId, result):
        self.log.debug(__name__ + '::setRequestResult: reqId=%s' % (reqId,))
        self.requestResults[reqId] = result

    def resetRequestResults(self):
        """
        Reset self.requestResults when request_data makes a new request
        :return:
        """
        self.log.debug(__name__ + '::resetRequestResult')
        self.requestResults = {}
