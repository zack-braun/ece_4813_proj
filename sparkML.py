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
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.regression import DecisionTreeRegressor
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.feature import VectorIndexer
from pyspark.ml import Pipeline
import json

#Source Code for Regression available here: https://spark.apache.org/docs/1.6.1/ml-classification-regression.html

#Enter AWS Credentials
AWS_KEY=""
AWS_SECRET=""
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

  #combinedDataList = combineData()

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
  result = pandaDF.corr()["Total Crimes"]

  return result.to_json()



@app.route('/linearreg', methods = ['GET'])
def linearRegression():
  #combinedDataList = combineData()
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

  # label data
  input_data = featureddf.rdd.map(lambda x: (x['Total Crimes'], DenseVector([x['Depart'],x['Heat'], x['PrecipTotal'], x['Tavg'], x['Tmax'], x['Tmin']])))
  MLdf = spark.createDataFrame(input_data, ["label", "features"])
  #MLdf.printSchema()
  #MLdf.show(2,False)

  # Define LinearRegression algorithm
  lr = LinearRegression()

  # Fit 2 models, using different regularization parameters
  modelA = lr.fit(MLdf, {lr.regParam:0.3})
  predictionsA = modelA.transform(MLdf)
  #predictionsA.show(1005)

  evaluator = RegressionEvaluator(metricName="rmse")
  RMSE = evaluator.evaluate(predictionsA)
  #print("ModelA: Root Mean Squared Error = " + str(RMSE))

  pandaDF = predictionsA.toPandas()

  actual = pandaDF['label'].tolist()
  prediction = pandaDF['prediction'].tolist()

  return json.dumps({
          'actual': actual,
          'prediction': prediction,
          'RMSE': RMSE
         })

@app.route('/gbtreg', methods = ['GET'])
def gbt():

  #combinedDataList = combineData()
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

  # label data
  input_data = featureddf.rdd.map(lambda x: (x['Total Crimes'], DenseVector([x['Depart'],x['Heat'], x['PrecipTotal'], x['Tavg'], x['Tmax'], x['Tmin']])))
  MLdf = spark.createDataFrame(input_data, ["label", "features"])

  # Automatically identify categorical features, and index them.
  # Set maxCategories so features with > 4 distinct values are treated as continuous.
  featureIndexer =\
      VectorIndexer(inputCol="features", outputCol="indexedFeatures", maxCategories=4).fit(MLdf)

  # Split the data into training and test sets (30% held out for testing)
  (trainingData, testData) = MLdf.randomSplit([0.7, 0.3])

  # Train a GBT model.
  gbt = GBTRegressor(featuresCol="indexedFeatures", maxIter=10)

  # Chain indexer and GBT in a Pipeline
  pipeline = Pipeline(stages=[featureIndexer, gbt])

  # Train model.  This also runs the indexer.
  model = pipeline.fit(MLdf)

  # Make predictions.
  predictions = model.transform(MLdf)

  # Select example rows to display.
  #predictions.select("prediction", "label", "features").show(5)

  # Select (prediction, true label) and compute test error
  evaluator = RegressionEvaluator(
      labelCol="label", predictionCol="prediction", metricName="rmse")
  rmse = evaluator.evaluate(predictions)
  #print("Root Mean Squared Error (RMSE) on test data = %g" % rmse)

  gbtModel = model.stages[1]
  #print(gbtModel)  # summary only

  pandaDF = predictions.toPandas()
  actual = pandaDF['label'].tolist()
  prediction = pandaDF['prediction'].tolist()

  return json.dumps({
          'actual': actual,
          'prediction': prediction,
          'treeSize': str(gbtModel),
          'RMSE': rmse
         })

@app.route('/rfreg', methods = ['GET'])
def rfreg():

  #combinedDataList = combineData()
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

  # label data
  input_data = featureddf.rdd.map(lambda x: (x['Total Crimes'], DenseVector([x['Depart'],x['Heat'], x['PrecipTotal'], x['Tavg'], x['Tmax'], x['Tmin']])))
  MLdf = spark.createDataFrame(input_data, ["label", "features"])

  # Automatically identify categorical features, and index them.
  # Set maxCategories so features with > 4 distinct values are treated as continuous.
  featureIndexer =\
      VectorIndexer(inputCol="features", outputCol="indexedFeatures", maxCategories=4).fit(MLdf)

  # Split the data into training and test sets (30% held out for testing)
  (trainingData, testData) = MLdf.randomSplit([0.7, 0.3])

  # Train a RandomForest model.
  rf = RandomForestRegressor(featuresCol="indexedFeatures")

  # Chain indexer and forest in a Pipeline
  pipeline = Pipeline(stages=[featureIndexer, rf])

  # Train model.  This also runs the indexer.
  model = pipeline.fit(MLdf)

  # Make predictions.
  predictions = model.transform(MLdf)

  # Select example rows to display.
  #predictions.select("prediction", "label", "features").show(5)

  # Select (prediction, true label) and compute test error
  evaluator = RegressionEvaluator(
      labelCol="label", predictionCol="prediction", metricName="rmse")
  rmse = evaluator.evaluate(predictions)
  #print("Root Mean Squared Error (RMSE) on test data = %g" % rmse)

  rfModel = model.stages[1]
  #print(rfModel)  # summary only

  pandaDF = predictions.toPandas()


  actual = pandaDF['label'].tolist()
  prediction = pandaDF['prediction'].tolist()

  return json.dumps({
          'actual': actual,
          'prediction': prediction,
          'treeSize': str(rfModel),
          'RMSE': rmse
         })


@app.route('/dectreereg', methods = ['GET'])
def decTreeReg():
  #combinedDataList = combineData()
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

  # label data
  input_data = featureddf.rdd.map(lambda x: (x['Total Crimes'], DenseVector([x['Depart'],x['Heat'], x['PrecipTotal'], x['Tavg'], x['Tmax'], x['Tmin']])))
  MLdf = spark.createDataFrame(input_data, ["label", "features"])
  #MLdf.show(10,False)
  # Automatically identify categorical features, and index them.
  # We specify maxCategories so features with > 4 distinct values are treated as continuous.
  featureIndexer =\
      VectorIndexer(inputCol="features", outputCol="indexedFeatures", maxCategories=4).fit(MLdf)

  # Split the data into training and test sets (30% held out for testing)
  (trainingData, testData) = MLdf.randomSplit([0.7, 0.3])

  # Train a DecisionTree model.
  dt = DecisionTreeRegressor(featuresCol="indexedFeatures")

  # Chain indexer and tree in a Pipeline
  pipeline = Pipeline(stages=[featureIndexer, dt])

  # Train model.  This also runs the indexer.
  model = pipeline.fit(MLdf)

  # Make predictions.
  predictions = model.transform(MLdf)

  # Select example rows to display.
  #predictions.select("prediction", "label", "features").show(5,False)

  # Select (prediction, true label) and compute test error
  evaluator = RegressionEvaluator(
      labelCol="label", predictionCol="prediction", metricName="rmse")
  rmse = evaluator.evaluate(predictions)
  #print("Root Mean Squared Error (RMSE) on test data = %g" % rmse)

  treeModel = model.stages[1]
  # summary only
  #print(treeModel)

  pandaDF = predictions.toPandas()

  actual = pandaDF['label'].tolist()
  prediction = pandaDF['prediction'].tolist()
  print len(prediction)
  return json.dumps({
          'actual': actual,
          'prediction': prediction,
          'treeSize': str(treeModel),
          'RMSE': rmse
         })

@app.route('/kmeans/<int:cluster>', methods=['GET'])
def kMeans(cluster):

  #combinedDataList = combineData()

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
  #featureddf.printSchema()
  #featureddf.show(2,False)
  # Replace `df` with the new DataFrame
  input_data = featureddf.rdd.map(lambda x: (x['Total Crimes'], DenseVector([x['Depart'],x['Heat'], x['PrecipTotal'], x['Tavg'], x['Tmax'], x['Tmin'], x['Total Crimes']])))
  MLdf = spark.createDataFrame(input_data, ["label", "features"])
  #MLdf.printSchema()
  #MLdf.show(2,False)
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
  #print("Within Set Sum of Squared Errors = " + str(wssse))

  # Shows the result.
  centers = model.clusterCenters()
  #print("Cluster Centers: ")
  centerlist = []
  i = 0;
  for center in centers:
    centerData = {}
    centerData['Center ' + str(i) + ' Depart'] = center[0]
    centerData['Center ' + str(i) + '  Heat'] = center[1]
    centerData['Center ' + str(i) + '  PrecipTotal'] = center[2]
    centerData['Center ' + str(i) + '  Tavg'] = center[3]
    centerData['Center ' + str(i) + '  Tmax'] = center[4]
    centerData['Center ' + str(i) + '  Tmin'] = center[5]
    centerData['Center ' + str(i) + '  Total Crimes'] = center[6]
    centerlist.append(centerData)
    i = i + 1

  transformed = model.transform(MLdf).select("features", "prediction")
  #transformed.printSchema()
  #transformed.show(50,False)
  pandaDF = transformed.toPandas()

  Tavg = []
  precip = []
  crimes = []
  for item in pandaDF['features'].tolist():
    Tavg.append(item[3])
    crimes.append(item[6])
    precip.append(item[2])
  cluster = pandaDF['prediction'].tolist()

  clusters = []
  for x in range(len(centerlist)):
    clusters.append({
      'name': 'Cluster' + str(x),
      'data': [[Tavg[i], crimes[i], precip[i]] for i in range(len(Tavg)) if cluster[i] == x]
      })

  #print(clusters)

  return json.dumps({
                      'clusters': clusters,
                      'clusterCenters': centerlist,
                      'WSSSE': wssse
                     })

# GLOBALS ###########
combinedDataList = combineData();
if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = True, port = 8081)






