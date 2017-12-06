
#!flask/bin/python
from __future__ import print_function
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
from datetime import datetime, timedelta
import boto3
import requests
import json
import ast
#Enter AWS Credentials
AWS_KEY=""
AWS_SECRET=""
REGION="us-east-2"

# Get the table
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)




app = Flask(__name__, static_url_path="")

####Globals
numCluster = 6;

@app.route('/', methods=['GET'])
def home_page():

    return render_template('index.html')


#Weather Routes
@app.route('/getPastWeather', methods=['GET'])
#Get past weather data for the past 30 days
def get_past_weather():
  past30Days = []
  for i in range(0, 5): #Change the '5' to '30' to get weather for past 30 days
    #Get date i days ago
    date = str(datetime.now() - timedelta(days=i))[0:10]
    date = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%Y')

    #Pass date to wunderground API
    apiDate = "history_" + datetime.strptime(date, '%m/%d/%Y').strftime('%Y%m%d')

    result = requests.get('http://api.wunderground.com/api/29c156d422e6a0ff/' + apiDate + '/q/IL/Chicago.json').json()

    #Populate list
    weatherData = {}
    weatherData['Date'] = date
    weatherData['PrecipTotal'] = result['history']['dailysummary'][0]['precipi']
    weatherData['Tavg'] = result['history']['dailysummary'][0]['meantempi']
    weatherData['Tmax'] = result['history']['dailysummary'][0]['maxtempi']
    weatherData['Tmin'] = result['history']['dailysummary'][0]['mintempi']

    past30Days.append(weatherData)
  return render_template('predictive.html', pastWeather = past30Days)

@app.route('/getForecast', methods=['GET'])
#Get weather forecast for next five days including current day
def get_forecast():
  result = requests.get('https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20weather.forecast%20where%20woeid%20in%20(select%20woeid%20from%20geo.places(1)%20where%20text%3D%22chicago%2C%20IL%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys').json()

  forecast = []
  for i in range(0,5):
  	date = str(datetime.now() + timedelta(days=i))[0:10]
  	date = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%Y')

  	day = {}
  	day['Date'] = date
  	day['Tmin'] = result['query']['results']['channel']['item']['forecast'][i]['low']
  	day['Tmax'] = result['query']['results']['channel']['item']['forecast'][i]['high']
  	day['Tavg'] = str((int(day['Tmin']) + int(day['Tmax']))/2)
  	forecast.append(day)
  return render_template('predictive.html', forecast = forecast)

@app.route('/weatherdata', methods=['GET'])
def get_data_weather():
  #Get Appropriate data from Dynamo
  weatherTable = dynamodb.Table('ChicagoWeather')

  response = weatherTable.scan()

  items = response['Items']

  weatherdataList = []
  dateString = []
  if len(items) > 0:
    for item in items:
      data = {}
      #split date into Y-M-D for chart
      dateString = str(item["Date"]).split('/')
      for i in range(0, len(dateString)):
        if len(dateString[i]) < 2:
          dateString[i] = '0' + dateString[i]
      data["Date"] = int(dateString[2] + dateString[0] + dateString[1])  #for sorting x-axis
      data["Month"] = int(dateString[0])
      data["Day"] = int(dateString[1])
      data["Year"] = int('20' + dateString[2])

      #other data
      data["Depart"] = float(item["Depart"])
      data["Heat"] = int(item["Heat"])
      data["PrecipTotal"] = float(item["PrecipTotal"])
      data["Tavg"] = int(item["Tavg"])
      data["Tmax"] = int(item["Tmax"])
      data["Tmin"] = int(item["Tmin"])
      weatherdataList.append(data)
    return jsonify(sorted(weatherdataList, key=lambda k: k["Date"]))
  else:
    return jsonify({'Date': 0, 'Year': 0, 'Month': 0, 'Day': 0, 'Depart': 0, 'Heat': 0, 'PrecipTotal': 0, 'Tavg': 0, 'Tmax': 0, 'Tmin': 0})

@app.route('/weatherdata/<dataField>', methods=['GET'])
def get_field_data_weather(dataField):
  #Get Appropriate data from Dynamo
  weatherTable = dynamodb.Table('ChicagoWeather')

  response = weatherTable.scan()

  items = response['Items']

  weatherdataList = []
  dateString = []
  if len(items) > 0:
    for item in items:
      data = {}
      #split date into Y-M-D for chart
      dateString = str(item["Date"]).split('/')
      for i in range(0, len(dateString)):
        if len(dateString[i]) < 2:
          dateString[i] = '0' + dateString[i]
      data["Date"] = int(dateString[2] + dateString[0] + dateString[1])  #for sorting x-axis
      data["Month"] = int(dateString[0])
      data["Day"] = int(dateString[1])
      data["Year"] = int('20' + dateString[2])

      #other data
      data[dataField] = float(item[dataField])
      weatherdataList.append(data)
    return jsonify(sorted(weatherdataList, key=lambda k: k["Date"]))
  else:
    return jsonify({'Date': 0, 'Year': 0, 'Month': 0, 'Day': 0, dataField: 0})

@app.route('/weather', methods=['GET'])
def weather_page():
  return render_template('weather.html')


#Crime Routes
@app.route('/crimedata', methods=['GET'])
def get_data_crime():
  #Get Appropriate data from Dynamo
  crimeTable = dynamodb.Table('ChicagoCrime')
  
  response = crimeTable.scan()
 
  items = response['Items']
 
  crimedataList = []
  dateString = []
  if len(items) > 0:
    for item in items:
      data = {}
      #split date into Y-M-D for chart
      dateString = str(item["Date"]).split('/')
      for i in range(0, len(dateString)):
        if len(dateString[i]) < 2:
          dateString[i] = '0' + dateString[i]
      data["Date"] = int(dateString[2] + dateString[0] + dateString[1])  #for sorting x-axis
      data["Month"] = int(dateString[0])
      data["Day"] = int(dateString[1])
      data["Year"] = int('20' + dateString[2])
  
      #other data
      keys = item.keys()
      for key in keys:
        if key == 'Date':
          pass
        else:
          data[key] = int(item[key])
      crimedataList.append(data)
    return jsonify(sorted(crimedataList, key=lambda k: k["Date"]))

@app.route('/crimedata/<dataField>', methods=['GET'])
def get_field_data_crime(dataField):
  #Get Appropriate data from Dynamo

  #Handle invalid characters in url, i.e. '/', ',', ' '
  dataFieldNew = dataField.replace('Location_', 'Location: ')
  dataFieldNew = dataFieldNew.replace('Type_', 'Type: ')
  dataFieldNew = dataFieldNew.replace('_s_', ' / ')
  dataFieldNew = dataFieldNew.replace('_c_', ', ')
  dataFieldNew = dataFieldNew.replace('_p1_', '(')
  dataFieldNew = dataFieldNew.replace('_p2_', ')')
  dataFieldNew = dataFieldNew.replace('_x_', '.')
  dataFieldNew = dataFieldNew.replace('_h_', '-')
  dataFieldNew = dataFieldNew.replace('__', '/')
  dataFieldNew = dataFieldNew.replace('_', ' ')

  crimeTable = dynamodb.Table('ChicagoCrime')

  response = crimeTable.scan()

  items = response['Items']

  crimedataList = []
  dateString = []
  if len(items) > 0:
    for item in items:
      data = {}
      #split date into Y-M-D for chart
      dateString = str(item["Date"]).split('/')
      for i in range(0, len(dateString)):
        if len(dateString[i]) < 2:
          dateString[i] = '0' + dateString[i]
      data["Date"] = int(dateString[2] + dateString[0] + dateString[1])  #for sorting x-axis
      data["Month"] = int(dateString[0])
      data["Day"] = int(dateString[1])
      data["Year"] = int('20' + dateString[2])

      #other data
      data[dataField] = float(item[dataFieldNew])
      crimedataList.append(data)
    return jsonify(sorted(crimedataList, key=lambda k: k["Date"]))
  else:
    return jsonify({'Date': 0, 'Year': 0, 'Month': 0, 'Day': 0, dataField: 0})

#Public Areas/Others Crimes Page
@app.route('/crime', methods=['GET'])
def crimedata_page():
  return render_template('crime.html')

#Residential Crimes Page
@app.route('/crimeResidential', methods=['GET'])
def crimeResidentialdata_page():
  return render_template('crimeResidential.html')

#Stores/Restaurants Crimes Page
@app.route('/crimeStores', methods=['GET'])
def crimeStoresdata_page():
  return render_template('crimeStores.html')

#Crime Types Page 1
@app.route('/crimeTypes1', methods=['GET'])
def crimeTypes1data_page():
  return render_template('crimeTypes1.html')

#Crime Types Page 2
@app.route('/crimeTypes2', methods=['GET'])
def crimeTypes2data_page():
  return render_template('crimeTypes2.html')

#Crime Types Page 3
@app.route('/crimeTypes3', methods=['GET'])
def crimeTypes3data_page():
  return render_template('crimeTypes3.html')

#Crime Types Page 4
@app.route('/crimeTypes4', methods=['GET'])
def crimeTypes4data_page():
  return render_template('crimeTypes4.html')

#Total Crimes Chart
@app.route('/crimeTotal', methods=['GET'])
def crimeTotaldata_page():
  return render_template('crimeTotal.html')


#Predictive Routes
@app.route('/kmeansClusters', methods = ['GET'])
def kmeansClusters():
  global numCluster
  numCluster = request.args.get('quantity')
  return render_template('predictive.html')



@app.route('/predictivedata', methods=['GET'])
def get_data_predictive():
  #print(numCluster)
  #Get Appropriate data from Spark Flask App
  r = requests.get('http://0.0.0.0:8081/kmeans/' + str(numCluster))
  kmeansData = ast.literal_eval(r.text)
  r = requests.get('http://0.0.0.0:8081/linearreg')
  linRegData = ast.literal_eval(r.text)
  r = requests.get('http://0.0.0.0:8081/corr')
  corrData = ast.literal_eval(r.text)
  r = requests.get('http://0.0.0.0:8081/gbtreg')
  gbtRegData = ast.literal_eval(r.text)
  r = requests.get('http://0.0.0.0:8081/rfreg')
  rfRegData = ast.literal_eval(r.text)
  r = requests.get('http://0.0.0.0:8081/dectreereg')
  dectreeRegData = ast.literal_eval(r.text)


  print(linRegData)
  result = jsonify({
          'LinRegData': linRegData,
          'kmeansData': kmeansData,
          'corrData': corrData,
          'gbtRegData': gbtRegData,
          'rfRegData': rfRegData,
          'dectreeRegData': dectreeRegData
          })
  return result


@app.route('/predictive', methods=['GET'])
def predictive_page():
  return render_template('predictive.html')

#addional routes may be needed for interactivity


if __name__ == '__main__':
    app.run(debug=True, port=8000)

