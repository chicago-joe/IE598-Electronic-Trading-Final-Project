from qtpylib.blotter import Blotter

class MainBlotter(Blotter):
    pass

if __name__ == "__main__":
    blotter = MainBlotter(
        dbhost    = "localhost", # MySQL server
        dbname    = "qtpy",      # MySQL database
        dbuser    = "root",    # MySQL username
        dbpass    = "jlcpartners123!",   # MySQL password
        ibport    = 4002,        # IB port (7496/7497 = TWS, 4001 = IBGateway)
        ibclient = 1,
        orderbook = False,         # fetch and stream order book data
        threads = 6
    )

    blotter.run()