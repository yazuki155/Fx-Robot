# -*- coding: utf-8 -*-
# インポート
import ssl
import gmail

#GMailでメールを送信するためのクラスを宣言
class GmailSender():
    def __init__(self):
        self.gmail_account = "fx00signal00sender@gmail.com"
        self.gmail_password = "fxsignal1234"
        self.mail_to = "fx00signal00reciever@gmail.com"
        self.subject = ""
        self.body_html = ""


    #買いの場合。フィールドの情報を買いのメッセージに変更。
    def create_message_bull(self,pairs,time,tf,SL):
        # メールデータ(MIME)の作成
        self.subject = "fxシグナル" + pairs + time
        self.body_html = ("""----------------------------------------------
""" +
"""pair:""" + pairs +
"""
time_frame:""" + tf +
"""
時刻:"""  + time +
"""
買いシグナル
""" +
"""Swing_Low:""" + str(SL))


    def create_message_bear(self,pairs,time,tf,SH):
        # メールデータ(MIME)の作成
        self.subject = "fxシグナル" + pairs + time
        self.body_html = ("""----------------------------------------------
""" +
"""pair:""" + pairs +
"""
time_frame:""" + tf +
"""
時刻:""" + time +
"""
売りシグナル
""" +
"""Swing_High:""" + str(SH))


    def print_data_bull(self,pairs,time,tf,SL):
        print('----------------------------------------------')
        print('pair:' + pairs)
        print('time_frame:' + tf)
        print('時刻：' + time)
        print('bullish_Engulfing')
        print('Swing_High:'+ str(SL))

    def print_data_bear(self,pairs,time,tf,SH):
        print('----------------------------------------------')
        print('pair:' + pairs)
        print('time_frame:' + tf)
        print('時刻：' + time)
        print('bearish_Engulfing')
        print('Swing_High:'+ str(SH))


    def send_message(self):
        # Gmailに接続
        client = gmail.GMail(self.gmail_account, self.gmail_password)
        message = gmail.Message(self.subject, to=self.mail_to, text=self.body_html)
        client.send(message)
        client.close()
