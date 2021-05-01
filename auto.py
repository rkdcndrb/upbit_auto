import time
import pyupbit
import datetime
import requests
import numpy as np
import pandas as pd

# csv파일 만드는 작업 해야함

# 업비트 및 슬랙 api key
access = "Pp8CYjmLxQirFBZaRHT6FfNFYxi5JwHCxMsNuuko"
secret = "fsEjxJOOibEtCxNkQiCa6Cnw23aE8292V5V8NrxG"
token = "xoxb-1632287813905-1619668906098-Z9Pq47cuKXgPSx5UC3ozsLMs"

# 프로그램 조건
base = 'minute15'
code = 'KRW-UPP'

# 슬랙 메시지 전송
def post_message(token, channel, text):
  response = requests.post("https://slack.com/api/chat.postMessage",
    headers={"Authorization": "Bearer "+token},
    data={"channel": channel,"text": text}
  )

# 매수 시 메시지 ㅋ
def gazeua():
  now = time.localtime()
  today = str(now.tm_year) + '/' + str(now.tm_mon) + '/' + str(now.tm_mday) + ' ' + str(now.tm_hour) + ':' + str(now.tm_min)  
  msg = "[%s]\n매수했어용~ 떡상 가즈아!\n" % (today)
  return msg

# 매수 목표가
def get_target_price(ticker, k):
  df = pyupbit.get_ohlcv(ticker, interval=base, count=2)
  target_price = df.iloc[1]['open'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
  if 1000 < target_price < 10000:
    h = round(target_price % 5)
    target_price += (5 - h)
  elif 10000 < target_price:
    h = round(target_price % 10)
    target_price += (10 - h)
  elif 100 < target_price < 1000:
    target_price = round(target_price)
  return target_price

# 시작 시간
def get_start_time(ticker):
  df = pyupbit.get_ohlcv(ticker, interval=base, count=1)
  start_time = df.index[0]
  return start_time

# 15일 이평선
def get_ma15(ticker):
  df = pyupbit.get_ohlcv(ticker, interval=base, count=15)
  ma15 = df['close'].rolling(15).mean().iloc[-1]
  return ma15

# 5일 이평선
def get_m5(ticker):
  df = pyupbit.get_ohlcv(ticker, interval=base, count=5)
  m5 = df['close'].rolling(5).mean().iloc[-1]
  return m5

# 20일 이평선
def get_m20(ticker):
  df = pyupbit.get_ohlcv(ticker, interval=base, count=20)
  m20 = df['close'].rolling(20).mean().iloc[-1]
  return m20

# 원화 잔고
def get_balance(coin):
  balances = upbit.get_balances()
  for b in balances:
    if b['currency'] == coin:
      if b['balance'] is not None:
        return float(b['balance'])
      else:
        return 0

# 보유 코인 잔고
def get_coinbal(coin):
  bal = upbit.get_balance(coin)
  return bal

# 현재가
def get_current_price(ticker):
  return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

# 종가
def get_close_price(ticker):
  df = pyupbit.get_ohlcv(ticker, interval=base, count=1)
  close_price = df['close'].iloc[-1]
  return close_price

# 로그인
upbit = pyupbit.Upbit(access, secret)
post_message(token, "#upbit-choong", '자동매매 프로그램 시~작 !\n\n건투를 빌어용~~')

# 감시 종목 목록
btc_list = ['KRW-KAVA', 'KRW_DOGE', 'KRW_PXL']

# 여러 조건과 변수
target_msg = 0
price_for_ror = 0
temp_ror = np.array([])
stacked_ror = np.array([])
stacked_date = np.array([])
isLoop = False
save_time = None
notYet = False

start_time = None
end_time = None

while True:
  try:
    now = datetime.datetime.now()
    if notYet == False:
      start_time = get_start_time(code)
      end_time = start_time + datetime.timedelta(minutes=15)
    # if isLoop == False:
    #   save_time = start_time + datetime.timedelta(days=7)
    #   isLoop = True
    if start_time < now < end_time - datetime.timedelta(seconds=10):
      notYet = True
      target_price = get_target_price(code, 0.5)
      time.sleep(0.1)
      m5 = get_m5(code)
      time.sleep(0.1)
      m20 = get_m20(code)
      current_price = get_current_price(code)
      if target_msg == 0:
        m_now = time.localtime()
        today = str(m_now.tm_year) + '/' + str(m_now.tm_mon) + '/' + str(m_now.tm_mday) + ' ' + str(m_now.tm_hour) + ':' + str(m_now.tm_min)
        post_message(token, '#upbit-choong', '[%s]\n종목: %s\n매수목표가: %d\n현재가: %d\n' % (today, code, target_price, current_price))
        price_for_ror = target_price
        target_msg = 1
      if target_price < current_price and m5 > m20 and now < end_time - datetime.timedelta(minutes=1):
        krw = get_balance("KRW")
        if krw > 5000:
          buy_result = upbit.buy_market_order(code, krw * 0.995)
          crn = get_current_price(code)
          msg = gazeua()
          post_message(token, "#upbit-choong", msg + "\n종목: %s\n현재가: %s\n\n행운을 빕니다ㅎㅅㅎ" % (code, crn))
    else:
      notYet = False
      coinbal = get_coinbal(code)
      if coinbal > 0:
        sell_result = upbit.sell_market_order(code, coinbal)
        #종가 및 수익률, 누적수익률 계산
        close_price = get_close_price(code)
        ror = close_price / price_for_ror
        temp_ror = np.append(temp_ror, np.array([ror]))
        stacked = np.round_((temp_ror.cumprod() - 1) * 100, 2)
        stacked_ror = np.append(stacked_ror, np.array([stacked]))
        post_message(token, "#upbit-choong", '매도했어용!\n' + "\n종목: %s\n종가: %s\n수익률: %s\n누적수익률: %s" % (code, str(close_price), str(((ror-1) * 100)), str(stacked[-1])) + r'%' + '\n\n계속파이팅~')
        stacked_date = np.append(stacked_date, np.array(start_time))
      target_msg = 0
    time.sleep(0.1)
  except Exception as e:
    print(e)
    post_message(token, "#upbit-choong", '무슨에러 ?\n%s\n\n' % (e))
    time.sleep(0.1)