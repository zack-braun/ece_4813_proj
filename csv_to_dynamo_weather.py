# Script to write csv records into dynamo db table.

from __future__ import print_function # Python 2/3 compatibility
from __future__ import division #Python 2/3 compatiblity for integer division
import argparse
import boto3
import csv
import time
from random import randint
import datetime
import json

AWS_KEY="AKIAIWFYRZWNWCDHI4ZA"
AWS_SECRET="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"
REGION="us-east-2"

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)

table = dynamodb.Table('ChicagoWeather')

weather_csv = '/Users/stb/Desktop/ece_4813_proj/weather.csv'

# write records to dynamo db
with open(weather_csv) as csv_file:
    tokens = csv.reader(csv_file)
    # read first line in file which contains dynamo db field names
    header = tokens.next()
    # rest of file contain new records
    for token in tokens:
        item = {}
        try:
            for i,val in enumerate(token):
                if val:
                    key = header[i]
                    if 'T' in val:
                        val = 0
                    elif 'M' in val:
                        raise Exception('Missing Data')
                    item[key] = val
            table.put_item(Item = item)
        except:
            pass

    time.sleep(0.01) # to accomodate max write provisioned capacity for table
