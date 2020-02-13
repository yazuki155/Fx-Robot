# -*- coding: utf-8 -*-
#Fx市場の各通貨ペアとそれぞれの６つの時間足をフィルタリングし、それぞれ期待される条件ならメールを送信する
# 既存のモジュールをインポート
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.positions as positions
import pandas as pd
# API接続設定のファイルを読み込む
import configparser

#自作クラスをインポート
#インポート方法：ファイル名.クラス名　or from ファイル名 import クラス名
from Gmail_Sender import GmailSender

# APIの設定
config = configparser.ConfigParser()
config.read('./config.ini', encoding='utf-8') # パスの指定が必要
accountID = config['oanda']['accountID']
access_token = config['oanda']['access_token']
api = API(environment="practice",access_token=access_token)

count = 101
time_frame = ['M30','H1','H2','H4','H8','D']
pairs = ["USD_JPY","USD_CHF","CHF_JPY","USD_CAD","CAD_JPY","CAD_CHF","EUR_USD","EUR_JPY","EUR_GBP","EUR_AUD",
"EUR_NZD","EUR_CHF","EUR_CAD","GBP_USD","GBP_JPY","GBP_CHF","GBP_AUD","GBP_NZD","GBP_CAD","AUD_USD","AUD_JPY",
"AUD_NZD","AUD_CHF","AUD_CAD","NZD_USD","NZD_JPY","NZD_CHF","NZD_CAD"]


print(type(accountID))
print(access_token)
for p in range(len(pairs)):
    for tf in range(len(time_frame)):
        params = {
          "count": count,
          "granularity": time_frame[tf]
        }

        # APIから為替レートのストリーミングを取得
        r = instruments.InstrumentsCandles(instrument=pairs[p], params=params)
        api.request(r)

        # dataとしてリストへ変換
        data = []
        for raw in r.response['candles']:
            data.append([raw['time'], raw['volume'], raw['mid']['o'], raw['mid']['h'], raw['mid']['l'], raw['mid']['c']])

        # リストからデータフレームへ変換
        rate = pd.DataFrame(data)
        rate.columns = ['time', 'v', 'o', 'h', 'l', 'c']
        rate = rate.set_index("time")

        #一旦リスト化したことにより、rate.timeの型がdate_time型が失われてただのunicodeになってしまった。
        #なので、pd.to_datetime()を使ってstringのtimeをdate_timeに変換
        rate.index = pd.to_datetime(rate.index,utc=True)
        # インデックスの日付を綺麗にする
        rate.index = pd.to_datetime(rate.index).tz_convert('Asia/Tokyo')
        rate = rate.astype(float)
        #print(str(rate['c'].index[10]))

        for i in range(count-1,count):
            #買い・売りの条件を設定する
            Swing_low = 0
            Swing_high = 0
            current = i
            previous =  i - 1
            #始値終値高値安値をそれぞれ現在、過去で宣言
            openBarPrevious = rate['o'][previous]
            closeBarPrevious = rate['c'][previous]
            highBarPrevious = rate['h'][previous]
            lowBarPrevious = rate['l'][previous]
            openBarCurrent = rate['o'][current]
            closeBarCurrent = rate['c'][current]
            highBarCurrent = rate['h'][current]
            lowBarCurrent = rate['l'][current]
            volumeCurrent = rate['v'][current]
            volumePrevious = rate['v'][previous]
            #bullish engulfing
            #一つ前の(high - open)*0.9 + open を現在の終値が超えてる
            bullishEngulfing = openBarCurrent < openBarPrevious and closeBarCurrent > openBarPrevious and ((highBarPrevious - openBarPrevious)*0.9 + openBarPrevious) < closeBarCurrent
            #一つ前の(open - low)*0.9 + open を現在の終値が下回ってる
            bearishEngulfing = openBarCurrent > openBarPrevious and closeBarCurrent < openBarPrevious and ((openBarPrevious - lowBarPrevious)*0.9 + openBarPrevious) > closeBarCurrent

            sma = rate['c'][i -10 : i].mean()
            dev = round(rate['c'][i -10 : i].std(), 5)
            bollinger_up = sma + dev*2
            bollinger_down = sma - dev*2
            #BB Rules
            bb_bullish = lowBarPrevious <= bollinger_down or lowBarCurrent <= bollinger_down
            bb_bearish = highBarPrevious >= bollinger_up or highBarCurrent >= bollinger_up

            #Swing High/Swing Low rules
            for s in range(count-1):
                close_Previous_1 = rate['c'][s-1]
                close_Previous_2 = rate['c'][s-2]
                close_Previous_3 = rate['c'][s-3]
                close_Previous_4 = rate['c'][s-4]
                high_Previous_2 = rate['h'][s-2]
                low_Previous_2 = rate['l'][s-2]

                #スイングハイ、スイングローの設定
                if high_Previous_2 > closeBarCurrent and high_Previous_2 > close_Previous_1 and high_Previous_2 > close_Previous_3 and high_Previous_2 > close_Previous_4:
                    Swing_high = high_Previous_2
                    #print('----------------------------------------------')
                    #print('Swing_High')
                    #print('時刻：'+str(rate['h'].index[current-2]))
                    #print(Swing_high)

                if low_Previous_2 < closeBarCurrent and low_Previous_2 < close_Previous_1 and low_Previous_2 < close_Previous_3 and low_Previous_2 < close_Previous_4:
                    Swing_low = low_Previous_2
                    #print('----------------------------------------------')
                    #print('Swing_Low')
                    #print('時刻：'+str(rate['c'].index[current-2]))
                    #print(Swing_low)

            #高値安値のブレイクを定義する
            #買いの時は、下ブレイク。(open > Line and low < Line)
            #Swing_bullishは買いのエンゴルフィングバーの時の条件。つまりスイングローを下にブレイクし、買いのエンゴルを表してる。
            Swing_bullish =  (openBarPrevious > Swing_low and lowBarPrevious < Swing_low) or (openBarCurrent > Swing_low and lowBarCurrent < Swing_low)
            #売りの時は、上ブレイク。(open < Line and high > Line)
            #Swing_bearishは売りのエンゴルフィングバーの時の条件。つまりスイングハイを上にブレイクし、売りのエンゴルを表してる。
            Swing_bearish =  (openBarPrevious < Swing_high and highBarPrevious > Swing_high) or (openBarCurrent < Swing_high and highBarCurrent > Swing_high)

            #volume Rules
            #過去100日の出来高の平均値を算出
            v_ma = rate['v'][i -100 : i].mean()
            if volumeCurrent > v_ma or volumeCurrent > volumePrevious:
                volume_rule = True
            else:
                volume_rule = False

            #メールを送信するための追加変数
            pairs_ = pairs[p]
            time_ = str(rate['c'].index[current])
            tf_ = time_frame[tf]
            #GmailSender クラスからインスタンスを作成
            sendMail = GmailSender()
            #Generate Signals
            if bullishEngulfing and bb_bullish and Swing_bullish and volume_rule:

                sendMail.print_data_bull(pairs_,time_,tf_,Swing_low)
                sendMail.create_message_bull(pairs_,time_,tf_,Swing_low)
                sendMail.send_message()

            elif bearishEngulfing and bb_bearish and Swing_bearish and volume_rule:

                sendMail.print_data_bear(pairs_,time_,tf_,Swing_high)
                sendMail.create_message_bear(pairs_,time_,tf_,Swing_high)
                sendMail.send_message()

print(str(rate['c'].index[current]))
print('end')
