4/25/2019
IE 598 – Electronic Trading
University of Illinois at Urbana-Champaign

## Statistical Arbitrage Trading in Python
#### InteractiveBrokers Paper-Trader Algorithm
######*by  Ruozhong Yang &  Joseph Loss*


For our final project, we are going to develop, back-test, and implement an algorithmic trading strategy through the InteractiveBrokers Python API software. 

IB live-market data subscriptions:
1. Streaming real-time quotes for NYSE (CTA/Network A), AMEX
(CTA/Network B), NASDAQ (UTP/Network C), and OPRA (US
Options). 
   - Includes top-of-book data.

Algorithm Backtesting
The official IB API software does not support back-testing.
For our backtesting and profitability analysis, we've selected the *__backtrader__* Python Library. 
Find out more here: [https://backtrader.com/](https://backtrader.com/)
- Data streaming and impressive back-testing capabilities on both
historical data and real-time data.
- Real-time and historical data providers include InteractiveBrokers,
Quandl, Quantopian, Yahoo, and several others.

Other Python Libraries under consideration: 
- IbPy
- PyAlgoTrader 
- IBridgePy