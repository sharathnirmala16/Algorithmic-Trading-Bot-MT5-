import time
import matplotlib.pyplot as plt
import pytz
import MetaTrader5 as mt
import pandas as pd
from datetime import datetime
import math
from stocktrends import Renko
import numpy as np
#import pandas_dtype_efficiency as pd_eff
mt.initialize()

login = 00000000 #Enter your long id 
password = '0000000' #Enter your password
server = 'OctaFX-Demo'

mt.login(login, password, server)
cur_pair = 'AUDUSD'
account_info = mt.account_info()
balance = account_info.balance
leverage = account_info.leverage
lots = 10

print('Balance: $'+ str(balance), ' Leverage:', leverage)

def GetData(cur_pair = 'AUDUSD', n = 500, timeframe = mt.TIMEFRAME_M1):
    mt.initialize()
    rates = mt.copy_rates_from_pos(cur_pair, timeframe, 0, n)
    rates_frame = pd.DataFrame(rates)
    while (rates_frame.shape[0] == 0):
        print('Unable to obtain data, trying again in 60s...')
        time.sleep(60)
        rates = mt.copy_rates_from_pos(cur_pair, timeframe, 0, n)
        rates_frame = pd.DataFrame(rates)
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit = 's')
    rates_frame = rates_frame.drop(columns = ['tick_volume', 'spread', 'real_volume'])
    rates_frame = rates_frame.rename(columns = {'time':'date'})
    return rates_frame

def ConvertUNIXSerToDateTimeSer(unix_time_series):
    temp = []
    for i in range(len(unix_time_series)):
        temp.append(datetime.utcfromtimestamp(unix_time_series[i]).strftime('%Y-%m-%d %H:%M:%S'))
    return pd.Series(temp)

def ConvertUNIXToDateTime(unix_time):
    return datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')

def LotsValue(lots):
    return lots * 100000

def ATR(DF, n = 14):
    df = DF.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis = 1, skipna = False)
    df['ATR'] = df['TR'].ewm(com = n, min_periods = n).mean()
    return df['ATR']

def MACD(data):
    ser1 = data['close'].ewm(com = 12, min_periods = 12).mean()
    ser2 = data['close'].ewm(com = 26, min_periods = 26).mean()
    data['MACD_Line'] = ser1 - ser2
    data['MACD_Signal'] = data['MACD_Line'].ewm(com = 9, min_periods = 9).mean()
    return data

def RenkoDF(DF, SMA_len = 9, box_size = 0.0002):
    df = DF.copy()
    df2 = Renko(df)
    df2.brick_size = box_size
    renko_df = df2.get_ohlc_data()
    renko_df['SMA' + str(SMA_len)] = renko_df['close'].rolling(SMA_len).mean()
    renko_df = MACD(renko_df)
    return renko_df

#1 for Long, -1 for Short, 0 for nothing 
##def CheckLongOrShort(data, i, smaStr):
##    if (data['close'][i] > data[smaStr][i] and data['uptrend'][i] == True and data['uptrend'][i - 1] == True):
##        return 1
##    elif (data['close'][i] < data[smaStr][i] and data['uptrend'][i] == False and data['uptrend'][i - 1] == False):
##        return -1
##    else:
##        return 0

def CheckLongOrShort(data, i):
    if data['MACD_Line'][i] > data['MACD_Signal'][i]:
        return 1
    else:
        return -1

def Confirmation(data, i):
    if (data['uptrend'][i] == True and data['uptrend'][i - 1] == True):
        return 1
    elif (data['uptrend'][i] == False and data['uptrend'][i - 1] == False):
        return -1
    else:
        return 0
    
def BuyOrder(lots = 0.1, cur_pair = 'AUDUSD', comment = 'algo testing buy order'):
    order_request = {
        'action': mt.TRADE_ACTION_DEAL,
        'symbol': cur_pair,
        'volume': lots,
        'type': mt.ORDER_TYPE_BUY,
        'price': mt.symbol_info_tick(cur_pair).bid,
        'deviation': 5,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_FOK,
        'comment': comment
    }
    try:
        order = mt.order_send(order_request)
        return order._asdict()
    except Exception as e:
        print(e)
        empty_dic = {}
        return empty_dic

def BuyOrder(sl, tp, lots = 0.1, cur_pair = 'AUDUSD', comment = 'algo testing buy order'):
    order_request = {
        'sl': sl,
        'tp': tp,
        'action': mt.TRADE_ACTION_DEAL,
        'symbol': cur_pair,
        'volume': lots,
        'type': mt.ORDER_TYPE_BUY,
        'price': mt.symbol_info_tick(cur_pair).bid,
        'deviation': 5,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_FOK,
        'comment': comment
    }
    try:
        order = mt.order_send(order_request)
        return order._asdict()
    except Exception as e:
        print(e)
        empty_dic = {}
        return empty_dic

def CloseBuyOrder(position, lots = 0.1, cur_pair = 'AUDUSD', comment = 'algo testing buy order'):
    order_request = {
        'action': mt.TRADE_ACTION_DEAL,
        'symbol': cur_pair,
        'volume': lots,
        'position': position, 
        'type': mt.ORDER_TYPE_SELL,
        'price': mt.symbol_info_tick(cur_pair).ask,
        'deviation': 5,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_FOK,
        'comment': comment
    }
    try:
        order = mt.order_send(order_request)
        return order._asdict()
    except Exception as e:
        print(e)
        empty_dic = {}
        return empty_dic
        

def SellOrder(lots = 0.1, cur_pair = 'AUDUSD', comment = 'algo testing buy order'):
    order_request = {
        'action': mt.TRADE_ACTION_DEAL,
        'symbol': cur_pair,
        'volume': lots,
        'type': mt.ORDER_TYPE_SELL,
        'price': mt.symbol_info_tick(cur_pair).ask,
        'deviation': 5,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_FOK,
        'comment': comment
    }
    try:
        order = mt.order_send(order_request)
        return order._asdict()
    except Exception as e:
        print(e)
        empty_dic = {}
        return empty_dic

def SellOrder(sl, tp, lots = 0.1, cur_pair = 'AUDUSD', comment = 'algo testing buy order'):
    order_request = {
        'sl': sl,
        'tp': tp,
        'action': mt.TRADE_ACTION_DEAL,
        'symbol': cur_pair,
        'volume': lots,
        'type': mt.ORDER_TYPE_SELL,
        'price': mt.symbol_info_tick(cur_pair).ask,
        'deviation': 5,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_FOK,
        'comment': comment
    }
    try:
        order = mt.order_send(order_request)
        return order._asdict()
    except Exception as e:
        print(e)
        empty_dic = {}
        return empty_dic

def CloseSellOrder(position, lots = 0.1, cur_pair = 'AUDUSD', comment = 'algo testing buy order'):
    order_request = {
        'action': mt.TRADE_ACTION_DEAL,
        'cur_pair': cur_pair,
        'volume': lots,
        'position': position, 
        'type': mt.ORDER_TYPE_BUY,
        'price': mt.symbol_info_tick(cur_pair).bid,
        'deviation': 5,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_FOK,
        'comment': comment
    }
    try:
        order = mt.order_send(order_request)
        return order._asdict()
    except Exception as e:
        print(e)
        empty_dic = {}
        return empty_dic

def PercentChange(init_price, final_price):
    return ((final_price / init_price) - 1) * 100

def MainCode():
    trades_df = pd.DataFrame(columns = ['Buy Datetime', 'Sell Datetime', 'Lots', 'Buy Price', 
                                    'Sell Price', 'Position', "Long or Short", 'Available Capital'])
    active_order_position = 0
    #Data order = ['Buy Datetime', 'Lots', 'Buy Price', 'Order Type', 'Position']
    active_order_data = []
    entered = False
    lots = 0.1
    data = pd.DataFrame(columns = ['date', 'open', 'high', 'low', 'close'])
    take_profit = 0
    stop_loss = 0

    print('Collecting Primary OHLC Data and Converting to Renko...')
    data = GetData()
    print(data.tail(5))

    renko_df = RenkoDF(data)
    print(renko_df.tail(5))

    print('Starting Trading Session...')
    #date contains datetime
    while True:
        data = GetData()
        renko_df = RenkoDF(data)
        current_index = renko_df.shape[0] - 1
    
        if (balance * leverage < LotsValue(lots) * renko_df['close'][current_index]):
            print('Trading Session ended due to insufficient funds.')
            break
    
        condition = CheckLongOrShort(renko_df, current_index)
        confirmation = Confirmation(renko_df, current_index)
        if not entered:
            if condition == 1 and confirmation == 1:
                avg_price = (mt.symbol_info_tick(cur_pair).ask + mt.symbol_info_tick(cur_pair).bid) / 2
                take_profit = avg_price + (0.0002 * 1.5)
                stop_loss = avg_price - (0.0002 * 2.5)
                order = BuyOrder(stop_loss, take_profit, lots, cur_pair)
                exec_time = datetime.now()
                if (len(order) == 1):
                    print(mt.last_error())
                elif (order['retcode'] == 10009):
                    entered = True
                    active_order_position = order['order']
                    print('Active Buy Order: ', active_order_position, exec_time, 'SL: ', stop_loss, 'TP: ', take_profit)
                    active_order_data = [exec_time, lots, order['price'], 'Long', active_order_position]
                else:
                    print('Order Return Code: ', order['retcode'])
                    print('Long TP: ', take_profit, 'SL: ', stop_loss)
            elif condition == -1 and confirmation == -1:
                avg_price = (mt.symbol_info_tick(cur_pair).ask + mt.symbol_info_tick(cur_pair).bid) / 2
                take_profit = avg_price - (0.0002 * 1.5)
                stop_loss = avg_price + (0.0002 * 2.5)
                order = SellOrder(stop_loss, take_profit, lots, cur_pair)
                exec_time = datetime.now()
                if (len(order) == 1):
                    print(mt.last_error())
                elif (order['retcode'] == 10009):
                    entered = True
                    active_order_position = order['order']
                    print('Active Sell Order: ', active_order_position, exec_time, 'SL: ', stop_loss, 'TP: ', take_profit)
                    active_order_data = [exec_time, lots, order['price'], 'Short', active_order_position]
                else:
                    print('Order Return Code: ', order['retcode'])
                    print('Short TP: ', take_profit, 'SL: ', stop_loss)
        else:
            if ((len(mt.positions_get(sumbol = cur_pair)) == 0) and (len(active_order_data) > 0)):
                print('Position Closed at', datetime.now(), '. Available Capital: $', mt.account_info().balance)
                entered = False
                active_order_data = []
        time.sleep(60)

MainCode()
