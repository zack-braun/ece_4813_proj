#!flask/bin/python
from __future__ import print_function
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect


app = Flask(__name__, static_url_path="")

@app.route('/', methods=['GET'])
def home_page():

    return render_template('index.html')

@app.route('/weather', methods=['GET'])
def weather_page():
    #Get Appropriate data from Dynamo
    return render_template('weather.html')

@app.route('/crime', methods=['GET'])
def crime_page():

    return render_template('crime.html')

@app.route('/predictive', methods=['GET'])
def predictive_page():

    return render_template('predictive.html')

#addional routes may be needed for interactivity


if __name__ == '__main__':
    app.run(debug=True, port=8000)

