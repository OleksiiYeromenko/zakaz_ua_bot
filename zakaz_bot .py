#!/usr/bin/python3
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, CallbackQueryHandler, PicklePersistence
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from telegram.error import NetworkError, Unauthorized, TimedOut
import logging
import os
#from time import time
from datetime import timedelta
import pickle
import numpy as np
import requests
import time
import json
import config

dn = os.path.dirname(os.path.realpath(__file__))

# Token for telegram bot
TOKEN = config.TOKEN

# Default stores monitoring period:
MONITORING_PERIOD = 2016 #week with 5 min interval

# Pickle to store unique users
USERS_PICKLE = os.path.join(dn,"users.pkl")
# Pickle to store megarmarket and ashan notification users
MM_USERS_PICKLE = os.path.join(dn,"megamarket_users.pkl")
METRO_USERS_PICKLE = os.path.join(dn,"metro_users.pkl")
NOVUS_USERS_PICKLE = os.path.join(dn,"novus_users.pkl")
ASHAN_USERS_PICKLE = os.path.join(dn,"ashan_users.pkl")


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# Define command handlers
def start(update, context):
    logger.info("User {} started bot".format(update.effective_user["id"])) #update.message.chat_id
    update.message.reply_text('Hello, {}'.format(update.message.from_user.first_name))
    #custom keyborad
    custom_keyboard = [['/start', '/help'],['/monitor_store']]  #'
    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard, resize_keyboard=True, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                     text="This bot is created to monitor available slots in zakaz.ua stores delivery schedule (for now - Megamarket, Metro, Novus and Ashan).\nSelect command or type your own:",
                     reply_markup=reply_markup)
    # save unique users to pickle (open existing)
    try:
        with open(USERS_PICKLE, 'rb') as f:
                registered_users = pickle.load(f)
    except:
        registered_users = {}
    registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
    with open(USERS_PICKLE, 'wb') as f:
        pickle.dump(registered_users, f)
    logger.info("user dict: {}".format(registered_users))
    

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                            text="""  This bot is created to monitor available slots in zakaz.ua stores delivery schedule (for now - Megamarket, Metro, Novus and Ashan).
  For Megamarket, Novus and Metro selected Dorogozhychi-Syrets zone (Megamarket Kosmopolit, Novus on Kilceva 12, Metro-Teremki), for Ashan -  Kyiv_borshhagivka_suburb zone (Ashan on Kilceva 4).

Supported commands:
/start - Hello command
/help - Show help
/monitor_store - monitor available slots in store delivery schedule

Bot author: @oyeryomenko""")


def text(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text+" 😃")  #chat_id=update.message.chat_id
    
    
def select_store(update, context):
    store_list = ['Megamarket', 'Ashan', 'Novus', 'Metro']       
    inline_kb=[]
    crossIcon = u"\u274C"
    checkIcon = u"\u2705" #u2714
    for s in store_list:
        inline_kb.append([InlineKeyboardButton(text=checkIcon+" "+s, callback_data="monitoringstore "+s), InlineKeyboardButton(text=crossIcon+" Unsubscribe "+s, callback_data="unsubscribestore "+s)])       
    #inline_kb = [[InlineKeyboardButton(s,callback_data="monitoringstore "+s)] for s in store_list]+[[InlineKeyboardButton("Unsubscribe "+s,callback_data="unsubscribestore "+s)] for s in store_list]    
    reply_markup = InlineKeyboardMarkup(inline_kb)
    update.message.reply_text('Please choose the store:', reply_markup=reply_markup)    
#     store = "".join(context.args)
#     update.message.reply_text("You said: " + user_says)
    
def register_monitoring_user(update, context):
    logger.info("User {} registered for {}".format(update.effective_user["id"],update.callback_query.data)) 
    query = update.callback_query
    code = query.data.split(' ')[-1]
    context.bot.answer_callback_query(query.id, "Registering for monitoring {} store".format(code))
    #query.edit_message_text(text="Prediction for: {}".format(query.data))
    if code=='Megamarket':
        # save users to pickle (open existing)
        try:
            with open(MM_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
        except:
            registered_users = {}
        registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
        with open(MM_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Megamarket user dict: {}".format(registered_users)) 

    elif code=='Metro':
        try:
            with open(METRO_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
        except:
            registered_users = {}
        registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
        with open(METRO_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Metro user dict: {}".format(registered_users))         

    elif code=='Novus':
        try:
            with open(NOVUS_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
        except:
            registered_users = {}
        registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
        with open(NOVUS_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Novus user dict: {}".format(registered_users))         
          
    elif code=='Ashan':
        try:
            with open(ASHAN_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
        except:
            registered_users = {}
        registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
        with open(ASHAN_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Ashan user dict: {}".format(registered_users)) 
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Wrong store name:{}".format(code))
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤓 You are subscribed for monitoring {} store".format(code))  

    
def unsubscribe_monitoring_user(update, context):
    logger.info("User {} unsubscribed from {}".format(update.effective_user["id"],update.callback_query.data)) 
    query = update.callback_query
    code = query.data.split(' ')[-1]
    context.bot.answer_callback_query(query.id, "Unsubscribing from monitoring {} store".format(code))
    #query.edit_message_text(text="Prediction for: {}".format(query.data))
    if code=='Megamarket':
        # save users to pickle (open existing)
        try:
            with open(MM_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
                    registered_users.pop(update.effective_chat.id, None)
        except:
            registered_users = {}
        with open(MM_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Megamarket user dict: {}".format(registered_users)) 
        
    elif code=='Metro':
        try:
            with open(METRO_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
                    registered_users.pop(update.effective_chat.id, None)
        except:
            registered_users = {}
        with open(METRO_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Metro user dict: {}".format(registered_users)) 
        
    elif code=='Novus':
        try:
            with open(NOVUS_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
                    registered_users.pop(update.effective_chat.id, None)
        except:
            registered_users = {}
        with open(NOVUS_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Novus user dict: {}".format(registered_users)) 
            
    elif code=='Ashan':
        try:
            with open(ASHAN_USERS_PICKLE, 'rb') as f:
                    registered_users = pickle.load(f)
                    registered_users.pop(update.effective_chat.id, None)
        except:
            registered_users = {}
        with open(ASHAN_USERS_PICKLE, 'wb') as f:
            pickle.dump(registered_users, f)
        logger.info("Ashan user dict: {}".format(registered_users)) 
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Wrong store name:{}".format(code))
    context.bot.send_message(chat_id=update.effective_chat.id, text="You are unsubscribed from monitoring {} store".format(code))  

    
    
def set_monitoring(update, context):
    global MONITORING_PERIOD
    update.message.reply_text('Setting monitoring time for zakaz ua stores..')
    timer = ''.join(context.args)
    logger.info("User {} requested to start monioring for {} hrs".format(update.effective_chat.id, timer))    
    if update.effective_chat.id==109458488:
        try: 
            MONITORING_PERIOD = int(timer) * 12 # convert to 5-min intervals
        except ValueError:
            context.bot.send_message(chat_id=update.effective_chat.id, text='You tries to set {} hrs. Should be numerical number of hours'.format(timer))       
        context.bot.send_message(chat_id=update.effective_chat.id, text='You have set monitoring time to {} hrs.'.format(timer))
        logger.info("User {} have set monioring for {} hrs".format(update.effective_chat.id, timer))
    else: 
        context.bot.send_message(chat_id=update.effective_chat.id, text='Hello, {}. You are not aythorised to set monitoring time'.format(update.effective_user["first_name"]))

    
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="What is "+update.message.text+"? 🤔")
    context.bot.send_message(chat_id=update.effective_chat.id, text="I didn't understand that command.")

#
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

############ Zakaz.ua scraping
def get_delivery_plan_megamarket():
    #add random to get request
    rand_number = np.random.rand()
    #Get delivery schedule plan
    url = "https://stores-api.zakaz.ua/stores/48267602/delivery_schedule/plan/?coords=50.4679482,30.431043899999963&some_value={}".format(rand_number)
    #coords: 50.4679482,30.431043899999963
    headers = {"authority":"stores-api.zakaz.ua"
               ,"path":"/stores/48267602/delivery_schedule/plan/?coords=50.4679482,30.431043899999963"
               ,"origin":"https://megamarket.zakaz.ua"
               ,"referer":"https://megamarket.zakaz.ua/uk/"
               ,"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
               ,"x-chain":"megamarket"}
    try:
        response = requests.get(url, headers=headers) #, timeout=5
    except requests.exceptions.ConnectionError:
        print("Megamarket Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            print("Response Not JSON: {}".format(response.text))
            return False
        except Exception as e:
            logging.error(e)
            return False
    else:
        logger.info("Error in response from Megamarket: {}".format(response.status_code)) 
        return False
    
def get_delivery_plan_metro():
    #add random to get request
    rand_number = np.random.rand()
    #Get delivery schedule plan
    url = "https://stores-api.zakaz.ua/stores/48215611/delivery_schedule/plan/?coords=50.4679482,30.4310439&some_value={}".format(rand_number)
    #coords: 50.4679482,30.431043899999963
    headers = {"authority":"stores-api.zakaz.ua"
               ,"path":"/stores/48215611/delivery_schedule/plan/?coords=50.4679482,30.4310439"
               ,"origin":"https://beta.metro.zakaz.ua"
               ,"referer":"https://beta.metro.zakaz.ua/uk/?utm_source=beta&utm_medium=head_banner&utm_campaign=return"
               ,"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
               ,"x-chain":"metro"}
    try:
        response = requests.get(url, headers=headers) #, timeout=5
    except requests.exceptions.ConnectionError:
        print("Metro Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            print("Response Not JSON: {}".format(response.text))
            return False
        except Exception as e:
            logging.error(e)
            return False
    else:
        logger.info("Error in response from Megamarket: {}".format(response.status_code)) 
        return False
    
    
def get_delivery_plan_novus():
    #add random to get request
    rand_number = np.random.rand()
    #Get delivery schedule plan
    url = "https://stores-api.zakaz.ua/stores/48201029/delivery_schedule/plan/?coords=50.468081,30.430879&some_value={}".format(rand_number)
    #coords: 50.4679482,30.431043899999963
    headers = {"authority":"stores-api.zakaz.ua"
               ,"path":"/stores/48267602/delivery_schedule/plan/?coords=50.4679482,30.431043899999963"
               ,"origin":"https://novus.zakaz.ua"
               ,"referer":"https://novus.zakaz.ua/uk/"
               ,"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
               ,"x-chain":"novus"}
    try:
        response = requests.get(url, headers=headers) #, timeout=5
    except requests.exceptions.ConnectionError:
        print("Novus Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            print("Response Not JSON: {}".format(response.text))
            return False
        except Exception as e:
            logging.error(e)
            return False
    else:
        logger.info("Error in response from Megamarket: {}".format(response.status_code)) 
        return False
    
    
def get_delivery_plan_ashan():
    #Get delivery schedule plan
    url = "https://auchan.zakaz.ua/api/query.json"
    headers = {"authority":"auchan.zakaz.ua"
               ,"path":"/api/query.json"
               ,"origin":"https://auchan.zakaz.ua"
               ,"referer":"https://auchan.zakaz.ua/uk/"
               ,"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
               ,"x-requested-with":"XMLHttpRequest"}
    payload = {"meta":{},"request":[{"args":{"store_id":"48246403","zone_id":"kiev_borshhagivka_suburb_1","delivery_type":"plan"},"v":"0.1","type":"user.set_zone","id":{"store_id":"48246403","zone_id":"kiev_borshhagivka_suburb_1","delivery_type":"plan"}},{"args":{"store_ids":["48246403"]},"v":"0.1","type":"store.list","id":"store"},{"args":{"store_id":"48246403"},"v":"0.1","type":"user.info","id":"user_info"},{"args":{"store_ids":["48246403"],"only_available":False,"zone_id":"kiev_borshhagivka_suburb_1","delivery_type":"plan"},"v":"0.1","type":"timewindows.list","id":"timewindows_list"},{"args":{"store_id":"48246403","revision":3,"contract_id":None,"payment_method":None},"v":"0.1","type":"cart.state","id":"cart"}]}
    #Syrets {"meta":{},"request":[{"args":{"store_id":"48246401","zone_id":"Parkovo-syretskyy","delivery_type":"plan"},"v":"0.1","type":"user.set_zone","id":{"store_id":"48246401","zone_id":"Parkovo-syretskyy","delivery_type":"plan"}},{"args":{"store_ids":["48246401"]},"v":"0.1","type":"store.list","id":"store"},{"args":{"store_id":"48246401"},"v":"0.1","type":"user.info","id":"user_info"},{"args":{"store_ids":["48246401"],"only_available":false,"zone_id":"Parkovo-syretskyy","delivery_type":"plan"},"v":"0.1","type":"timewindows.list","id":"timewindows_list"},{"args":{"store_id":"48246401","revision":4,"contract_id":null,"payment_method":null},"v":"0.1","type":"cart.state","id":"cart"}]}
    #Svyatoshino - {"meta":{},"request":[{"args":{"store_id":"48246403","zone_id":"Zhytomyrska","delivery_type":"plan"},"v":"0.1","type":"user.set_zone","id":{"store_id":"48246403","zone_id":"Zhytomyrska","delivery_type":"plan"}},{"args":{"store_ids":["48246403"]},"v":"0.1","type":"store.list","id":"store"},{"args":{"store_id":"48246403"},"v":"0.1","type":"user.info","id":"user_info"},{"args":{"store_ids":["48246403"],"only_available":false,"zone_id":"Zhytomyrska","delivery_type":"plan"},"v":"0.1","type":"timewindows.list","id":"timewindows_list"},{"args":{"store_id":"48246403","revision":4,"contract_id":null,"payment_method":null},"v":"0.1","type":"cart.state","id":"cart"}]}
    #KPI - {"meta":{},"request":[{"args":{"store_id":"48246403","zone_id":"Komarova","delivery_type":"plan"},"v":"0.1","type":"user.set_zone","id":{"store_id":"48246403","zone_id":"Komarova","delivery_type":"plan"}},{"args":{"store_ids":["48246403"]},"v":"0.1","type":"store.list","id":"store"},{"args":{"store_id":"48246403"},"v":"0.1","type":"user.info","id":"user_info"},{"args":{"store_ids":["48246403"],"only_available":false,"zone_id":"Komarova","delivery_type":"plan"},"v":"0.1","type":"timewindows.list","id":"timewindows_list"},{"args":{"store_id":"48246403","revision":5,"contract_id":null,"payment_method":null},"v":"0.1","type":"cart.state","id":"cart"}]}
    #test-office2019  - {"meta":{},"request":[{"args":{"store_id":"48246401","zone_id":"test_offise_2019","delivery_type":"plan"},"v":"0.1","type":"user.set_zone","id":{"store_id":"48246401","zone_id":"test_offise_2019","delivery_type":"plan"}},{"args":{"store_ids":["48246401"]},"v":"0.1","type":"store.list","id":"store"},{"args":{"store_id":"48246401"},"v":"0.1","type":"user.info","id":"user_info"},{"args":{"store_ids":["48246401"],"only_available":false,"zone_id":"test_offise_2019","delivery_type":"plan"},"v":"0.1","type":"timewindows.list","id":"timewindows_list"},{"args":{"store_id":"48246401","revision":5,"contract_id":null,"payment_method":null},"v":"0.1","type":"cart.state","id":"cart"}]}
    try:
        response = requests.post(url, headers=headers, json=payload) #, timeout=5
    except requests.exceptions.ConnectionError:
        print("Ashan Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            print("Response Not JSON: {}".format(response.text))
            return False
        except Exception as e:
            logging.error(e)
            return False
    else:
        logger.info("Error in response from Ashan: {}".format(response.status_code)) 
        return False


def check_status_stores(json):
    if json==False:
        return(False, False, False)
    else:
        status = None
        for day in json:
            for slot in day[list(day.keys())[1]]:
                if slot['is_open']:
                    status = True
                    date = slot['date']
                    time = slot['time_range']
                    return(status, date, time)
        return(False, False, False)
    
def check_status_ashan(json):    
    if json==False:
        return(False, False, False)
    else:
        for day in json['responses'][3]['data']['items'][0]['windows']:
            date = day['date']
            for slot in day['windows']:
                if slot['is_available']:
                    status = True
                    time = slot['range_time']
                    return(status, date, time)
        return(False, False, False)
############

def main():
    #make bot persistant(chat_data, user_data and ConversationHandler),  jobs - not!
#     my_persistence = PicklePersistence(filename='userdata.pickle')

    # Create Updater instance
    updater = Updater(token=TOKEN,
#                       persistence=my_persistence,
                      use_context=True)

    # Register handlers in Dispatcher
    start_handler = CommandHandler('start', start) # start handler
    updater.dispatcher.add_handler(start_handler)   # register start handler
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('monitor_store', select_store))
    updater.dispatcher.add_handler(CommandHandler('set_monitoring', set_monitoring))
    updater.dispatcher.add_handler(CallbackQueryHandler(register_monitoring_user, pattern=r'^monitoringstore ')) 
    updater.dispatcher.add_handler(CallbackQueryHandler(unsubscribe_monitoring_user, pattern=r'^unsubscribestore ')) 
    updater.dispatcher.add_handler(MessageHandler(Filters.text, text))
    #
    updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    #error logging handler
    updater.dispatcher.add_error_handler(error)


    # Run bot
    updater.start_polling()

    # Zakaz.ua store monitoring
    init_mm_status = False
    init_metro_status = False
    init_novus_status = False
    init_a_status = False
    i = 0
    while i < MONITORING_PERIOD:
        logger.info('Monitoring time left: {}hrs'.format(int((MONITORING_PERIOD-i)/12)))
        if MONITORING_PERIOD-i < 13:
            updater.bot.send_message(chat_id='109458488', text="Monitoring will be stopped in 1 hour. To continue: `set_monitoring 24` i={}".format(i))
        #Megamarket    
        try:
            with open(MM_USERS_PICKLE, 'rb') as f:
                    megamarket_registered_users = pickle.load(f)
        except:
            megamarket_registered_users = {}
        
        del_plan = get_delivery_plan_megamarket()
        status = check_status_stores(del_plan)
        if status[0]:
            if init_mm_status != status[2]:
                for usr in megamarket_registered_users.keys():
                    try:
                        updater.bot.send_message(chat_id=usr, text="😎 Free slot in Megamarket delivery schedule. Nearest on {}, {} \nhttps://megamarket.zakaz.ua/uk/".format(status[1],status[2]), disable_web_page_preview=True)
                    except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, megamarket_registered_users[usr])) 
                    except TimedOut:
                        logger.info("Message sending timed out..")                         
        elif init_mm_status != False:
            for usr in megamarket_registered_users.keys():
                try:
                    updater.bot.send_message(chat_id=usr, text="😕 No more free slots in Megamarket delivery schedule. I will notify when appear")
                except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, megamarket_registered_users[usr])) 
                except TimedOut:
                        logger.info("Message sending timed out..") 
        init_mm_status = status[2]
        
        #Metro    
        try:
            with open(METRO_USERS_PICKLE, 'rb') as f:
                    metro_registered_users = pickle.load(f)
        except:
            metro_registered_users = {}
        
        del_plan = get_delivery_plan_metro()
        status = check_status_stores(del_plan)
        if status[0]:
            if init_metro_status != status[2]:
                for usr in metro_registered_users.keys():
                    try:
                        updater.bot.send_message(chat_id=usr, text="😎 Free slot in Metro delivery schedule. Nearest on {}, {} \nhttps://beta.metro.zakaz.ua/uk \nI'll let you know if anything changes".format(status[1],status[2]), disable_web_page_preview=True)
                    except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, metro_registered_users[usr])) 
                    except TimedOut:
                        logger.info("Message sending timed out..")                         
        elif init_metro_status != False:
            for usr in metro_registered_users.keys():
                try:
                    updater.bot.send_message(chat_id=usr, text="😕 No more free slots in Metro delivery schedule. I will notify when appear")
                except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, metro_registered_users[usr])) 
                except TimedOut:
                        logger.info("Message sending timed out..") 
        init_metro_status = status[2]
        
        #Novus  
        try:
            with open(NOVUS_USERS_PICKLE, 'rb') as f:
                    novus_registered_users = pickle.load(f)
        except:
            novus_registered_users = {}
        
        del_plan = get_delivery_plan_novus()
        status = check_status_stores(del_plan)
        if status[0]:
            if init_novus_status != status[2]:
                for usr in novus_registered_users.keys():
                    try:
                        updater.bot.send_message(chat_id=usr, text="😎 Free slot in Novus delivery schedule. Nearest on {}, {} \nhttps://novus.zakaz.ua/uk/ \nI'll let you know if anything changes".format(status[1],status[2]), disable_web_page_preview=True)
                    except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, novus_registered_users[usr])) 
                    except TimedOut:
                        logger.info("Message sending timed out..")                         
        elif init_novus_status != False:
            for usr in novus_registered_users.keys():
                try:
                    updater.bot.send_message(chat_id=usr, text="😕 No more free slots in Novus delivery schedule. I will notify when appear")
                except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, novus_registered_users[usr])) 
                except TimedOut:
                        logger.info("Message sending timed out..") 
        init_novus_status = status[2]        
        
        #Ashan
        try:
            with open(ASHAN_USERS_PICKLE, 'rb') as f:
                        ashan_registered_users = pickle.load(f)
        except:
            ashan_registered_users = {}
        del_plan = get_delivery_plan_ashan()
        status = check_status_ashan(del_plan)
        if status[0]:
            if init_a_status != status[2]:
                for usr in ashan_registered_users.keys():
                    try:
                        updater.bot.send_message(chat_id=usr, text="😎 Free slot in Ashan delivery schedule. Nearest on {}, {} \nhttps://auchan.zakaz.ua/uk/ \nI'll let you know if anything changes".format(status[1],status[2]), disable_web_page_preview=True)
                    except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, megamarket_registered_users[usr])) 
                    except TimedOut:
                        logger.info("Message sending timed out..") 
        elif init_a_status != False:
            for usr in ashan_registered_users.keys():
                try:
                    updater.bot.send_message(chat_id=usr, text="😕 No more free slots in Ashan delivery schedule. I will notify when appear")
                except Unauthorized:
                        logger.info("User blocked bot: {},{}".format(usr, megamarket_registered_users[usr]))             
                except TimedOut:
                    logger.info("Message sending timed out..") 
        init_a_status = status[2]
            #time.sleep(120+np.random.randint(-5,5))
        #else:
            #print('Checking..')
        time.sleep(300+np.random.randint(-5,5))
        i+=1
        
    # Stop the Bot when Ctrl+C received
    updater.idle()


if __name__ == '__main__':
    logger.info("Starting bot")
    main()

