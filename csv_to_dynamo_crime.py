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

table = dynamodb.Table('ChicagoCrime')

crimes_2005_2007 = '/Users/stb/Documents/ECE_4813/Chicago_Crimes_2005_to_2007.csv'
crimes_2008_2011 = '/Users/stb/Documents/ECE_4813/Chicago_Crimes_2008_to_2011.csv'
crimes_2012_2017 = '/Users/stb/Documents/ECE_4813/Chicago_Crimes_2012_to_2017.csv'


# clean csvs into
for crime_csv in [crimes_2005_2007,crimes_2008_2011,crimes_2012_2017]:
    print('Next CSV')
    with open(crime_csv) as csv_file:
        tokens = csv.reader(csv_file)
        # read first line in file which contains dynamo db field names
        header = tokens.next()


# write records to dynamo db
for crime_csv in [crimes_2005_2007,crimes_2008_2011,crimes_2012_2017]:
    print('Next CSV')
    with open(crime_csv) as csv_file:
        tokens = csv.reader(csv_file)
        # read first line in file which contains dynamo db field names
        header = tokens.next()
        # rest of file contain new records
        count = 0
        for token in tokens:

            count += 1
            if count%1000==0:
                print(count)

            item = {}
            for i,val in enumerate(token):
                if val:
                    key = header[i]
                    if key:
                        item[key] = val

            table.put_item(Item = item)

            time.sleep(0.01) # to accomodate max write provisioned capacity for table
