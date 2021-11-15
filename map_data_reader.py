import urllib.request, re, csv

#import libraries for auto uploading, notifying
import gspread
from oauth2client.service_account import ServiceAccountCredentials

#change each run
todays_date = "may_5"

#*****************************************************************************
#STEP ONE: pull data from isdh site to populate map
#*****************************************************************************

#open isdh data webpage site 
web_page = urllib.request.urlopen("https://www.coronavirus.in.gov/map/covid-19-indiana-universal-report-current-public.json")
contents = web_page.read().decode(errors="replace")
web_page.close()

#isolate segment of json code with needed data for map colorizing
metrics = re.findall('(?<="weekly_statistics").+(?="demographics")', contents, re.DOTALL)

#isolate each data set into a string
district = re.findall('(?<=district": \[).+?(?=])', metrics[0])
weekly_cases_per_100k = re.findall('(?<=per_capita": \[).+?(?=])', metrics[0])
m3b_covid_positive_tests_adm_rate_moving_mean = re.findall('(?<=positivity_rate": \[).+?(?=])', metrics[0])
weekly_positivity_rate_delta = re.findall('(?<=positivity_rate_delta": \[).+?(?=])', metrics[0])

#parse each data set into lists
district = re.findall('[\d]+', district[0])
weekly_cases_per_100k = re.findall("[\d]+", weekly_cases_per_100k[0])
m3b_covid_positive_tests_adm_rate_moving_mean = re.findall("[\d]+.[\d]+", m3b_covid_positive_tests_adm_rate_moving_mean[0])
weekly_positivity_rate_delta = re.findall("[\d]+.[\d]+", weekly_positivity_rate_delta[0])
scores = []
colors = []

#calculate score and color for each district (based on ISDH calculations: https://www.coronavirus.in.gov/map/CountyScoringMapDetails.pdf)
for i in range(len(district)):
    point1 = 0
    point2 = 0  
    
    if 5 <= float(m3b_covid_positive_tests_adm_rate_moving_mean[i]) < 10:
        point1 = 1
    elif 10 <= float(m3b_covid_positive_tests_adm_rate_moving_mean[i]) < 15:
        point1 = 2
    elif float(m3b_covid_positive_tests_adm_rate_moving_mean[i]) >= 15:
        point1 = 3
        
    if 10 <= int(weekly_cases_per_100k[i]) < 100:
        point2 = 1
    elif 100 <= int(weekly_cases_per_100k[i]) < 200:
        point2 = 2
    elif int(weekly_cases_per_100k[i]) >= 200:
        point2 = 3
        
    score = (point1 + point2) / 2
    
    scores.append(score)
    
    #based on score, determine color (based on ISDH rules)
    if score <= 0.5:
        color = "blue"
    elif score <= 1.5:
        color = "yellow"
    elif score <= 2.5:
        color = "orange"
    elif score == 3.0:
        color = "red"
        
    colors.append(color)
    
#*****************************************************************************
#STEP 2: write data to csv sheet
#*****************************************************************************

#write data into csv file
with open('covid_data' + todays_date + '.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["District", "Weekly cases per 100k people", "7-day-positivity rate", "Weekly positivity rate delta", "Score", "Color"])
    for i in range(len(district)):
        writer.writerow([district[i], weekly_cases_per_100k[i], m3b_covid_positive_tests_adm_rate_moving_mean[i], weekly_positivity_rate_delta[i], scores[i], colors[i]])

#*****************************************************************************
#STEP 3: open google sheet, write csv data to sheet
#*****************************************************************************

#use creds to create a client to interact with Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('cterbush-credentials.json', scope)
client = gspread.authorize(creds)

#Find a workbook by name, open first sheet
sheet = client.open("Color Map ISDH Data").sheet1
data = open('covid_data' + todays_date + '.csv', 'r').read()
client.import_csv('1Kj8l81gJNIkfr6RzymcFIc7zoE4jXN8vyHpQkgK6X4c', data)






