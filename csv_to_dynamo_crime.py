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
import numpy as np
import pandas as pd


AWS_KEY="AKIAIWFYRZWNWCDHI4ZA"
AWS_SECRET="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"
REGION="us-east-2"

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)

table = dynamodb.Table('ChicagoCrime')

print('Reading CSVs')
crimes_2005_2007 = pd.read_csv('/Users/stb/Documents/ECE_4813/Chicago_Crimes_2005_to_2007.csv', error_bad_lines=False)
print('1')
crimes_2008_2011 = pd.read_csv('/Users/stb/Documents/ECE_4813/Chicago_Crimes_2008_to_2011.csv', error_bad_lines=False)
print('2')
crimes_2012_2017 = pd.read_csv('/Users/stb/Documents/ECE_4813/Chicago_Crimes_2012_to_2017.csv', error_bad_lines=False)
print('3')

crimes_2005_2017 = pd.concat(
    [crimes_2005_2007,crimes_2008_2011,crimes_2012_2017],
    ignore_index=False,
    axis=0
)

del crimes_2005_2007
del crimes_2008_2011
del crimes_2012_2017

crimes_2005_2017.drop_duplicates(subset=['ID', 'Case Number'], inplace=True)

crimes_2005_2017.drop(crimes_2005_2017[crimes_2005_2017['Year'] > 2014].index, inplace=True)

crimes_2005_2017.drop(
    [
        'Unnamed: 0',
        'Case Number',
        'IUCR',
        'X Coordinate',
        'Y Coordinate',
        'Updated On',
        'Year',
        'FBI Code',
        'Beat',
        'Ward',
        'Community Area',
        'Location',
        'District',
        'Block',
        'Description',
        'Domestic',
        'Latitude',
        'Longitude'
    ],
    inplace=True,
    axis=1
)
print('Dropped Duplicates')

crimes_2005_2017.Date = pd.to_datetime(crimes_2005_2017.Date, format='%m/%d/%Y %I:%M:%S %p')
crimes_2005_2017.index = pd.DatetimeIndex(crimes_2005_2017.Date)

NUM_CATEGORIES = 20
loc_to_change  = list(crimes_2005_2017['Location Description'].value_counts()[NUM_CATEGORIES:].index)
type_to_change = list(crimes_2005_2017['Primary Type'].value_counts()[NUM_CATEGORIES:].index)

crimes_2005_2017.loc[crimes_2005_2017['Location Description'].isin(loc_to_change) , crimes_2005_2017.columns=='Location Description'] = 'OTHER'
crimes_2005_2017.loc[crimes_2005_2017['Primary Type'].isin(type_to_change) , crimes_2005_2017.columns=='Primary Type'] = 'OTHER'

crimes_2005_2017['Location Description'] = pd.Categorical(crimes_2005_2017['Location Description'])
crimes_2005_2017['Primary Type']         = pd.Categorical(crimes_2005_2017['Primary Type'])


# Crime Types per Day
crimes_count_date = crimes_2005_2017.pivot_table('ID', aggfunc=np.size, columns='Primary Type', index=crimes_2005_2017.index.date, fill_value=0)
crimes_count_date.index = pd.DatetimeIndex(crimes_count_date.index)
for column in list(crimes_count_date):
    crimes_count_date.rename(columns={column: 'Type: ' + column}, inplace=True)

# Total Crime per Day
total_crimes = pd.DataFrame(index=crimes_count_date.index)
total_crimes['Total Crimes'] = crimes_count_date.sum(axis=1)

# Crime Locations per Day
location_count_date = crimes_2005_2017.pivot_table('ID', aggfunc=np.size, columns='Location Description', index=crimes_2005_2017.index.date, fill_value=0)
location_count_date.index = pd.DatetimeIndex(location_count_date.index)
for column in list(location_count_date):
    location_count_date.rename(columns={column: 'Location: ' + column}, inplace=True)

# Combined DataFrame
combined = pd.merge(total_crimes, crimes_count_date, left_index=True, right_index=True)
combined = pd.merge(combined, location_count_date, left_index=True, right_index=True)
combined.index = combined.index.strftime(date_format="%m/%d/%y")

# write records to dynamo db
count = 0
for index, row in zip(combined.to_dict(orient='index'), combined.to_dict(orient='records')):
    count += 1
    if count%1000==0:
        print(count)
    item = {'Date': index}
    item.update(row)

    table.put_item(Item = item)

    time.sleep(0.01) # to accomodate max write provisioned capacity for table
