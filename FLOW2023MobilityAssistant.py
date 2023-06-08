#authors: Sean Varie, Cheung Ka Yi (Kaila)

import streamlit as st
import pandas as pd
import numpy as np
import math
import requests
import csv
import json
import time
from datetime import datetime
from beebotte import *
import plotly.express as px # interactive charts
from pprint import pprint

API_KEY = "HjYV37tn0gFaYWqGA3pD394c"
SECRET_KEY = "MKFzf3suZGmMHkEiQV2wHT9c4RCmBpXB"

bclient = BBT(API_KEY, SECRET_KEY)

botteTemp = Resource(bclient, 'ClimateData', 'Temperature')
botteHumid = Resource(bclient, 'ClimateData', 'Humidity')

def parseSensorData():
    temperaturesRead = botteTemp.read()
    humidityRead = botteHumid.read()

    temperatures = [d['data'] for d in temperaturesRead]
    temperatureTS = [datetime.utcfromtimestamp(d['ts']/1000) for d in temperaturesRead]
    tempsDic = {'timeStamp': temperatureTS, 'temps': temperatures}

    humidities = [d['data'] for d in humidityRead]
    humiditiesTS = [datetime.utcfromtimestamp(d['ts']/1000) for d in humidityRead]
    humiditiesDic = {'timeStamp': humiditiesTS, 'humidity': humidities}

    tempsDF=pd.DataFrame(data=tempsDic)
    humiditiesDF = pd.DataFrame(data=humiditiesDic)

    return pd.DataFrame(data=pd.merge(tempsDF, humiditiesDF, how='outer', on=['timeStamp']))


def generateBikeStationsCSV():
    # Creating csv file
    myfile = open('BikeStations.csv', 'w', newline='')
    csvwriter = csv.writer(myfile) # 2. create a csvwriter object
    csvwriter.writerow(['ID','totalSlotNumber','City','Street','Longitude','Latitude']) ## 4. write the header
        


    #Looping on every dock station (57 known)
    for i in range(1,60): 
        # Formating URL
        addedstr=str(i)
        if i < 9:
            addedstr = '0'+addedstr
        url='https://portail-api-data.montpellier3m.fr/bikestation?id=urn%3Angsi-ld%3Astation%3A0'+addedstr+'&limit=1'
        # Sending request
        response = requests.get(url)

        # Translating byte response to Python data structures
        response_json = response.json()
        if len(response_json)>0:
            ## Print Raw Data
            #print(response_json)

            # Extracting data from Json
            data=[response_json[0]['id'].replace(":","%3"),
                response_json[0]['totalSlotNumber']['value'],
                response_json[0]['address']['value']['addressLocality'],
                response_json[0]['address']['value']['streetAddress'],
                response_json[0]['location']['value']['coordinates'][0],
                response_json[0]['location']['value']['coordinates'][1]
                ]
    
            # Print Extracted data
            print(data)

            # Wrinting Values in csv
            csvwriter.writerow(data) # 5. write the rest of the data

    myfile.close()

#returns the distance between the bike station at the 'station' index in the df dataframe and the location of the provided latitude and longitude
def distanceToStation(station: int, latitude: float, longitude: float, df):
    return math.dist([df.iloc[[station]].get('latitude')[station], df.iloc[[station]].get('longitude')[station]], [latitude, longitude])

def getAvailableBikerNumbers(df):
    df['availableBikes'] = np.nan

    for r in df.index:

        url = 'https://portail-api-data.montpellier3m.fr/bikestation?id=urn%3Angsi-ld%3Astation%3A' + df["ID"][r][-3:] + '&limit=1'

        response = requests.get(url)
        bikeStationInfo = response.json()

        df['availableBikes'][r] = bikeStationInfo[0]['availableBikeNumber']['value']
    return df

#finds the closest bike station (with available bikes) from the given dataframe df and returns its' index in df
def findClosestAvailableBike(df, userLatitude, userLongitude):
    bikeDF = getAvailableBikerNumbers(df)

    closestStationWithBikesIndex = 0

    bikeDF['distanceToUser'] = np.nan

    for i in range(len(bikeDF.index)):
        distance = distanceToStation(i, userLatitude, userLongitude, bikeDF)
        if ((distance < distanceToStation(closestStationWithBikesIndex, userLatitude, userLongitude, bikeDF)) and bikeDF['availableBikes'][i] > 0):
            closestStationWithBikesIndex = i

        bikeDF['distanceToUser'][i] = distance

    return closestStationWithBikesIndex


sensorDF = parseSensorData()

with st.form("Sensor Data"):
   st.write("View Temperature or Humidity over time (check for humidity)")
   checkbox_val = st.checkbox("Form checkbox")
   
   submitted = st.form_submit_button("Submit")#submit button
   if submitted:
       if(checkbox_val):
           fig_humidity = st.empty()
           with fig_humidity:
              st.markdown("Humidity (%) over Time")
              humid_fig = px.line(sensorDF, x="timeStamp", y="humidity")
              st.write(humid_fig)
       else:
           fig_temps = st.empty()
           with fig_temps:
              st.markdown("Temperature (C) over Time")
              temps_fig = px.line(sensorDF, x="timeStamp", y="temps")
              st.write(temps_fig)


with st.form("Bike Station Finder"):
   st.write("Bike Station Finder")
   userLatitude = st.number_input('Your Latitude',format='%f',step=0.000001)
   userLongitude = st.number_input('Your Longitude',format='%f',step=0.000001)

   # Every form must have a submit button.
   submitted = st.form_submit_button("Submit")
   if submitted:
       generateBikeStationsCSV()

       bikeStationsDF = pd.read_csv('BikeStations.csv')
       bikeStationsDF.rename(columns={'Latitude':'latitude'}, inplace=True)
       bikeStationsDF.rename(columns={'Longitude':'longitude'}, inplace=True)

       closestBikeIndex = findClosestAvailableBike(bikeStationsDF, userLatitude, userLongitude)
       st.write("The closest bike station with available bikes is at latitude:" + str(bikeStationsDF['latitude'][closestBikeIndex]) + " longitude:" + str(bikeStationsDF['longitude'][closestBikeIndex]))
       st.map(bikeStationsDF.iloc[[closestBikeIndex]])
       
 
API_key = "ff7451e3f8f59f95b1c2e5cdedf711a8"
base_url = "http://api.openweathermap.org/data/2.5/weather?"
 
city_name = 'Montpellier'
Final_url = base_url + "appid=" + API_key + "&q=" + city_name
 
weather_data = requests.get(Final_url).json()

st.write("In Montpellier the temperature is: " + str(weather_data['main']['temp']-273.15) + "C, but feels like: " + str(weather_data['main']['feels_like']-273.15) + "C")
st.write("The weather is: " + weather_data['weather'][0]['description'])






