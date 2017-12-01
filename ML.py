from pyspark.mllib.linalg import SparseVector
from pyspark.mllib.regression import LabeledPoint
from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.types import *



weatherFilename = 'weather.csv'



# Build the SparkSession
spark = SparkSession.builder \
   .master("local") \
   .appName("Linear Regression Model") \
   .config("spark.executor.memory", "1gb") \
   .getOrCreate()

sc = spark.sparkContext

#read in data
rdd = spark.read.csv(
    weatherFilename, header=True
)


# Inspect the first 2 lines
print rdd.take(2)

# Map the RDD to a DF
df = df.rdd.map(lambda line: Row(date=line[0],
                              Tmax=line[1],
                              Tmin=line[2],
                              Tavg=line[3],
                              Depart=line[4],
                              PrecipTotal=line[5],
                              Heat=line[6])).toDF()

# Print the data types of all `df` columns
# df.dtypes

# Print the schema of `df`
df.printSchema()
