import requests
import json
from cs50 import SQL
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from numerize import numerize
from helpers import apology, login_required, lookup, usd

import yfinance as yf

from dotenv import load_dotenv

load_dotenv()

#Configure application
app = Flask(__name__)

app.secret_key = 'aaaaaaaaa'

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Opening JSON file
with open('./static/data/tickers.json') as fp:
    stockdata = json.load(fp)

@app.route("/")
def index():
    return render_template("homepage.html")

@app.route("/search", methods=['POST'])
def search():
    #take the query from the front end and find the matches
    #https://www.programiz.com/python-programming/methods/built-in/filter
    #https://www.w3schools.com/python/python_regex.asp


    term = request.form['q']
    filtered_dict = list(filter(lambda stock: (((stock['Name']).upper()).startswith(term.upper())) or ((stock['Symbol']).startswith(term.upper())) , stockdata))

    resp = jsonify(filtered_dict)
    resp.status_code = 200

    return resp

@app.route("/getdata", methods=['GET', 'POST'])
def getdata():
    jsonData = request.get_json()
    ticker = jsonData["symbol"]

    url = "https://yfapi.net/v6/finance/quote"

    querystring = {"symbols": {ticker}}

    headers = {
    'x-api-key': API_KEY
     }

    response = requests.request("GET", url, headers=headers, params=querystring)

    print('stockdata', response.text)

    stockresult = response.get(['result'])

    return render_template('indextest3copy.html', stockdata=stockresult)

@app.route("/junk")
def display_quote():
    symbol = request.args.get('symbol', default="AAPL")

    quote = yf.Ticker(symbol)

    return quote.info


@app.route("/quote", methods=['GET', 'POST'])
def quote():
    symbol = request.args.get('symbol', default="AAPL")

    quote = yf.Ticker(symbol)

    data = quote.info

    print('data', data)

    #format yield
    if data['dividendYield'] is None:
        dividendyield = 0
    else:
        dividendyield = data['dividendYield']*100

    #format rev and earnings growth
    if data['earningsGrowth'] is None:
        earningsgrowth = None
    else:
        earningsgrowth = data['earningsGrowth']*100

    if data['revenueGrowth'] is None:
        revgrowth = None
    else:
        revgrowth = data['revenueGrowth']*100

    #format roe
    if data['returnOnEquity'] is None:
        roe = None
    else:
        roe = data['returnOnEquity']*100

    #format short
    if data['shortPercentOfFloat'] is None:
        shortpercent = 0
    else:
        shortpercent = data['shortPercentOfFloat']*100

    #format target price
    if data['targetMeanPrice'] is None:
        targetUpDown = None
    else:
        targetUpDown = round(((data['targetMeanPrice']/data['currentPrice'])-1)*100,2)

    #format targetupdown
    if data['targetMeanPrice'] is None:
        targetMeanPrice = None
    else:
        targetMeanPrice = data['targetMeanPrice']


    #momentum grade calc
    if data['52WeekChange'] is None and data['fiftyDayAverage'] is not None:
        relstren52wk = round((1+data['currentPrice'])/(1+data['fiftyDayAverage']),2)
        momentum_grade = getMomentumGrade(relstren52wk)
    elif data['52WeekChange'] is None and data['fiftyDayAverage'] is None:
        momentum_grade = getMomentumGrade(.85) 
    else:
        relstren52wk = round((1+data['52WeekChange'])/(1+data['SandP52WeekChange']),2)
        momentum_grade = getMomentumGrade(relstren52wk)

    print('rel stren', relstren52wk)
    print('momograde', momentum_grade)

    #valuation grade calc
    valuation_grade = getValGrade(data['forwardPE'], data['enterpriseToRevenue'])
    print(data['forwardPE'], data['enterpriseToRevenue'])
    print('valgrade', valuation_grade)

    #quality grade calc
    quality_grade = getQualityGrade(data['returnOnEquity'])
    
    #growth grade calc
    growth_grade = getGrowthGrade(data['revenueGrowth'])

    #overall grade calc
    score = calcOverallNumberScore(growth_grade, quality_grade, momentum_grade, valuation_grade)
    print('score', score)

    marketcap= data['marketCap']

    tickerData = {
        'name': data['shortName'],
        'sector': data['sector'],
        'industry': data['industry'],
        'marketcap': numerize.numerize(marketcap),
        'forwardpe': data['forwardPE'],
        'ent2rev': data['enterpriseToRevenue'],
        'debt2equity': data['debtToEquity'],
        'divyield': dividendyield,
        'revgrwth': revgrowth,
        'earngrwth': earningsgrowth,
        'roe': roe,
        'shortpctflt': shortpercent,
        'beta': data['beta'],
        'recommendation': data['recommendationKey'],
        'targetMeanPrice': targetMeanPrice,
        'targetUpDown': targetUpDown,
        'symbol': data['symbol'],
        'price': data['currentPrice'],
        'price_change': round((data['currentPrice']-data['previousClose']),2),
        'percent_change': round(((round((data['currentPrice']-data['previousClose']),2))/data['previousClose'])*100, 2),
        'summary': data['longBusinessSummary'],
        'relstrgrade': momentum_grade,
        'valgrade': valuation_grade,
        'growthgrade': growth_grade,
        'qualitygrade': quality_grade,
        'overallscore': score

    }

    #return data
    return render_template('quote.html', tickerData=tickerData, symbol=symbol)

def getMomentumGrade(avg):
    if avg is None:
        return "B-"
    elif avg >0  and avg <= .75:
        return "D-"
    elif avg >.75  and avg <= .85:
        return "D+"
    elif avg >.85  and avg <= .92:
        return "C-"
    elif avg >.92  and avg <= .98:
        return "C+"
    elif avg > .98 and avg <1.04:
        return "B"
    elif avg > 1.04 and avg <1.12:
        return "A-"
    elif avg > 1.12 and avg <1.20:
        return "A"
    else:
        return "A+"

def getValGrade(fwdpe, entrev):
    if fwdpe is None or entrev is None:
        return "C"
    if fwdpe is None or int(fwdpe) < 0:
        val = getRevVal(entrev)
        return val
    elif int(fwdpe) > 0 and int(fwdpe) <=10:
        return "A+"
    elif int(fwdpe) > 10  and int(fwdpe) <=13:
        return "A-"
    elif int(fwdpe) > 13  and int(fwdpe) <=15:
        return "B+"
    elif int(fwdpe) > 15  and int(fwdpe) <=18:
        return "B"
    elif int(fwdpe) > 18  and int(fwdpe) <=22:
        return "B-"
    elif int(fwdpe) > 22  and int(fwdpe) <=30:
        return "C+"
    elif int(fwdpe) > 30  and int(fwdpe) <=40:
        return "C"
    elif int(fwdpe) > 40  and int(fwdpe) <=60:
        return "C-"
    else:
        return "D"

def getRevVal(entrev):
    if int(entrev) < 1:
        return "B+"
    elif int(entrev) > 1 and int(entrev)<=2:
        return "B"
    elif int(entrev) > 2 and int(entrev)<4:
        return "B-"
    elif int(entrev) > 4 and int(entrev)<8:
        return "C+"
    elif int(entrev) > 8 and int(entrev)<14:
        return "C-"
    elif int(entrev) > 14 and int(entrev)<20:
        return "D+"
    else:
        return "F"

def getGrowthGrade(avg):
    if avg is None:
        return "C"
    elif avg < 0:
        return "D"
    elif avg > 0 and avg < .02:
        return "C"
    elif avg >=.02  and avg < .04:
        return "C+"
    elif avg >=.04  and avg <= .06:
        return "B-"
    elif avg >=.06 and avg <.09:
        return "B+"
    elif avg >= .09 and avg <.15:
        return "A-"
    elif avg > .15 and avg <.25:
        return "A"
    else:
        return "A+"

def getQualityGrade(avg):
    if avg is None:
        return "C"
    elif avg < 0:
        return "F"
    elif avg > 0 and avg < .02:
        return "D-"
    elif avg >=.02  and avg < .05:
        return "D"
    elif avg >=.05 and avg <= .07:
        return "C-"
    elif avg >=.07 and avg <.10:
        return "C"
    elif avg >= .10 and avg <.15:
        return "B-"
    elif avg >= .15 and avg <.20:
        return "B"
    elif avg >= .20 and avg <.25:
        return "B+"
    elif avg >= .25 and avg <.35:
        return "A-"
    elif avg >= .35 and avg <.40:
        return "A"
    else:
        return "A+"

values = {
        "A+": 10,
        "A" :  9,
        "A-": 8.5,
        "B+" : 8,
        "B"  : 7,
        "B-" : 6,
        "C+" : 5,
        "C" : 4,
        "C-"  : 3,
        "D+" : 2,
        "D":  1,
        "D-":  0,
        "F": -1
}

def calcOverallNumberScore(growth_grade, quality_grade, momentum_grade, valuation_grade):
    total = values[growth_grade] + values[quality_grade] + values[momentum_grade] + values[valuation_grade]
    avg = round(total/4)
    score = get_letter_grade(avg)
    return score

def get_letter_grade(val):
    for key, value in values.items():
         if val == value:
             return key


@app.route("/history")
def display_history():
    symbol = request.args.get('symbol', default="AAPL")
    quote = yf.Ticker(symbol)
    hist = quote.history(period="5y", interval="1wk")
    data = hist.to_json()
    data = json.loads(data)
    closed = data['Close']

    priceData = []

    for i in closed:
        price = closed[i]
        priceData.append([int(i), price])

    
    return jsonify(priceData)
    