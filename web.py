from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
import sys
import time
import os
import numpy as np
import codecs
import datetime
import requests
from bs4 import BeautifulSoup
import html2text

localdatatemplate = "date,county,state,fips,cases,deaths,confirmed_cases,confirmed_deaths,probable_cases,probable_deaths"

app = Flask(__name__)

@app.route('/')
def landing():
	return render_template('landing.html')

@app.route('/main')
def main():
	#get county and state
	county = request.args.get("county").capitalize()
	region = request.args.get("state").capitalize()
	country = "US"

	#get country case data
	datareq = requests.get("https://www.worldometers.info/coronavirus/country/"+str(country)+"/")
	datareq = datareq.text

	#format country case data
	country_html = datareq[datareq.index("Coronavirus Cases"):datareq.index("Coronavirus Cases") + 100]
	country_html = BeautifulSoup(country_html)
	country_html = country_html.find("span")
	country_cases = html2text.html2text(str(country_html))
	country_cases = country_cases.replace(",", " ", 10)

	local_area = county
	if local_area == "New York":
		local_area = "New York City"


	#get county case data
	local_data_req = requests.get("https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us-counties.csv")
	local_data_req = local_data_req.text
	try:
		if local_area == '':
			raise ValueError
		local_cases = local_data_req[local_data_req.index(local_area+","+region):local_data_req.index(local_area+","+region)+100]
		local_cases = local_cases.split(",")
		local_cases_confirmed = local_cases[5]
		local_cases_confirmed = "{:,}".format(int(local_cases_confirmed))
	except ValueError:
		local_area = region
		local_data_req = requests.get("https://www.worldometers.info/coronavirus/usa/"+str(region.replace(" ", "-")))
		local_data_req = local_data_req.text
		local_data_req = local_data_req[local_data_req.index("Coronavirus Cases"):local_data_req.index("Coronavirus Cases") + 100]
		local_data_req = BeautifulSoup(local_data_req)
		local_data_req = local_data_req.find("span")
		local_cases = html2text.html2text(str(local_data_req))
		local_cases = local_cases.replace("\n", "", 100)
		local_cases = local_cases.replace(",", "", 100)
		local_cases = "{:,}".format(int(local_cases))
		local_cases_confirmed = local_cases

	local_cases_confirmed = local_cases_confirmed.replace(",", " ", 10)


	#get state case data
	state_case_data = requests.get("https://www.worldometers.info/coronavirus/usa/"+str(region.replace(" ", "-")))
	state_case_data = state_case_data.text
	state_case_data = state_case_data[state_case_data.index("name: 'Cases'"):]
	state_case_data = state_case_data[state_case_data.index("[") + 1:state_case_data.index("]")]
	state_case_data = state_case_data.split(",")
	state_spread_risk = round(100 * ((int(state_case_data[-1]) / int(state_case_data[-2])) - 1), 2)

	red_green_thresh = 0.8

	state_spread_red = state_spread_risk * (255 / red_green_thresh)
	state_spread_green = 255

	if state_spread_red > 255:
		state_spread_red = 255

	if state_spread_risk > red_green_thresh:
		state_spread_green = 255 - ((state_spread_risk - red_green_thresh) * (255 / red_green_thresh))

		if state_spread_green < 0:
			state_spread_green = 0

	print(state_spread_risk)

	state_spread_risk = round(10 * state_spread_risk / (2 * red_green_thresh), 2)

	print(state_spread_risk, state_spread_green, state_spread_red)


	if local_area == region or local_area == '':
		full_local_listing = region
	else:
		full_local_listing = local_area + " County,<br> " + region

	return render_template('main.html', 
		country = country,
		country_cases = country_cases,
		local_area = local_area,
		region = region,
		local_cases_confirmed = local_cases_confirmed,
		full_local_listing = full_local_listing,
		state_spread_risk = state_spread_risk,
		state_spread_red = state_spread_red,
		state_spread_green = state_spread_green)

try:
	app.run(host = sys.argv[1], debug = True, port = int(sys.argv[2])) 
except IndexError:
    raise IndexError("Please enter the target IP as the first argument, and the target port as the second.")

