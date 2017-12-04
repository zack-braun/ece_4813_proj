#!flask/bin/python
from __future__ import print_function
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
from datetime import datetime, timedelta
import boto3
import requests
import json
#Enter AWS Credentials
AWS_KEY="AKIAIWFYRZWNWCDHI4ZA"
AWS_SECRET="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"
REGION="us-east-2"

# Get the table
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)




app = Flask(__name__, static_url_path="")

@app.route('/', methods=['GET'])
def home_page():

    return render_template('index.html')

@app.route('/getPastWeather', methods=['GET'])
#Get past weather data for the past 30 days
def get_past_weather():
  past30Days = []
  for i in range(1, 31):
    #Get date i days ago
    date = str(datetime.now() - timedelta(days=i))[0:10]

    #Pass date to wunderground API
    apiDate = "history_" + datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
    
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

@app.route('/weather', methods=['GET'])
def weather_page():
  return render_template('weather.html')
##COMMENT OUT START
# @app.route('/crime', methods=['GET'])
# def crime_page():

#   #gets Chicagocrime from DB
#   crimeTable = dynamodb.Table('ChicagoCrime')

#   response = crimeTable.scan()

#   items = response['Items']

#   crimedataList = []

#   if len(items) > 0:
#     for item in items:
#       data = {}
#       data["Date"] = str(item["Date"])  #Assuming all "dates" will be of entry YEAR-MONTH-DAY e.g. 2017-12-02  #Assuming all "dates" will be of entry YEAR-MONTH-DAY e.g. 2017-12-02
      # dateString = data["Date"].split('-')
      # data["Year"] = int(dateString[0])
      # data["Month"] = int(dateString[1])
      # data["Day"] = int(datestring[2])

      #rest of data
#       data["Location: ALLEY"] = int(item["Location: ALLEY"])
#       data["Location: ALLEY"] = int(item["Location: APARTMENT"])
#       data["Location: COMMERCIAL / BUSINESS OFFICE"] = float(item["Location: COMMERCIAL / BUSINESS OFFICE"])
#       data["Location: DEPARTMENT STORE"] = int(item["Location: DEPARTMENT STORE"])
#       data["Location: GAS STATION"] = int(item["Location: GAS STATION"])
#       data["Location: GROCERY FOOD STORE"] = int(item["Location: GROCERY FOOD STORE"])
#       data["Location: OTHER"] = int(item["Location: OTHER"])
#       data["Location: PARK PROPERTY"] = int(item["Location: PARK PROPERTY"])
#       data["Location: PARKING LOT/GARAGE(NON.RESID.)"] = int(item["Location: PARKING LOT/GARAGE(NON.RESID.)"])
#       data["Location: RESIDENCE"] = int(item["Location: RESIDENCE"])
#       data["Location: RESIDENCE PORCH/HALLWAY"] = int(item["Location: RESIDENCE PORCH/HALLWAY"])
#       data["Location: RESIDENCE-GARAGE"] = int(item["Location: RESIDENCE-GARAGE"])
#       data["Location: RESTAURANT"] = int(item["Location: RESTAURANT"])
#       data["Location: SCHOOL, PUBLIC, BUILDING"] = int(item["Location: SCHOOL, PUBLIC, BUILDING"])
#       data["Location: SIDEWALK"] = int(item["Location: SIDEWALK"])
#       data["Location: SMALL RETAIL STORE"] = int(item["Location: SMALL RETAIL STORE"])
#       data["Location: STREET"] = int(item["Location: STREET"])
#       data["Location: VEHICLE NON-COMMERCIAL"] = int(item["Location: VEHICLE NON-COMMERCIAL"])
#       data["Total Crimes"] = int(item["Total Crimes"])
#     crimedataList.append(data)

#   #example how to get from DB
#   #data is saved as an Array of JSONs
#     return render_template('crime.html')


# @app.route('/predictive', methods=['GET'])
# def predictive_page():

#     return render_template('predictive.html')
#COMMENT OUT END
#addional routes may be needed for interactivity


if __name__ == '__main__':
    app.run(debug=True, port=8000)

