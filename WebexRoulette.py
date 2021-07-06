import requests
import random
import itertools  
from itertools import combinations
import re
import datetime as dt
from datetime import datetime, timedelta
import string
import json
from flask import Flask, request, redirect, url_for, render_template
import configparser


## Add your company emails split by departments.
## You can change the numbers and name of the departments that you can find below 

certificationList = ['email@1.com', 'email@1.com']
channelList = ['email@1.com', 'email@1.com']
marketingList = ['email@1.com', 'email@1.com']
renewalsList = ['email@1.com', 'email@1.com']
salesList = ['email@1.com', 'email@1.com']
seList = ['email@1.com', 'email@1.com']
wrpList = ['email@1.com', 'email@1.com']
brokerList = ['email@1.com']

# add all list names without txt here.
listNames = ['wrpList', 'brokerList', 'certificationList', 'channelList', 'marketingList', 'renewalsList', 'salesList', 'seList']

allList =  certificationList + channelList + marketingList + renewalsList + salesList + seList + wrpList + brokerList

meetingsPairsFiles = ["meetingsPairsWeekFirst.txt", "meetingsPairsWeekSecond.txt", "meetingsPairsWeekThird.txt", "meetingsPairsWeekFourth.txt"]

credential = configparser.ConfigParser()
credential.read('cred')

TIMEZONE_STRING = credential['Parameters']['TIMEZONE_STRING']

UTCOFFSET = credential['Parameters']['UTCOFFSET']

START_DATE = credential['Parameters']['START_DATE']

START_TIME = credential['Parameters']['START_TIME']

END_TIME = credential['Parameters']['END_TIME']

MEETINGS_API_URL = credential['Parameters']['MEETINGS_API_URL']

WEBEX_INTEGRATION_CLIENT_ID = credential['Webex']['WEBEX_INTEGRATION_CLIENT_ID']

WEBEX_INTEGRATION_REDIRECT_URI = credential['Webex']['WEBEX_INTEGRATION_REDIRECT_URI']

WEBEX_INTEGRATION_CLIENT_SECRET = credential['Webex']['WEBEX_INTEGRATION_CLIENT_SECRET']

WEBEX_INTEGRATION_SCOPE = credential['Webex']['WEBEX_INTEGRATION_SCOPE']

bearer_meeting_12h = credential['Webex']['WEBEX_ACCESS_TOKEN']

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer_meeting_12h
}

def get_random_alphanumeric_string(letters_count, digits_count):
    sample_str = ''.join((random.choice(string.ascii_letters) for i in range(letters_count)))
    sample_str += ''.join((random.choice(string.digits) for i in range(digits_count)))

    # Convert string to list and shuffle it to mix letters and digits
    sample_list = list(sample_str)
    random.shuffle(sample_list)
    final_string = ''.join(sample_list)
    return final_string

def send_webex_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request

def createTimeFile():
    iteratioNumber = 4
    deltaDays = 7 
    timeList = START_DATE.split('-')
    dateList = []
    for i in range(0, (iteratioNumber)):
        dateObj = dt.datetime(int(timeList[0]), int(timeList[1]), int(timeList[2])) + timedelta(deltaDays * i)
        timeStringStart = dateObj.strftime('%Y-%m-%d') + 'T' + START_TIME + UTCOFFSET
        timeStringEnd = dateObj.strftime('%Y-%m-%d') + 'T' + END_TIME + UTCOFFSET


        dateList.append(timeStringStart + ',' + timeStringEnd)
    
    with open("timeFile.txt", "w") as f:
        for item in dateList:
            f.write(item + '\n')

# %Y-%m-%dT%H:%M:%S
# 2020-06-27T12:00:00+03:00

def createMeetings():
    with open("timeFile.txt", "r") as f:
        dateTime = f.read().split('\n')
        if dateTime[-1] == '':
            dateTime.remove('')
    timeStringNumber = 0
    print("dateTime ", dateTime)
    for meetingsPairs in meetingsPairsFiles:
        with open(meetingsPairs, "r") as f:
            meetingsPairsByDate = f.read()
            createMeeting(meetingsPairsByDate, dateTime[timeStringNumber])
            timeStringNumber += 1

def createMeeting(meetingsPairsByDate, dateTime):
    createMeetingUrl = MEETINGS_API_URL + '/meetings'
    
    print("dateTime ", dateTime)
    metingsIdList = []
    pairsWithDate = []
    if True:
        
        emailList = meetingsPairsByDate.split('\n')
        if emailList[-1] == '':
            emailList.remove('')
        print("emailList", emailList)
        for emails in emailList:
            password = get_random_alphanumeric_string(7, 4)
            startEnd = dateTime.split(',')
            print("startEnd[0] ", startEnd[0])
            print("startEnd[1] ", startEnd[1])
            agenda = "Meeting {}".format(emails)
            body = {
            "title": "Webex Roulette: {}".format(emails),
            "agenda": agenda,
            "password": password,
            "start": startEnd[0],
            "end": startEnd[1],
            "timezone": TIMEZONE_STRING,
            "meetingType": "scheduledMeeting", 
            "enabledAutoRecordMeeting": False,
            "allowAnyUserToBeCoHost": True
            }
            meeting = send_webex_post(createMeetingUrl, body)
            print(meeting)
            metingsIdList.append(meeting['id'])
            pairInfoStr = meeting['id'] + ';' + emails + ';' + dateTime 
            pairsWithDate.append(pairInfoStr)
            #sendingInvite(emails, meeting['id'])
        with open("meetingsId.txt", "a") as m:
            for item in metingsIdList:
                m.write(item + '\n')
        with open("allPairsWithDate.txt", "a") as m:
            for item in pairsWithDate:
                m.write(item + '\n')

def sendingInvite(emails, meetingId):
    AddMeetingInviteeURL = MEETINGS_API_URL + '/meetingInvitees'
    emailList = emails.split(',')
    for email in emailList:
        body = {
	    "meetingId": meetingId,
	    "email": email,
	    "coHost": True
        }
        invite = send_webex_post(AddMeetingInviteeURL, body)
        with open("meetingsInviteLogs.txt", "a") as f:
            f.write(str(invite) + '\n' + meetingId + ' ' + emails + '\n')

def createPairsMonth():
    for pairsFileName in meetingsPairsFiles:
        createPairsWeek(pairsFileName)

def createPairsWeek(pairsFileName):
    monthList = []
    NUMBER_OF_PAIRS_PER_DAY = 7
    with open("allMonthPairs.txt", "r") as p:
        allMonthPairs = p.read().split('\n')
    with open("meetingsPairs.txt", "r") as f:
        lst = f.read().split('\n')
        meetingCount = 0
        while (meetingCount < NUMBER_OF_PAIRS_PER_DAY):
            pair = random.choice(lst)
            pairSplit = pair.split(',')
            #print("pairSplit ", pairSplit)
            emailList = re.findall(r'[\w\.-]+@[\w\.-]+', str(monthList))
            if (emailList.count(pairSplit[0]) < 1) and (emailList.count(pairSplit[1]) < 1) and (pair not in allMonthPairs):

                monthList.append(pair)

                meetingCount += 1

        with open(pairsFileName, "w") as m:
            for item in monthList:
                m.write(item + '\n')
        with open("allMonthPairs.txt", "a") as p:
            for item in monthList:
                p.write(item + '\n')


def createPairs():
    lst = []
    for comb in combinations(allList, 2):
        lst.append(comb)
    print("len all list", len(lst))
    overlayList = []
    
    # Creating pairs with employees/people from one direction/teams that regularly meet with each 
    # other for next deleting these pairs from the final list so people can have a meeting 
    # with new people from other departments
    for lstName in listNames:
        for comb in combinations(lstName, 2):
            overlayList.append(comb)
    for item in overlayList:
        if item in lst:
            lst.remove(item)

    with open("meetingsPairs.txt", "a") as f:
        for item in lst:
            f.write(item[0] + ',' + item[1] + '\n')

def createMeetingsAndFiles():
    with open("meetingsPairs.txt", "r") as f:
        if (len(f.read()) < 2):
            createPairs()
    with open("timeFile.txt", "r") as f:
        if (len(f.read()) < 2):
            createTimeFile()
    with open("allMonthPairs.txt", "r") as f:
        if (len(f.read()) < 2):
            createPairsMonth()
    with open("allPairsWithDate.txt", "r") as f:
        if (len(f.read()) < 2):
            createMeetings()

if __name__ == "__main__": 
    createMeetingsAndFiles()


    
