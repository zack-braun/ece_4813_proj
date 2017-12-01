from pyspark.mllib.linalg import SparseVector
from pyspark.mllib.regression import LabeledPoint
from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.types import *
import boto3


#Enter AWS Credentials
AWS_KEY="AKIAIWFYRZWNWCDHI4ZA"
AWS_SECRET="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"
REGION="us-east-2"

# Get the table
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)



weatherTable = dynamodb.Table('ChicagoWeather')

response = weatherTable.scan()

items = response['Items']

weatherdataList = []

if len(items) > 0:
  for item in items:
    data = {}
    data["Date"] = str(item["Date"])
    data["Depart"] = int(item["Depart"])
    data["Heat"] = int(item["Heat"])
    data["PrecipTotal"] = float(item["PrecipTotal"])
    data["Tavg"] = int(item["Tavg"])
    data["Tmax"] = int(item["Tmax"])
    data["Tmin"] = int(item["Tmin"])
  weatherdataList.append(data)

crimeTable = dynamodb.Table('ChicagoCrime')

response = crimeTable.scan()

items = response['Items']

crimedataList = []

if len(items) > 0:
  for item in items:
    data = {}
    data["Date"] = str(item["Date"])
    data["Location: ALLEY"] = int(item["Location: ALLEY"])
    data["Location: ALLEY"] = int(item["Location: APARTMENT"])
    data["Location: COMMERCIAL / BUSINESS OFFICE"] = float(item["Location: COMMERCIAL / BUSINESS OFFICE"])
    data["Location: DEPARTMENT STORE"] = int(item["Location: DEPARTMENT STORE"])
    data["Location: GAS STATION"] = int(item["Location: GAS STATION"])
    data["Location: GROCERY FOOD STORE"] = int(item["Location: GROCERY FOOD STORE"])
    data["Location: OTHER"] = int(item["Location: OTHER"])
    data["Location: PARK PROPERTY"] = int(item["Location: PARK PROPERTY"])
    data["Location: PARKING LOT/GARAGE(NON.RESID.)"] = int(item["Location: PARKING LOT/GARAGE(NON.RESID.)"])
    data["Location: RESIDENCE"] = int(item["Location: RESIDENCE"])
    data["Location: RESIDENCE PORCH/HALLWAY"] = int(item["Location: RESIDENCE PORCH/HALLWAY"])
    data["Location: RESIDENCE-GARAGE"] = int(item["Location: RESIDENCE-GARAGE"])
    data["Location: RESTAURANT"] = int(item["Location: RESTAURANT"])
    data["Location: SCHOOL, PUBLIC, BUILDING"] = int(item["Location: SCHOOL, PUBLIC, BUILDING"])
    data["Location: SIDEWALK"] = int(item["Location: SIDEWALK"])
    data["Location: SMALL RETAIL STORE"] = int(item["Location: SMALL RETAIL STORE"])
    data["Location: STREET"] = int(item["Location: STREET"])
    data["Location: VEHICLE NON-COMMERCIAL"] = int(item["Location: VEHICLE NON-COMMERCIAL"])
    data["Total Crimes"] = int(item["Total Crimes"])
  crimedataList.append(data)

# Build the SparkSession
spark = SparkSession.builder \
   .master("local") \
   .appName("Linear Regression Model") \
   .config("spark.executor.memory", "1gb") \
   .getOrCreate()

sc = spark.sparkContext

#converts Array of Json
weatherRDD = sc.parallelize(weatherdataList)
crimeRDD = sc.parallelize(crimedataList)


#converts JSON to dataFrame
weatherdf = spark.read.json(weatherRDD)
crimedf = spark.read.json(crimeRDD)

weatherdf.printSchema()
crimedf.printSchema()



