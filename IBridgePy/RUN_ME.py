# -*- coding: utf-8 -*-
"""
There is a risk of loss when trading stocks, futures, forex, options and other
financial instruments. Please trade with capital you can afford to
lose. Past performance is not necessarily indicative of future results.
Nothing in this computer program/code is intended to be a recommendation, explicitly or implicitly, and/or
solicitation to buy or sell any stocks or futures or options or any securities/financial instruments.
All information and computer programs provided here is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how to use these information and
are solely responsible any consequences of using these information.

If you have any questions, please send email to IBridgePy@gmail.com
All rights reserved.
"""

fileName = 'example_show_positions.py'
# fileName = 'example_get_historical_data.py'
# fileName = 'example_show_real_time_prices.py'
# fileName = 'example_place_order.py'
# fileName = 'example_get_contract_details.py'
# fileName = 'example_get_option_greeks.py'
# fileName = 'example_security_screener.py'

# !!!!!! IMPORTANT  !!!!!!!!!!!!!!!!!
accountCode = 'DU818589'  # You need to change it to your own IB account number
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

'''
In the default mode, handle_data will be called every second.
To run Quantopian algorithms, handle_data will be called every minute
Please use the following runMode
'''
# runMode = 'RUN_LIKE_QUANTOPIAN'

with open("configuration.txt") as f:
    script = f.read()
exec(script)