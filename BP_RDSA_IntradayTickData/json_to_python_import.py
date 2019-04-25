import pandas

RDSA_1y60m = pandas.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/rdsa-1yr-60min-intraday.json')
RDSA_2y240m = pandas.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/rdsa-2yr-240min-intraday.json')
BP_1y60m = pandas.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/bp-1yr-60min-intraday.json')
BP_2y240m = pandas.read_json('C:/Users/jloss/PycharmProjects/IE598_Final_Project/BP_RDSA_IntradayTickData/bp-2yr-240min-intraday.json')

print(RDSA_1y60m)

