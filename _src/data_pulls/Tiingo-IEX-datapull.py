TIINGO_API_KEY = 'c552a39f0066da5ba3fa00fc31dcd39e9528a33f'

# reminder to change your API key
#if not TIINGO_API_KEY or (TIINGO_API_KEY == 'c552a39f0066da5ba3fa00fc31dcd39e9528a33f'):
#    raise Exception("Please provide a valid Tiingo API key!")


from tiingo import TiingoClient

config = {
    'api_key': TIINGO_API_KEY,
    'session': True     # reuse HTTP sessions across API calls for bttr performance
    }

client = TiingoClient(config)

# get ticker metadata
# ticker_metadata = client.get_ticker_metadata("AAPL")
# print(ticker_metadata)
# ticker_price = client.get_ticker_price("AAPL", frequency="monthly")
# print(ticker_price)

import matplotlib.pyplot as plt
#%matplotlib inline

ticker_history_df = client.get_dataframe("")
client.list_tickers()