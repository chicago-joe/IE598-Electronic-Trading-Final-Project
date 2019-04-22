from sys import exit
import pandas as pd
import pytz
import datetime as dt


def roundToMinTick(price, minTick=0.01):
    """
    for US interactive Brokers, the minimum price change in US stocks is
    $0.01. So if the user made calculations on any price, the calculated
    price must be round using this function to the minTick, e.g., $0.01
    """
    if price < 0.0:
        print(__name__ + '::roundToMinTick: EXIT, negative price =' + str(price))
        exit()
    return int(price / minTick) * minTick


def dt_to_utc_in_seconds(a_dt, showTimeZone=None):
    """
    dt.datetime.fromtimestamp
    the return value depends on local machine timezone!!!!
    So, dt.datetime.fromtimestamp(0) will create different time at different machine
    So, this implementation does not use dt.datetime.fromtimestamp
    """
    # print (__name__+'::dt_to_utc_in_seconds: EXIT, read function comments')
    # exit()
    if a_dt.tzinfo is None:
        if showTimeZone:
            a_dt = showTimeZone.localize(a_dt)
        else:
            a_dt = pytz.utc.localize(a_dt)
            # print(__name__+'::dt_to_utc_in_seconds:EXIT, a_dt is native time, showTimeZone must be not None')
            # exit()
    return (a_dt.astimezone(pytz.utc) - pytz.utc.localize(dt.datetime(1970, 1, 1, 0, 0))).total_seconds()


def utc_in_seconds_to_dt(utcInSeconds, timezoneName='UTC'):
    # return dt.datetime.utcfromtimestamp(epoch).replace(tzinfo=datetime.timezone.utc)
    return pytz.timezone(timezoneName).localize(dt.datetime.utcfromtimestamp(utcInSeconds))


def read_file_to_dataFrame(fullFilePath):
    return pd.read_csv(fullFilePath, index_col=0)
