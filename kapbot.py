#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to send you notifications on Kaplan classes
"""
This Bot uses the Updater class to handle the bot.

First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from functools import wraps
from telegram import ReplyKeyboardMarkup, ChatAction, ParseMode, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
import threading
import time, datetime
import logging
import mysql.connector
import json
import urllib
import configparser

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Get config file
config = configparser.ConfigParser()
config.read('config.ini')

# Connect to database
kapbotdb = mysql.connector.connect(
    host = config['mysqlDB']['host'],
    user = config['mysqlDB']['user'],
    passwd = config['mysqlDB']['passwd'],
    database = config['mysqlDB']['database']
)

# Define typing action
def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(*args, **kwargs):
            bot, update = args
            bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(bot, update, **kwargs)
        return command_func
    
    return decorator

send_typing_action = send_action(ChatAction.TYPING)

CHOOSING, START_ONBOARDING, UNI_SELECTION, STUDENTTYPE_SELECTION, EDITING_CLASSES, ADD_ANOTHER_CLASS, CLASS_CHOICE, TYPING_REPLY, TYPING_CHOICE, STUDENTTYPE_POSTOB_SELECTION, RETURNING_SELECTION, EXISTING_CLASS_DIRECTOR, DELETION_CHOICE, ACCOUNT_OPTIONS_DIRECTOR, DELETE_ACC_CONFIRMED, BOT_INFO_SELECTION = range(16)

@send_typing_action
def start(bot, update):
    # Determine if DB has information on user
    userExists = False
    userInfoCursor = kapbotdb.cursor(buffered=True)
    userInfoCursor.execute("SELECT TelegramID FROM RegisteredUsers WHERE TelegramID = " + str(update.message.from_user.id))
    if userInfoCursor.rowcount == 1:
        userExists = True

    # Direct to onboarding if user is new
    if userExists == False:
        update.message.reply_text("Welcome to KaplanScheduleBot! 🤖🤖🤖\nThis bot sends you information about your classes before it starts.")
        update.message.reply_text("Before we begin, some information is needed, press the continue button below to proceed.",
            reply_markup=ReplyKeyboardMarkup([['Continue', 'Cancel']],
            one_time_keyboard=True, resize_keyboard=True))
        
        return START_ONBOARDING

    # Direct to account maintenance if not new    
    else:
        update.message.reply_text("Welcome back to KaplanScheduleBot! 🤖🤖🤖")

        #Check if all data complete
        userInfoCheckCursor = kapbotdb.cursor(buffered=True)
        queryStudentType = "SELECT * FROM RegisteredUsers WHERE TelegramID = " + str(update.message.from_user.id)
        userInfoCheckCursor.execute(queryStudentType)
        
        userResult = userInfoCheckCursor.fetchone()

        if userResult[2] == "ND":
            update.message.reply_text("⚠️ The bot is still lacking some information about you.")
            update.message.reply_text(
                "Are you a full-time or part-time student?", 
                reply_markup=ReplyKeyboardMarkup([['FT', 'PT']], 
                one_time_keyboard=True, resize_keyboard=True))
            return STUDENTTYPE_POSTOB_SELECTION
        else:
            stringedClasslist = ""
            classSubsCursor = kapbotdb.cursor(buffered=True)
            querySubscriptions = "SELECT ClassCode FROM NotificationSubscription WHERE TelegramID = " + str(update.message.from_user.id)
            classSubsCursor.execute(querySubscriptions)

            subsResult = classSubsCursor.fetchall()

            for x in subsResult:
                stringedClasslist = stringedClasslist + "\n" + x[0]

            if len(stringedClasslist) == 0:
                update.message.reply_text("You have not configured me to provide you any class notifications")
            else:
                update.message.reply_text("You have configured the bot to provide you notifications for the following classes: *" 
                    + stringedClasslist + "*", parse_mode=ParseMode.MARKDOWN)
                
            update.message.reply_text("How can I help you today? 😼", 
                reply_markup=ReplyKeyboardMarkup([['Find-a-study-room'],['Configure classes', 'Account options'],['Bot info']],
                resize_keyboard=True))

            return RETURNING_SELECTION

@send_typing_action
def onboarding_choice(bot, update, user_data):
    text = update.message.text

    # End conversation with user if no onboarding wanted
    if text == "Cancel":
        update.message.reply_text("Send the /start command again if you change your mind", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Proceed to obtain user university if Continue button pressed
    elif text == "Continue":
        update.message.reply_text(
            "Which university do you belong to?", 
            reply_markup=ReplyKeyboardMarkup([['Murdoch University'], ['University College Dublin']], 
            one_time_keyboard=True, resize_keyboard=True))
        return UNI_SELECTION

@send_typing_action
def list_study_rooms(bot, update):
    text = update.message.text
    studyRoomCursor = kapbotdb.cursor(buffered=True)
    studyRoomSQL = "SELECT * FROM ScrappedData WHERE ClassCode = 'Study Room'"
    studyRoomCursor.execute(studyRoomSQL)

    studyRoomResult = studyRoomCursor.fetchall()

    date = datetime.datetime.now().strftime("%d-%m-%Y")

    studyRoomString = "*Study rooms are at:*\n"

    studyRoomCounter = 0
    for x in studyRoomResult:
        studyRoomCounter += 1

        studyRoomString = studyRoomString + "*" + x[3] + "* " + x[6] + "\n"

        date = x[5]

    if studyRoomCounter == 0:
        update.message.reply_text("⚠️ There are no study rooms available today", parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    else:
        studyRoomString = studyRoomString + "\n_Data last updated " + str(date) + "_"
        update.message.reply_text(studyRoomString, parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())

    if text == "Find-a-study-room":
        update.message.reply_text("How can I help you today? 😼", 
        reply_markup=ReplyKeyboardMarkup([['Find-a-study-room'],['Configure classes', 'Account options'],['Bot info']],
        resize_keyboard=True))

        return RETURNING_SELECTION
    
    else:
        return ConversationHandler.END

@send_typing_action
def save_uni_choice(bot, update, user_data):
    text = update.message.text
    universityShortName = ""

    # Convert uni name to a abbreviation used by Kaplan
    if text == 'Murdoch University':
        universityShortName = "MUR"
    elif text == 'University College Dublin':
        universityShortName = "UCD"

    # Save user options into DB
    addNewUserCursor = kapbotdb.cursor(buffered=True)
    newUserSQL = "INSERT INTO RegisteredUsers (TelegramID, UniversityType, StudentType) VALUES (%s, %s, %s)"
    newUserVal = (update.message.from_user.id, universityShortName, "ND")
    addNewUserCursor.execute(newUserSQL, newUserVal)
    kapbotdb.commit()

    # Ask the next onboarding question
    update.message.reply_text("Are you a full-time or part-time student?",
        reply_markup=ReplyKeyboardMarkup([['FT', 'PT']],
        one_time_keyboard=True, resize_keyboard=True))

    return STUDENTTYPE_SELECTION

@send_typing_action
def configure_existing_classes_choices(bot, update):
    # Ask what to do with classes
    update.message.reply_text("Whatcha gonna do with the classes?", 
            reply_markup=ReplyKeyboardMarkup([['Add class', 'Remove class'],['< Back']], 
            one_time_keyboard=True,
            resize_keyboard=True))

    return EXISTING_CLASS_DIRECTOR

@send_typing_action
def configure_existing_account_options(bot, update):
    # Ask what to do with account
    update.message.reply_text("What would you like to do with your account?", 
            reply_markup=ReplyKeyboardMarkup([['Change student status', 'Delete account'], ['< Back']], 
            one_time_keyboard=True,
            resize_keyboard=True))

    return ACCOUNT_OPTIONS_DIRECTOR

@send_typing_action
def account_options_response(bot, update, user_data):
    text = update.message.text

    if text == "Change student status":
        update.message.reply_text(
            "Are you a full-time or part-time student?", 
            reply_markup=ReplyKeyboardMarkup([['FT', 'PT'],['< Back']], 
            one_time_keyboard=True, resize_keyboard=True))

        return STUDENTTYPE_POSTOB_SELECTION

    elif text == "Delete account":
        update.message.reply_text(
            "You are about to delete your account. This process is non-reversible.\n\nTo confirm delete, type *DELETE* in caps and press send.\nSend /start to cancel.", 
            reply_markup=ReplyKeyboardMarkup([['< Back']], 
            one_time_keyboard=True, resize_keyboard=True))
    
        return DELETE_ACC_CONFIRMED

def bot_info_director(bot, update, user_data):
    text = update.message.text
    chatid = update.message.from_user.id

    if text == "Some assurance about privacy":
        bot.send_chat_action(chat_id=chatid, action=ChatAction.TYPING)
        update.message.reply_text("This bot respects your privacy and _collects a minimal amount_ of data required for it to function.\n\n"
        "Breakdown of information stored on by the bot:\n1. *Telegram ID* - Recorded to provide a customised experience for your Telegram account, "
        "and to know where to send notifications when the time comes. Note that your Telegram ID differs from your username. In short, it is an ID number "
        "associated with your account.\n2. *Classes entered by you* - Classes that you want the bot to track.\n\nAt any time you wish to delete all information from "
        "your account, look for the Delete Account button in Account options. This process is irreversible as your data is immediately wiped from the bot.\n\n"
        "The /studyrooms and /queryclass command does not require you to initialise your account with this bot.\n\n_@KaplanScheduleBot is not a product of Kaplan"
        "Singapore, this bot is not responsible for data accuracy or reliability and availability of this service is not guaranteed._", 
        parse_mode=ParseMode.MARKDOWN)
    elif text == "Why":
        bot.send_chat_action(chat_id=chatid, action=ChatAction.UPLOAD_PHOTO)
        bot.send_photo(chat_id=chatid, photo=open('such_wow.jpg', 'rb'))
    elif text == "Limitations":
        bot.send_chat_action(chat_id=chatid, action=ChatAction.TYPING)
        update.message.reply_text("*Limitations of this bot:*\n1. Currently, switching universities requires you to delete and recreate your account.\n"
        "2. This bot does not check the class code you entered for validity, please ensure that you enter your class code correctly. Examples below:\n"
        "*Murdoch University* - BRD203A\n*Univ. College Dublin* - BBSLSCM28", 
        parse_mode=ParseMode.MARKDOWN)
    elif text == "< Back":
        update.message.reply_text("How can I help you today? 😼", 
        reply_markup=ReplyKeyboardMarkup([['Find-a-study-room'],['Configure classes', 'Account options'],['Bot info']],
        resize_keyboard=True))

        return RETURNING_SELECTION

    bot.send_chat_action(chat_id=chatid, action=ChatAction.TYPING)
    update.message.reply_text(
        "What would you like me to tell you?", 
        reply_markup=ReplyKeyboardMarkup([['Some assurance about privacy'],['Why','Limitations'],['< Back']], 
        one_time_keyboard=True, resize_keyboard=True))
    return BOT_INFO_SELECTION

@send_typing_action
def delete_user_account(bot, update, user_data):
    deleteAccountCursor = kapbotdb.cursor(buffered=True)
    deleteUserVal = update.message.from_user.id

    # First delete all notification records
    deleteNotifSQL = "DELETE FROM NotificationSubscription WHERE TelegramID = " + str(update.message.from_user.id)
    deleteAccountCursor.execute(deleteNotifSQL)
    kapbotdb.commit()

    # Then delete account record
    deleteAccountSQL = "DELETE FROM RegisteredUsers WHERE TelegramID = " + str(update.message.from_user.id)
    deleteAccountCursor.execute(deleteAccountSQL)
    kapbotdb.commit()

    # Confirm deletion with user
    update.message.reply_text("Your account has been deleted, /start if you would like to start over with this bot.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

@send_typing_action
def save_studenttype_choice(bot, update, user_data):
    text = update.message.text
    setStuTypeCursor = kapbotdb.cursor(buffered=True)
    setStuTypeSQL = "UPDATE RegisteredUsers SET StudentType = %s WHERE TelegramID = %s"

    # Add student type of current user to database
    if text == "FT":
        setFTStuVal = ("FT", update.message.from_user.id)
        setStuTypeCursor.execute(setStuTypeSQL, setFTStuVal)
        kapbotdb.commit()
    elif text == "PT":
        setFTStuVal = ("PT", update.message.from_user.id)
        setStuTypeCursor.execute(setStuTypeSQL, setFTStuVal)
        kapbotdb.commit()

    update.message.reply_text("Your preferences has been saved, please send /start to restart our conversation.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

@send_typing_action
def save_studenttype_choice_onboarding(bot, update, user_data):
    text = update.message.text
    setStuTypeCursor = kapbotdb.cursor(buffered=True)
    setStuTypeSQL = "UPDATE RegisteredUsers SET StudentType = %s WHERE TelegramID = %s"

    # Add student type of current user to database
    if text == "FT":
        setFTStuVal = ("FT", update.message.from_user.id)
        setStuTypeCursor.execute(setStuTypeSQL, setFTStuVal)
        kapbotdb.commit()
    elif text == "PT":
        setFTStuVal = ("PT", update.message.from_user.id)
        setStuTypeCursor.execute(setStuTypeSQL, setFTStuVal)
        kapbotdb.commit()

    # Ask the next onboarding question
    update.message.reply_text("Next, enter the class code that you wish to be notified of "
        "with no spaces.\n\n*For example:*\nMurdoch University unit codes look like *ICT380B*"
        "\nUCD unit codes look like *BBSLSCM28*.", parse_mode=ParseMode.MARKDOWN)
    update.message.reply_text("Press begin when you are ready!",
        reply_markup=ReplyKeyboardMarkup([['Begin']],
        one_time_keyboard=True, resize_keyboard=True))

    return EDITING_CLASSES

@send_typing_action
def add_classes(bot, update, user_data):
    update.message.reply_text('Alright, please send me a unit code', reply_markup=ReplyKeyboardRemove())

    return CLASS_CHOICE

@send_typing_action
def class_choice(bot, update, user_data):
    text = update.message.text
    addClassResult = add_class_helper(text)

    # Unit code provided was longer than 19 chars
    if addClassResult == 2:
        update.message.reply_text(
            "The unit code you have entered is too long, try again?",
            reply_markup=ReplyKeyboardMarkup([['Try again']],
            one_time_keyboard=True, resize_keyboard=True))
        return EDITING_CLASSES

    elif addClassResult == 1:
        # Remove spaces from the input
        text = text.replace(' ', '')

        # First check if the class has been added
        classExistenceCursor = kapbotdb.cursor(buffered=True)
        queryClassExistenceSQL = "SELECT ClassCode FROM NotificationSubscription WHERE TelegramID = %s AND ClassCode = %s"
        queryClassExistenceVal = (update.message.from_user.id, text)
        classExistenceCursor.execute(queryClassExistenceSQL, queryClassExistenceVal)

        # Insert class to DB if it does not exist
        if classExistenceCursor.rowcount == 0:
            classInsertionCursor = kapbotdb.cursor(buffered=True)
            insertSubsSQL = "INSERT INTO NotificationSubscription (TelegramID, ClassCode) VALUES (%s, %s)"
            insertSubsVal = (update.message.from_user.id, text)
            classInsertionCursor.execute(insertSubsSQL, insertSubsVal)
            kapbotdb.commit()

            update.message.reply_text("Your class " + text + " was successfully saved.\n\nWould you like to "
                "enter another class?", 
                reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True, resize_keyboard=True))

            return ADD_ANOTHER_CLASS

        # Return error message if class already exists
        if classExistenceCursor.rowcount > 0:
            update.message.reply_text("🚳 You already have this class in your collection, therefore it was not added."
            "\n\nWould you like to add another class?", reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], 
            one_time_keyboard=True, resize_keyboard=True))

            return ADD_ANOTHER_CLASS

# This class helper for future expansion
def add_class_helper(classCode):
    if len(classCode) >= 19:
        return 2
    else:
        return 1

@send_typing_action
def remove_classes(bot, update, user_data):
    if update.message.text == "< Back":
        update.message.reply_text("How can I help you today? 😼", 
        reply_markup=ReplyKeyboardMarkup([['Find-a-study-room'],['Configure classes', 'Account options'],['Bot info']],
        resize_keyboard=True))

        return RETURNING_SELECTION

    # Get info on existing classes from DB
    removeClassCursor = kapbotdb.cursor(buffered=True)
    querySubscriptions = "SELECT ClassCode FROM NotificationSubscription WHERE TelegramID = " + str(update.message.from_user.id)
    removeClassCursor.execute(querySubscriptions)
    subsResult = removeClassCursor.fetchall()

    # Provide users with buttons to delete their class
    classButtonArray = []
    
    # Populate button array
    for x in subsResult:
        classButtonArray.append(x)

    # Add a remove all classes button
    classButtonArray.append(["Remove all classes"])
    classButtonArray.append(["< Back"])

    update.message.reply_text("Delete one class? Or delete all classes (no confirmation 🧨)?", 
        reply_markup=ReplyKeyboardMarkup(classButtonArray, 
        one_time_keyboard=True, resize_keyboard=True))

    return DELETION_CHOICE

@send_typing_action
def process_class_deletion(bot, update, user_data):
    text = update.message.text
    classRemovalCursor = kapbotdb.cursor(buffered=True)

    if text == "Remove all classes":
        removeAllSubsSQL = "DELETE FROM NotificationSubscription WHERE TelegramID = " + str(update.message.from_user.id)
        classRemovalCursor.execute(removeAllSubsSQL)
        kapbotdb.commit()

        update.message.reply_text("All your classes are gone.")

    else:
        removeSubsSQL = "DELETE FROM NotificationSubscription WHERE TelegramID = %s AND ClassCode = %s"
        setRemoveSubsVal = (update.message.from_user.id, text)
        classRemovalCursor.execute(removeSubsSQL, setRemoveSubsVal)
        kapbotdb.commit()

        update.message.reply_text("The class " + text + " was deleted successfully.")

    update.message.reply_text("Whatcha gonna do with the classes?", 
        reply_markup=ReplyKeyboardMarkup([['Add class', 'Remove class'],['< Back']], 
        one_time_keyboard=True,
        resize_keyboard=True))

    return EXISTING_CLASS_DIRECTOR

@send_typing_action
def add_class_success(bot, update):
    update.message.reply_text("Your classes have been added successfully, don't forget to turn on notifications!")
    update.message.reply_text("If you need to talk to me again, send a /start command.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def unrecognized_input(bot, update):
    if update.message.text == "/studyrooms":
        return RETURNING_SELECTION

    update.message.reply_text("I have no idea what you just said! This conversation has now ended. Send /start to try again.")

    return ConversationHandler.END

@send_typing_action
def bot_not_started(bot, update):
    update.message.reply_text("Send /start to wake the bot")

    return ConversationHandler.END

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def sendNotifications(updater):
    global notificationsThread
#send notifications
    while (True):
        currentHour = time.strftime("%H", time.localtime())
        
        #Reset sent notifications at 1 am, sleep longer at night
        if (int(currentHour) == 1):
            resetNotifCountCursor = kapbotdb.cursor(buffered=True)
            updater.bot.send_message(chat_id=config['TelegramAdmin']['adminAccountID'], text="Notification daemon is going to sleep")
            resetNotificationCountSQL = "UPDATE NotificationSubscription SET DailyNotifCount = 0"
            resetNotifCountCursor.execute(resetNotificationCountSQL)
            kapbotdb.commit()

            #Sleep till 7am
            time.sleep(21600)
            updater.bot.send_message(chat_id=config['TelegramAdmin']['adminAccountID'], text="Notification daemon has woken up")

        #Update time incase sleep
        currentHour = time.strftime("%H", time.localtime())
        currentMinute = time.strftime("%M", time.localtime())
        currentSecond = time.strftime("%S", time.localtime())

        #Check for notifications to send by the half hour
        # if (int(currentMinute) > 0 and int(currentMinute) <= 30):
        #     sleepDuration = abs(30 - int(currentMinute))
        #     time.sleep(sleepDuration * 60)
        # elif (int(currentMinute) > 30 and int(currentMinute) <= 59):
        #     sleepDuration = abs(60 - int(currentMinute))
        #     time.sleep(sleepDuration * 60)

        #Obtain notifications from DB
        getScheduleCursor = kapbotdb.cursor(buffered=True)
        getTodayScheduleSQL = """SELECT RegisteredUsers.TelegramID, RegisteredUsers.StudentType, RegisteredUsers.UniversityType, NotificationSubscription.ClassCode, ScrappedData.ClassLoc, ScrappedData.StartTime, ScrappedData.Date, ScrappedData.Duration, NotificationSubscription.DailyNotifCount
        FROM NotificationSubscription 
        LEFT JOIN ScrappedData ON NotificationSubscription.ClassCode = ScrappedData.ClassCode
        LEFT JOIN RegisteredUsers ON RegisteredUsers.TelegramID = NotificationSubscription.TelegramID
        WHERE RegisteredUsers.StudentType = ScrappedData.StudentType
        AND NotificationSubscription.ClassCode = ScrappedData.ClassCode
        AND ScrappedData.Date = CURDATE();"""
        
        getScheduleCursor.execute(getTodayScheduleSQL)
        
        notifData = getScheduleCursor.fetchall()

        #Skip notif check if empty 
        if len(notifData) == 0:
            time.sleep(60)
            continue;

        #Update clock after sleep
        currentHour = time.strftime("%H", time.localtime())
        currentMinute = time.strftime("%M", time.localtime())
        currentTime = time.strftime("%H:%M", time.localtime())

        #Send notifications
        for x in notifData:
            notifCount = x[8]

            #Prevent spam, only one notification per day
            # getSentCountCursor = kapbotdb.cursor(buffered=True)
            # getSentCountSQL = "SELECT DailyNotifCount FROM NotificationSubscription WHERE TelegramID = %s AND ClassCode = %s"
            # getSentCountVals = (x[0], x[3])
            # getSentCountCursor.execute(getSentCountSQL, getSentCountVals)

            # sentCountData = getSentCountCursor.fetchone()

            # if sentCountData != 0:
            #     continue
            
            if notifCount > 0:
               continue

            FMT = '%H:%M'
            dbTimeVal = x[5]
            trimmedTime = (datetime.datetime.min + dbTimeVal).time()
            trimmedTime = trimmedTime.strftime(FMT)
            trimmedTime = trimmedTime[:5]

            tdelta = datetime.datetime.strptime(trimmedTime, FMT) - datetime.datetime.strptime(str(currentTime), FMT)
            timeInSecs = tdelta.total_seconds()
            timeInMins = timeInSecs / 60
            timeInMinsNoDecimal = int(timeInMins)

            #Notif debug
            threadID = notificationsThread.ident

            notifStringConstruct = "*" + x[3] + " @ " + x[4] + "*" + "\nHappening in ~" + str(timeInMinsNoDecimal) +" minutes\n" + x[7] + "\n*DEBUG MESG.*: This notification was sent by thread " + str(threadID) + "."

            if (timeInMins < 75 and timeInMins >= 0):
                updater.bot.send_message(chat_id=x[0], text=notifStringConstruct, parse_mode=ParseMode.MARKDOWN)

                #Update notif count
                notifCount += 1
                updateNotifCountCursor = kapbotdb.cursor(buffered=True)
                setNotifCountSQL = "UPDATE NotificationSubscription SET DailyNotifCount = %s WHERE TelegramID = %s AND ClassCode = %s"
                setNotifCountValues = (notifCount, x[0], x[3])
                updateNotifCountCursor.execute(setNotifCountSQL, setNotifCountValues)
                kapbotdb.commit()
                
def update_schedule(updater):
    # This daemon should only run once every two hours at the 15th minute
    while (True):
        currentHour = time.strftime("%H", time.localtime())
        currentMinute = time.strftime("%M", time.localtime())
        currentSecond = time.strftime("%S", time.localtime())

        #Only check for updates on the 15th minute every even hour
        sleepDuration = 0
        if (int(currentHour) % 2 != 0):
            sleepDuration += 60

        if (int(currentMinute) < 15):
            sleepDuration += abs(15 - int(currentMinute))
            time.sleep(sleepDuration * 60)
        else:
            sleepDuration += abs(60 - int(currentMinute) + 15)
            time.sleep(sleepDuration * 60)

        currentHour = time.strftime("%H", time.localtime())
        
        #Sleep longer in the morning
        if (int(currentHour) == 2):
            time.sleep(4 * 60 * 60)

        #First delete all rows in DB
        deleteAllScheduleCursor = kapbotdb.cursor(buffered=True)
        deleteAllRowsSQL = "DELETE FROM ScrappedData"
        deleteAllScheduleCursor.execute(deleteAllRowsSQL)
        kapbotdb.commit()

        #Obtain data from source
        url = "http://webapps.kaplan.com.sg/schedule/schedules2.json"
        response = urllib.urlopen(url)
        data = json.loads(response.read())

        #Parse the json
        insertParsedCursor = kapbotdb.cursor(buffered=True)

        for item in data:
            classroom = item["classroom"]
            date = item["days"][0]["date"]

            #Deeper json
            for className in item["days"][0]["classes"]:
                cName = className["ClassName"]
                cDur = className["Duration"]
                cStartTime = className["startTime"]
                eventName = className["eventName"]

                #Get other information from string
                ftpt = ""
                uniName = ""
                unitName = ""

                #Get the student type
                if cName[0:2] == "PT":
                    ftpt = "PT"
                elif cName[0:2] == "FT":
                    ftpt = "FT"
                        
                #Get the uni name
                if cName[3:6] == "UCD":
                    uniName = "UCD"
                elif cName[3:6] == "MUR":
                    uniName = "MUR"

                #Get the unit name
                if uniName == "UCD":
                    unitName = cName[7:]
                    unitName = unitName.replace(' ', '')

                    insertDataSQL = "INSERT INTO ScrappedData (StudentType, UniversityType, ClassCode, ClassLoc, StartTime, Date, Duration) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    insertDataSQLValues = (ftpt, uniName, unitName, classroom, cStartTime, date, cDur)
                    insertParsedCursor.execute(insertDataSQL, insertDataSQLValues)
                    kapbotdb.commit()
                    #print('Commitment Type: ' + ftpt + '\n' + 'Uni Name: ' + uniName + '\n' + 'Unit: ' + unitName + '\n' + 'Class Loc: ' + classroom + '\n')

                elif uniName == "MUR":
                    #MUR specific variables
                    unitNameUnspaced = cName[7:]
                    unitName = unitNameUnspaced.replace(' ', '')
                    possibleGroupName = ''
                    dataIssue = ''
                    dataIssueExists = False

                    # Check to determine if class might be restricted to group
                    dashPosition = eventName.find('-')
                    if dashPosition > 0:
                        possibleGroupName = eventName[dashPosition+2:]

                        # Check to determine if data is internally conflicting
                        if eventName.find(unitNameUnspaced) < 0:
                            dataIssue = 'Issues in raw data: Unit Name = ' + unitNameUnspaced + ' but Event Name = ' + eventName
                            dataIssueExists = True

                        else:
                            dataIssueExists = False

                    insertDataSQL = "INSERT INTO ScrappedData (StudentType, UniversityType, ClassCode, ClassLoc, StartTime, Date, Duration, PGroupName, dataIssueExists, dataIssue) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    insertDataSQLValues = (ftpt, uniName, unitName, classroom, cStartTime, date, cDur, possibleGroupName, dataIssueExists, dataIssue)
                    insertParsedCursor.execute(insertDataSQL, insertDataSQLValues)
                    kapbotdb.commit()

                #Get study room
                if eventName == "Study Room":
                    insertStudyRoomSQL = "INSERT INTO ScrappedData (ClassCode, ClassLoc, StartTime, Date, Duration) VALUES (%s, %s, %s, %s, %s)"
                    studyRoomValues = (eventName, classroom, cStartTime, date, cDur)
                    insertParsedCursor.execute(insertStudyRoomSQL, studyRoomValues)
                    kapbotdb.commit()

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(config['TelegramBotToken']['token'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    main_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            START_ONBOARDING: [RegexHandler('^(Continue|Cancel)$',
                                    onboarding_choice,
                                    pass_user_data=True),
                       ],

            UNI_SELECTION: [RegexHandler('^(Murdoch University|University College Dublin)$',
                                    save_uni_choice,
                                    pass_user_data=True),
                       ],

            STUDENTTYPE_SELECTION: [RegexHandler('^(FT|PT)$',
                                    save_studenttype_choice_onboarding,
                                    pass_user_data=True),
                       ],

            STUDENTTYPE_POSTOB_SELECTION: [RegexHandler('^(FT|PT)$',
                                    save_studenttype_choice,
                                    pass_user_data=True),
                            RegexHandler('^(< Back)$',
                                    configure_existing_account_options,
                                    ),
                       ],

            RETURNING_SELECTION: [RegexHandler('^(Configure classes)$',
                                    configure_existing_classes_choices),
                            RegexHandler('^(Account options)$',
                                    configure_existing_account_options),
                            RegexHandler('^(Find-a-study-room|\/studyrooms)$',
                                    list_study_rooms),
                            RegexHandler('^(Bot info)$',
                                    bot_info_director,
                                    pass_user_data=True),
                       ],

            BOT_INFO_SELECTION: [RegexHandler('^(Some assurance about privacy|Why|Limitations)$',
                                    bot_info_director,
                                    pass_user_data=True),
                        RegexHandler('^(< Back)$',
                                    bot_info_director,
                                    pass_user_data=True),
                       ],

            EDITING_CLASSES: [RegexHandler('^(Begin|Try again)$',
                                    add_classes,
                                    pass_user_data=True),
                       ],

            EXISTING_CLASS_DIRECTOR: [RegexHandler('^(Add class)$',
                                    add_classes,
                                    pass_user_data=True),
                       RegexHandler('^(Remove class)$',
                                    remove_classes,
                                    pass_user_data=True),
                       RegexHandler('^(< Back)$',
                                    remove_classes,
                                    pass_user_data=True),
                       ],

            ADD_ANOTHER_CLASS: [RegexHandler('^(Yes)$',
                                    add_classes,
                                    pass_user_data=True),
                       RegexHandler('^(No)$',
                                    add_class_success),
                       ],

            DELETION_CHOICE: [RegexHandler('^(< Back)$',
                                    remove_classes,
                                    pass_user_data=True),
                        MessageHandler(Filters.text,
                                           process_class_deletion,
                                           pass_user_data=True),
                            ],

            ACCOUNT_OPTIONS_DIRECTOR: [RegexHandler('^(Change student status|Delete account)$',
                                    account_options_response,
                                    pass_user_data=True),
                       RegexHandler('^(< Back)$',
                                    remove_classes,
                                    pass_user_data=True),
                       ],

            DELETE_ACC_CONFIRMED: [RegexHandler('^(DELETE)$',
                                    delete_user_account,
                                    pass_user_data=True),
                        RegexHandler('^(< Back)$',
                                    configure_existing_account_options),
                       ],

            CLASS_CHOICE: [MessageHandler(Filters.text,
                                           class_choice,
                                           pass_user_data=True),
                            ],
        },

        fallbacks=[RegexHandler('.*', unrecognized_input)],
        conversation_timeout=300
    )

    # classquery_conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler('studyrooms', list_study_rooms)],

    #     fallbacks=[RegexHandler('.*', unrecognized_input)],
    #     conversation_timeout=1
    # )

    dp.add_handler(main_conv_handler)
    dp.add_handler(CommandHandler('studyrooms', list_study_rooms))
    # dp.add_handler(classquery_conv_handler)
    dp.add_handler(MessageHandler(Filters.text, bot_not_started))

    # log all errors
    dp.add_error_handler(error)

    # Create new daemon to handle notification sending
    global notificationsThread
    notificationsThread = threading.Thread(target=sendNotifications, args=(updater,))
    notificationsThread.daemon = True
    notificationsThread.start()

    # Create new daemon to handle course updating
    crawlerThread = threading.Thread(target=update_schedule, args=(updater,))
    crawlerThread.daemon = True
    crawlerThread.start()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
