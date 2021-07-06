from app import app
import datetime as dt
from pprint import pprint
import os, time
import requests
import json
import sys
import subprocess
import os
import random
import atexit
import datetime as dt
from datetime import datetime, timedelta
from flask import Flask
from flask import request, redirect, url_for, render_template
import configparser
import re
import sqlite3

import random
import itertools  
from itertools import combinations
import datetime as dt
from datetime import datetime, timedelta
import string

import urllib.parse


from WebexRoulette import *

# read variables from config
credential = configparser.ConfigParser()
credential.read('cred')

######################
MEETINGS_API_URL = credential['Parameters']['MEETINGS_API_URL']

WEBEX_INTEGRATION_CLIENT_ID = credential['Webex']['WEBEX_INTEGRATION_CLIENT_ID']

WEBEX_INTEGRATION_REDIRECT_URI = credential['Webex']['WEBEX_INTEGRATION_REDIRECT_URI']

WEBEX_INTEGRATION_CLIENT_SECRET = credential['Webex']['WEBEX_INTEGRATION_CLIENT_SECRET']

WEBEX_INTEGRATION_SCOPE = credential['Webex']['WEBEX_INTEGRATION_SCOPE']

#WEBEX_USER_AUTH_URL = credential['Webex']['WEBEX_USER_AUTH_URL']

######################
refresh_token = ''
bearer_bot = credential['Webex']['WEBEX_TEAMS_TOKEN']
bearer_meeting = credential['Webex']['WEBEX_MEETINGS_TOKEN']
botEmail = credential['Webex']['WEBEX_BOT_EMAIL']
ROOM_ID_REPORT = credential['Webex']['WEBEX_TEAMS_ROOM_ID_REPORT']
WEBEX_TEAMS_ROOM_ID_REPORT = credential['Webex']['WEBEX_TEAMS_ROOM_ID_REPORT']
# WebhookUrl
webhookUrl = credential['Webex']['WEBEX_WEBHOOK_URL']

TIMEZONE_STRING = credential['Parameters']['TIMEZONE_STRING']

UTCOFFSET = credential['Parameters']['UTCOFFSET']

START_DATE = credential['Parameters']['START_DATE']

START_TIME = credential['Parameters']['START_TIME']

END_TIME = credential['Parameters']['END_TIME']

MEETINGS_API_URL = credential['Parameters']['MEETINGS_API_URL']

headers_bot = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer_bot
}

meeting_headers = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer_meeting
}

#### Functions

def createWebhook(bearer, webhookUrl):
    hook = True
    botWebhooks = send_webex_get("https://webexapis.com/v1/webhooks")["items"]
    for webhook in botWebhooks:
        if webhook["targetUrl"] == webhookUrl:
            hook = False
    if hook:
        dataWebhook = {
        "name": "Messages collab bot Webhook",
        "resource": "messages",
        "event": "created",
        "targetUrl": webhookUrl
        }
        dataWebhookCard = {
            "name": "Card Report collab bot Webhook",
            "targetUrl": webhookUrl,
            "resource": "attachmentActions",
            "event": "created"
        }
        send_webex_post("https://webexapis.com/v1/webhooks/", dataWebhook)
        send_webex_post("https://webexapis.com/v1/webhooks/", dataWebhookCard)
    print("Webhook status: done")

def deleteWebHooks(bearer, webhookUrl):
    webhookURL = "https://api.ciscospark.com/v1/webhooks/"
    botWebhooks = send_webex_get(webhookURL)["items"]
    for webhook in botWebhooks:
        send_webex_delete(webhookURL + webhook["id"])

def send_webex_get(url, payload=None,js=True):

    if payload == None:
        request = requests.get(url, headers=headers_bot)
    else:
        request = requests.get(url, headers=headers_bot, params=payload)
    if js == True:
        if request.status_code == 200:
            try:
                r = request.json()
            except json.decoder.JSONDecodeError:
                print("Error JSONDecodeError")
                return("Error JSONDecodeError")
            return r
        else:
            print (request)
            return ("Error " + str(request.status_code))
    return request

def send_webex_delete(url, payload=None):
    if payload == None:
        request = requests.delete(url, headers=headers_bot)
    else:
        request = requests.delete(url, headers=headers_bot, params=payload)

def send_webex_post_meeting(url, data):
    request = requests.post(url, json.dumps(data), headers=meeting_headers).json()
    return request

def send_webex_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers_bot).json()
    return request

def postLogInSpace(reportText):
    body = {
        "roomId": WEBEX_TEAMS_ROOM_ID_REPORT,
        "markdown": reportText,
        "text": "This text would be displayed by Webex Teams clients that do not support markdown."
    }
    send_webex_post('https://webexapis.com/v1/messages', body)

def postNotificationToPerson(reportText, personEmail):
    body = {
        "toPersonEmail": personEmail,
        "markdown": reportText,
        "text": "This text would be displayed by Webex Teams clients that do not support markdown."
        }
    send_webex_post('https://webexapis.com/v1/messages', body)

def postCard(personEmail):
    # open and read data from file as part of body for request
    with open("cardText.txt", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()
    print("POST CARD TO ", personEmail)

def postTimeDateCard(personEmail, meetingId):
    # open and read data from file as part of body for request
    with open("cardText.txt", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
        data = data.replace('MEETING_ID', meetingId)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()
    
    reportText = "Post TimeDateCard to " + personEmail
    postLogInSpace(reportText)

def askForNewTime(emploeeEmailForNewTime, personName, personEmail, oldDateTime, newDateTime, meetingId, newDateTimePeriod):
    with open("cardText_newTime.txt", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', emploeeEmailForNewTime)
        data = data.replace('MEETING_ID', meetingId).replace('PERSON_NAME', personName + ' (' + personEmail + ')' ).replace('OLD_DATE', oldDateTime).replace('NEW_DATE', newDateTime).replace('TIME_PERIOD', newDateTimePeriod)

    # Add encoding, if you use non-Latin characters                                                                                                                                                            
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()
    reportText = "A new date and time proposal has been submitted. The answer will be announced in a separate message"
    postNotificationToPerson(reportText, personEmail)


def get_random_alphanumeric_string(letters_count, digits_count):
    sample_str = ''.join((random.choice(string.ascii_letters) for i in range(letters_count)))
    sample_str += ''.join((random.choice(string.digits) for i in range(digits_count)))

    # Convert string to list and shuffle it to mix letters and digits
    sample_list = list(sample_str)
    random.shuffle(sample_list)
    final_string = ''.join(sample_list)
    return final_string

def getNewToken():

    global refresh_token
    headers_token = {
        "Content-type": "application/x-www-form-urlencoded"
    }
    body = {
        'grant_type': 'refresh_token',
        'client_id': WEBEX_INTEGRATION_CLIENT_ID,
        'client_secret': WEBEX_INTEGRATION_CLIENT_SECRET,
        'refresh_token': refresh_token
    }
    get_token = requests.post(MEETINGS_API_URL + "/access_token?", headers=headers_token, data=body)
    print("get_token ", get_token.text)
    webex_access_token = get_token.json()['access_token']
    newRefreshToken = get_token.json()['refresh_token']
    global bearer_meeting
    bearer_meeting = webex_access_token
    refresh_token = newRefreshToken
    return (bearer_meeting)

def createMeetingForPair(emails, dateTime):
    createMeetingUrl = MEETINGS_API_URL + '/meetings'
    if True:
        
        if True:
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
            "allowAnyUserToBeCoHost": False
            }
            try:
                meeting = send_webex_post_meeting(createMeetingUrl, body)
                print("Metting (createMeetingForPair) ", meeting)
                newPairInfoStr = meeting['id'] + ';' + emails + ';' + dateTime 
            except KeyError:
                getNewToken()
                meeting = send_webex_post_meeting(createMeetingUrl, body)
                print("Metting (createMeetingForPair) ", meeting)
                newPairInfoStr = meeting['id'] + ';' + emails + ';' + dateTime 
            reportText = '# Сreate meeting ' + meeting['id'] + ' ' + emails + '\n'
            postLogInSpace(reportText)
            sendingInvite(emails, meeting['id'])
            return newPairInfoStr


def sendingInvite(emails, meetingId):
    AddMeetingInviteeURL = MEETINGS_API_URL + '/meetingInvitees'
    emailList = emails.split(',')
    invites = ''
    for email in emailList:
        body = {
	    "meetingId": meetingId,
	    "email": email,
	    "coHost": False
        }
        # True
        invite = send_webex_post_meeting(AddMeetingInviteeURL, body)
        invites += str(invite) + '\n'
    
    # write to report log space
    reportText = '# sendingInvite \n' + invites + meetingId + ' ' + emails + '\n'
    postLogInSpace(reportText)

def removeMeetingID(pair):
    pair = pair.split(';')
    pair.pop(0)
    pairStr = " "
    return (pairStr.join(pair))

def printMeetingList(personEmail):
    #  s = "meetingID;e@1.ua,e@2.ua;Time\ne@3.ua,e@4.ua,Time\ne@3.ua,e@5.ua,Time"
    with open('allPairsWithDate.txt', 'r') as f:
        allPairs = f.read().split('\n')
    meetingPair = [i for i in allPairs if personEmail in i]
    n = 1
    reportText = "Enter the Meeting number (which time, and/or date you want to change) \n"
    for pair in meetingPair:
        pair = removeMeetingID(pair)
        reportText = reportText + " Meeting number: {} \n Pair: {} \n".format(n, pair)
        n += 1
    reportText += "\n Enter the Meeting number (which time, and/or date you want to change)" 
    body = {
        "toPersonEmail": personEmail,
        "markdown": reportText,
        "text": "This text would be displayed by Webex Teams clients that do not support markdown."
    }
    send_webex_post('https://webexapis.com/v1/messages', body)

def newBookingDate(personId, meetingId, date, cardTime):
    person = send_webex_get('https://api.ciscospark.com/v1/people/{}'.format(personId))
    personEmail = person["emails"][0]
    personName = person["displayName"]

    with open('allPairsWithDate.txt', 'r') as f:
        allPairs = f.read().split('\n')
    meetingPair = [i for i in allPairs if personEmail in i]
    for itemPair in meetingPair:
        if meetingId in itemPair:
            index = meetingPair.index(itemPair)
            break 
    pair = meetingPair[index]
    print("Pair ",pair)
    mPair = pair.split(';')
    emploeeEmailForNewTime = mPair[1].replace(personEmail,'').replace(',','')
    print("emploeeEmailForNewTime ", emploeeEmailForNewTime)
    # sample of dateTime string: 2021-04-03T15:10:00+03:00,2021-04-03T15:40:00+03:00
    oldDateTime = mPair[2][:16].replace('T',' time: ') + '-' + mPair[2][37:42]
    if '/' in date:
        date = date.split('/')
        date = date[2] + '-' + date[1] + '-' + date[0]
    newDateTime = '(year-month-day format) ' + date + ' time: ' + cardTime
    dateList = date.split('-')
    timeList = cardTime.split(':')
    dateObj = dt.datetime(int(dateList[0]), int(dateList[1]), int(dateList[2]), int(timeList[0]), int(timeList[1])) + timedelta(minutes=30)
    endMeetingTime = dateObj.strftime('%Y-%m-%dT%H:%M:%S') + UTCOFFSET
    newDateTimePeriod = date + 'T' + cardTime + ':00' + UTCOFFSET + ',' + endMeetingTime
    askForNewTime(emploeeEmailForNewTime, personName, personEmail, oldDateTime, newDateTime, meetingId, newDateTimePeriod)

    # write to report log space
    reportText = '# askForNewTime \n' + personName + ' ask for newDateTimePeriod ' + newDateTimePeriod + '\n'
    postLogInSpace(reportText)

def newTimeAnswerGet(personId, meetingId, button, newDateTimePeriod):
    person = send_webex_get('https://api.ciscospark.com/v1/people/{}'.format(personId))
    personEmail = person["emails"][0]
    personName = person["displayName"]
    with open('allPairsWithDate.txt', 'r') as f:
        allPairs = f.read().split('\n')
    meetingPair = [i for i in allPairs if personEmail in i]
    for itemPair in meetingPair:
        if meetingId in itemPair:
            index = meetingPair.index(itemPair)
            break 
    pair = meetingPair[index]
    print("newTimeAnswerGet pair: ", pair)
    mPair = pair.split(';')
    emailСolleagues = mPair[1].replace(personEmail, '').replace(',', '')
    if button == 'yes':
        newPairInfoStr = createMeetingForPair(mPair[1], newDateTimePeriod)
        with open("allPairsWithDate.txt", "r+") as m:
            allPairs = m.read()
            newPairTime = allPairs.replace(pair, newPairInfoStr)
        with open("allPairsWithDate.txt", "w") as m:
            m.write(newPairTime)
        
        reportText = "A new meeting was created with {}, and an invitation was sent to the email".format(emailСolleagues)
        reportTextСolleagues = "A new meeting was created with {}, and an invitation was sent to the email".format(personName)
        postNotificationToPerson(reportText, personEmail)
        postNotificationToPerson(reportTextСolleagues, emailСolleagues)
    elif button == 'no':
        reportText = "((We will report your response"
        reportTextСolleagues = "The suggested time did not match {}, you can agree on a new time and assign it via the bot".format(personName)
        postNotificationToPerson(reportText, personEmail)
        postNotificationToPerson(reportTextСolleagues, emailСolleagues)

def changeDateTimeCard(personEmail, meetingNum):
    #real line f02f4cca80584973951b5914e0ecb4a6;email1@mail.com,email2@mail.com;2021-04-03T15:10:00+03:00,2021-04-03T15:40:00+03:00
    meetingNum = int(meetingNum)    
    with open('allPairsWithDate.txt', 'r') as f:
        allPairs = f.read().split('\n')
    meetingPair = [i for i in allPairs if personEmail in i]
    try:
        pairWhichToChange = meetingPair[meetingNum - 1]
    except IndexError:
        reportText = 'Wrong meeting number'
        postNotificationToPerson(reportText, personEmail)
        return False
    mPair = pairWhichToChange.split(';')
    meetingId = mPair[0]
    emploeeEmailForNewTime = mPair[1].replace(personEmail,'').replace(',','')
    print("emploeeEmailForNewTime ", emploeeEmailForNewTime)
    postTimeDateCard(personEmail, meetingId)
    
def validDate(datestring):
    try:
        time.strptime(datestring, '%Y-%m-%d')
        currentDate = datetime.now().strftime('%Y-%m-%d').split('-')
        today = dt.datetime(int(currentDate[0]), int(currentDate[1]), int(currentDate[2]))
        timeList = datestring.split('-')
        cardDate = (dt.datetime(int(timeList[0]), int(timeList[1]), int(timeList[2])))
        if (cardDate >= today):
            return True
    except ValueError:
        return False

def validTime(input):
    try:
        time.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False

def printTitleCard(personEmail):   
    # open and read data from file as part of body for request
    with open("cardTextPosition.txt", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()

@app.route('/', methods=['GET', 'POST'])
def webex_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        print("Webhook:")
        pprint(webhook)
        msg = 'Date for Booking'
        if webhook['resource'] == 'messages' and webhook['data']['personEmail'] != botEmail:
            result = send_webex_get('https://webexapis.com/v1/messages/{0}'.format(webhook['data']['id']))
            print("result messages", result)
            in_message = result.get('text', '').lower()
            print("in_message", in_message)
            if in_message.startswith('/change'):
                personEmail = webhook['data']['personEmail']
                printMeetingList(personEmail)
            elif in_message >= '1' and in_message <= '4':
                changeDateTimeCard(webhook['data']['personEmail'], in_message)
            else:
                printMeetingList(webhook['data']['personEmail'])
            printTitleCard(webhook['data']['personEmail'])

        elif webhook['resource'] == 'attachmentActions':
            result = send_webex_get('https://webexapis.com/v1/attachment/actions/{}'.format(webhook['data']['id']))
            print("RESULT ",result)
            if (result['inputs']['type'] == 'newBookingDate'):
                if (validDate(result['inputs']['date']) and validTime(result['inputs']['time'])):
                    newBookingDate(result['personId'], result['inputs']['meetingId'], result['inputs']['date'], result['inputs']['time'])
                else:
                    person = send_webex_get('https://api.ciscospark.com/v1/people/{}'.format(result['personId']))
                    personEmail = person["emails"][0]
                    #
                    reportText = "You have entered invalid data by date/time, please enter the data again"
                    postNotificationToPerson(reportText, personEmail)
                    postTimeDateCard(personEmail, result['inputs']['meetingId'])
            elif (result['inputs']['type'] == 'askForNewTime'):
                newTimeAnswerGet(result['personId'], result['inputs']['meetingId'], result['inputs']['button'], result['inputs']['newDateTimePeriod'])

            if (result['inputs']['type'] == 'position'):
                pass
        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"http://bit.ly/SparkBot-512x512\" alt=\"Webex Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\"></i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Please don't forget to create Webhooks to start receiving events from Webex Teams!</i></b></center>" \
                "<center><b>Generate meeting token <a href='/token'>/token</a></b></center>"
        return message

@app.route('/token', methods=['GET'])
def mainpage_login():
    global redirected
    redirected = None
    return render_template('mainpage_login.html')

@app.route('/webexlogin', methods=['POST'])
def webexlogin():
    WEBEX_USER_AUTH_URL = MEETINGS_API_URL + "/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}".format(
        client_id=urllib.parse.quote(WEBEX_INTEGRATION_CLIENT_ID),
        redirect_uri=urllib.parse.quote(WEBEX_INTEGRATION_REDIRECT_URI),
        scope=urllib.parse.quote(WEBEX_INTEGRATION_SCOPE))
    
    return redirect(WEBEX_USER_AUTH_URL)

@app.route('/webexoauth', methods=['GET'])
def webexoauth():

    webex_code = request.args.get('code')

    print("WEBEX_INTEGRATION_REDIRECT_URI ", WEBEX_INTEGRATION_REDIRECT_URI)
    headers_token = {
        "Content-type": "application/x-www-form-urlencoded"
    }
    body = {
        'client_id': WEBEX_INTEGRATION_CLIENT_ID,
        'code': webex_code,
        'redirect_uri': WEBEX_INTEGRATION_REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_secret': WEBEX_INTEGRATION_CLIENT_SECRET
    }
    get_token = requests.post(MEETINGS_API_URL + "/access_token?", headers=headers_token, data=body)
    print("webex_code ", webex_code) 
    print("get_token ", get_token.text)
    webex_access_token = get_token.json()['access_token']
    global refresh_token
    refresh_token = get_token.json()['refresh_token']
    print(" webex_access_token ",  webex_access_token)
    with open("cred", "r+", encoding="utf-8") as f:
        data = f.read().replace('KEEP_IT_BLANK', webex_access_token)
        f.write(webex_access_token)
    global bearer_meeting
    bearer_meeting = webex_access_token
    createMeetingsAndFiles()
    return redirect('/')

deleteWebHooks(bearer_bot, webhookUrl)
createWebhook(bearer_bot, webhookUrl)
