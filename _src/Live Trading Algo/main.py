# IE598 Project - Joseph Loss
# An algorithmic trading trading strategy for IBroker's Python API.
#
# Original Templates, Classes, and Parameters located at:
# https://github.com/jamesmawm/High-Frequency-Trading-Model-with-IB
#
from tmp_hft_model import HFTModel


if __name__ == "__main__":
    model = HFTModel(host = 'localhost',
                     port = 4002,
                     client_id = 1,
                     is_use_gateway = False,
                     evaluation_time_secs = 1,
                     resample_interval_secs = '20s')

    model.start(["RDS A", "BP"], 100)

