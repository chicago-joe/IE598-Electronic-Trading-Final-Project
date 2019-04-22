import pytz
import datetime as dt
from IBridgePy.constants import TimeGeneratorType
import pandas as pd
from sys import exit


def make_custom_time_generator(customSpotTimeList):
    for spotTime in customSpotTimeList:
        if not isinstance(spotTime, dt.datetime):
            print(__name__ + '::make_custom_time_generator: spotTime=%s must be a datetime' % (spotTime,))
            exit()
        if spotTime.tzinfo is None:
            print(__name__ + '::make_custom_time_generator: spotTime=%s must have timezone' % (spotTime,))
            exit()
        yield spotTime


def make_auto_time_generator(startingTime, endingTime, freq='1T'):
    """

    :param startingTime:
    :param endingTime:
    :param freq:
    # 1S = 1 second; 1T = 1 minute; 1H = 1 hour; 1D = 1 day
    # https://pandas.pydata.org/pandas-docs/stable/timeseries.html#timeseries-offset-aliases
    :return: a datetime with timezone
    """
    tmp = pd.date_range(startingTime, endingTime, freq=freq, tz=pytz.timezone('US/Eastern'))

    # The 1st time point will be used by broker_client::CallBacks::currentTime so that handle_data will miss 1st time point.
    # The solution is to repeat 1st time point once to compensate
    tmp = [tmp[0]] + list(tmp)
    for ct in tmp:
        yield ct.to_pydatetime()


def make_local_time_generator():
    """

    :return: a datetime with timezone
    """
    while True:
        yield pytz.timezone('UTC').localize(dt.datetime.now())


class Iter:
    def __init__(self, generator):
        self.generator = generator

    def get_next(self):
        return next(self.generator)


class TimeGenerator:
    def __init__(self, timeGeneratorConfig):
        if timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.AUTO:
            self.iter = Iter(make_auto_time_generator(timeGeneratorConfig.startingTime,
                                                      timeGeneratorConfig.endingTime,
                                                      timeGeneratorConfig.freq))
        elif timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.LIVE:
            self.iter = Iter(make_local_time_generator())
        elif timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.CUSTOM:
            self.iter = Iter(make_custom_time_generator(timeGeneratorConfig.custom))

        self.timeNow = None

    def get_current_time(self):
        if self.timeNow is None:
            self.timeNow = self.iter.get_next()
        return self.timeNow

    def get_next_time(self):
        if self.timeNow is None:
            self.timeNow = self.iter.get_next()
        else:
            self.timeNow = self.iter.get_next()
        return self.timeNow
