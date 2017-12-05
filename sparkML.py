from pyspark.mllib.linalg import SparseVector
from pyspark.ml.linalg import DenseVector
from pyspark.mllib.regression import LabeledPoint
from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.types import *
import boto3
import datetime as dt
from operator import itemgetter
from collections import defaultdict
from pyspark.ml.feature import StandardScaler
from pyspark.ml.clustering import KMeans
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
import pandas as pd



#Enter AWS Credentials
AWS_KEY="kry"
AWS_SECRET="sad="
REGION="us-east-2"

# Get the table
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)


# Build the SparkSession
spark = SparkSession.builder \
   .master("local") \
   .appName("Crime") \
   .getOrCreate()
#creates context
sc = spark.sparkContext

app = Flask(__name__, static_url_path="")

def getWeather():
  weatherTable = dynamodb.Table('ChicagoWeather')

  response = weatherTable.scan()

  items = response['Items']

  weatherdataList = []

  if len(items) > 0:
    for item in items:
      data = {}
      data["Date"] = str(item["Date"])
      #data["Date"] = dt.datetime.strptime(item["Date"], "%m/%d/%y")
      data["Depart"] = int(item["Depart"])
      data["Heat"] = int(item["Heat"])
      data["PrecipTotal"] = float(item["PrecipTotal"])
      data["Tavg"] = int(item["Tavg"])
      data["Tmax"] = int(item["Tmax"])
      data["Tmin"] = int(item["Tmin"])
      weatherdataList.append(data)
  return weatherdataList

def getCrime():
  crimeTable = dynamodb.Table('ChicagoCrime')

  response = crimeTable.scan()

  items = response['Items']

  crimedataList = []

  if len(items) > 0:
    for item in items:
      data = {}
      keys = item.keys()
      for key in keys:
        key = str(key)
        if key == 'Date':
          data[key] = dt.datetime.strftime(dt.datetime.strptime(item["Date"], "%m/%d/%y"), "%-m/%-d/%y")
        else:
          data[key] = int(item[key])
      crimedataList.append(data)
  return crimedataList

def combineData():
  crimedataList = getCrime()
  weatherdataList = getWeather()
  combinedDataList = []
  for crimedata in crimedataList:
    combinedData = {}
    for weatherdata in weatherdataList:
      #print weatherdata['Date']
      if crimedata['Date'] == weatherdata['Date']:
        combinedData.update(weatherdata)
        combinedData.update(crimedata)
        combinedDataList.append(combinedData)
        break
  return combinedDataList

@app.route('/corr', methods=['GET'])
def corr():

  combinedDataList = combineData()

  MLlist = []
  for rows in combinedDataList:
    mlData = {}
    mlData['Total Crimes'] = rows['Total Crimes']
    mlData['Depart'] = rows['Depart']
    mlData['Heat'] = rows['Heat']
    mlData['PrecipTotal'] = rows['PrecipTotal']
    mlData['Tavg'] = rows['Tavg']
    mlData['Tmax'] = rows['Tmax']
    mlData['Tmin'] = rows['Tmin']
    MLlist.append(mlData)

  pandaDF = pd.DataFrame(MLlist)

  return jsonify(pandaDF.corr()["Total Crimes"].to_json())



@app.route('/kmeans/<int:cluster>', methods=['GET'])
def kMeans(cluster):

  newDepart = request.args.get('Depart')
  newHeat = request.args.get('Heat')
  newPrecipTotal = request.args.get('PrecipTotal')
  newTavg = request.args.get('Tavg')
  newTmax = request.args.get('Tmax')
  newTmin = request.args.get('Tmin')
  print newDepart

  combinedDataList = combineData()

  MLlist = []
  for rows in combinedDataList:
    mlData = {}
    mlData['Total Crimes'] = rows['Total Crimes']
    mlData['Depart'] = rows['Depart']
    mlData['Heat'] = rows['Heat']
    mlData['PrecipTotal'] = rows['PrecipTotal']
    mlData['Tavg'] = rows['Tavg']
    mlData['Tmax'] = rows['Tmax']
    mlData['Tmin'] = rows['Tmin']
    MLlist.append(mlData)

  #define input data
  inputRDD = sc.parallelize(MLlist)
  featureddf = spark.read.json(inputRDD)
  featureddf.printSchema()
  featureddf.show(2,False)
  # Replace `df` with the new DataFrame
  input_data = featureddf.rdd.map(lambda x: (x['Total Crimes'], DenseVector(x[0:])))
  MLdf = spark.createDataFrame(input_data, ["label", "features"])
  MLdf.printSchema()
  MLdf.show(2,False)
  """
  # Initialize the `standardScaler`
  standardScaler = StandardScaler(inputCol="unscaledFeatures", outputCol="features")

  # Fit the DataFrame to the scaler
  scaler = standardScaler.fit(MLdf)

  # Transform the data in `df` with the scaler
  scaled_df = scaler.transform(MLdf)
  scaled_df.printSchema()

  # Inspect the result
  scaled_df.show(2,False)
  """
  # Trains a k-means model.
  #for i in range(2,100):
  kmeans = KMeans(k=cluster)
  model = kmeans.fit(MLdf)
  centers = model.clusterCenters()

  # Evaluate clustering by computing Within Set Sum of Squared Errors.
  wssse = model.computeCost(MLdf)
  print("Within Set Sum of Squared Errors = " + str(wssse))

  # Shows the result.
  centers = model.clusterCenters()
  print("Cluster Centers: ")
  for center in centers:
      print(center)

  transformed = model.transform(MLdf).select("features", "prediction")
  transformed.printSchema()
  transformed.show(50,False)

  return str(wssse)

if __name__ == '__main__':
    app.run(debug=True, port=8081)



