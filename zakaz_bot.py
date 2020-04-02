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
import threading
from threading import Thread
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
logger = logging.getLogger(__name__) 
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Write log to the file
fileHandler = logging.FileHandler('zakaz_ua_bot.log', encoding='utf-8') #mode='w'
#fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
# Print log to the screen
consoleHandler = logging.StreamHandler()
#consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)


#######################################################
# Class for monitoring thread

class Monitoring(Thread):
    def __init__(self, updater):
        super(Monitoring, self).__init__()
        self.running = True
        self.updater = updater
        
    def run(self):   
        init_mm_status = False
        init_metro_status = False
        init_novus_status = False
        init_a_status = False     
        while self.running:
            # Zakaz.ua store monitoring
            #Megamarket    
            try:
                with open(MM_USERS_PICKLE, 'rb') as f:
                        megamarket_registered_users = pickle.load(f)
            except:
                megamarket_registered_users = {}
            if len(megamarket_registered_users)>0:
                del_plan = get_delivery_plan_megamarket()
                status = check_status_stores(del_plan)
                if status[0]:
                    if init_mm_status != status[2]:
                        for usr in megamarket_registered_users.keys():
                            try:
                                self.updater.bot.send_message(chat_id=usr, text="😎 З'явився вільний слот в графіку доставки Мегамаркет. Найближчий {}, {} \nhttps://megamarket.zakaz.ua/uk/ \nЯ повідомлю про зміни.".format(status[1],status[2]), disable_web_page_preview=True)
                            except Unauthorized:
                                logger.info("User blocked bot: {},{}".format(usr, megamarket_registered_users[usr])) 
                            except TimedOut:
                                logger.info("Message sending timed out..")                         
                elif init_mm_status != False:
                    for usr in megamarket_registered_users.keys():
                        try:
                            self.updater.bot.send_message(chat_id=usr, text="😕 Більше немає вільних слотів в графіку доставки Мегамаркет. Повідомлю коли з’явиться.")
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
            if len(metro_registered_users)>0:
                del_plan = get_delivery_plan_metro()
                status = check_status_stores(del_plan)
                if status[0]:
                    if init_metro_status != status[2]:
                        for usr in metro_registered_users.keys():
                            try:
                                self.updater.bot.send_message(chat_id=usr, text="😎 З'явився вільний слот в графіку доставки Метро. Найближчий {}, {} \nhttps://beta.metro.zakaz.ua/uk \nЯ повідомлю про зміни.".format(status[1],status[2]), disable_web_page_preview=True)
                            except Unauthorized:
                                logger.info("User blocked bot: {},{}".format(usr, metro_registered_users[usr])) 
                            except TimedOut:
                                logger.info("Message sending timed out..")                         
                elif init_metro_status != False:
                    for usr in metro_registered_users.keys():
                        try:
                            self.updater.bot.send_message(chat_id=usr, text="😕 Більше немає вільних слотів в графіку доставки Метро. Повідомлю коли з’явиться.")
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
            if len(novus_registered_users)>0:
                del_plan = get_delivery_plan_novus()
                status = check_status_stores(del_plan)
                if status[0]:
                    if init_novus_status != status[2]:
                        for usr in novus_registered_users.keys():
                            try:
                                self.updater.bot.send_message(chat_id=usr, text="😎 З'явився вільний слот в графіку доставки Новус. Найближчий  {}, {} \nhttps://novus.zakaz.ua/uk/ \nЯ повідомлю про зміни.".format(status[1],status[2]), disable_web_page_preview=True)
                            except Unauthorized:
                                logger.info("User blocked bot: {},{}".format(usr, novus_registered_users[usr])) 
                            except TimedOut:
                                logger.info("Message sending timed out..")                         
                elif init_novus_status != False:
                    for usr in novus_registered_users.keys():
                        try:
                            self.updater.bot.send_message(chat_id=usr, text="😕 Більше немає вільних слотів в графіку доставки Новус. Повідомлю коли з’явиться.")
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
            if len(ashan_registered_users)>0:            
                del_plan = get_delivery_plan_ashan()
                status = check_status_stores(del_plan)
                if status[0]:
                    if init_a_status != status[2]:
                        for usr in ashan_registered_users.keys():
                            try:
                                self.updater.bot.send_message(chat_id=usr, text="😎 З'явився вільний слот в графіку доставки Ашан. Найближчий {}, {} \nhttps://beta.auchan.zakaz.ua/uk/ \nЯ повідомлю про зміни.".format(status[1],status[2]), disable_web_page_preview=True)
                            except Unauthorized:
                                logger.info("User blocked bot: {},{}".format(usr, megamarket_registered_users[usr])) 
                            except TimedOut:
                                logger.info("Message sending timed out..") 
                elif init_a_status != False:
                    for usr in ashan_registered_users.keys():
                        try:
                            self.updater.bot.send_message(chat_id=usr, text="😕 Більше немає вільних слотів в графіку доставки Ашан. Повідомлю коли з’явиться.")
                        except Unauthorized:
                                logger.info("User blocked bot: {},{}".format(usr, megamarket_registered_users[usr]))             
                        except TimedOut:
                            logger.info("Message sending timed out..") 
                init_a_status = status[2]
                
            time.sleep(300+np.random.randint(-5,5))
                          
##############################################################     
    
    
    
# Define command handlers
def start(update, context):
    logger.info("User {} started bot".format(update.effective_user["id"])) #update.message.chat_id
    update.message.reply_text('Привіт, {}'.format(update.message.from_user.first_name))
    #custom keyborad
    custom_keyboard = [['/start', '/help'],['/monitor_store']]  #'
    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard, resize_keyboard=True, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                     text="Цей бот створений для моніторингу доступних слотів у графіку доставки магазинів на zakaz.ua (поки що - Мегамаркет, Метро, Новус та Ашан) у Києві.\nВиберіть магазин у '/monitor_store'",
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
    #return monitoring

    
# Stop monitoring Thread        
def stop_monitoring(update, context): #t=monitoring
    global monitoring  
    update.message.reply_text('OK, end monitoring...')
    monitoring.running = False # stop the thread

# Get some data from monitoring Thread
# def get(update, context, t=monitoring):
#     update.message.reply_text('OK, the current value is {}'.format(t.data))
    

    
    
    
def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                            text="""
    Цей бот створений для моніторингу доступних слотів у графіку доставки магазинів на zakaz.ua (поки що - Мегамаркет, Метро, Новус та Ашан) у Києві.
    Для Мегамаркет, Новус та Метро обрана зона Дорогожичі-Сирець (магазини Магамаркет Космополіт, Новус на Кільцевій 12, Метро-Теремки), для Ашан - зона Київ-Борщагівка (Ашан на Кільцевій 4).

Supported commands:
/start - Привітання
/help - Допомога
/monitor_store - Стежити за наявними місцями в графіку доставки магазинів

Автор боту: @oyeryomenko""")


def text(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text+" 😃")  #chat_id=update.message.chat_id
    
    
def select_store(update, context):
    store_list = ['Megamarket', 'Ashan', 'Novus', 'Metro']       
    inline_kb=[]
    crossIcon = u"\u274C"
    checkIcon = u"\u2705"
    for s in store_list:
        inline_kb.append([InlineKeyboardButton(text=checkIcon+" "+s, callback_data="monitoringstore "+s), InlineKeyboardButton(text=crossIcon+" Unsubscribe "+s, callback_data="unsubscribestore "+s)])       
    #inline_kb = [[InlineKeyboardButton(s,callback_data="monitoringstore "+s)] for s in store_list]+[[InlineKeyboardButton("Unsubscribe "+s,callback_data="unsubscribestore "+s)] for s in store_list]    
    reply_markup = InlineKeyboardMarkup(inline_kb)
    update.message.reply_text('Оберіть магазин:', reply_markup=reply_markup)    
#     store = "".join(context.args)
#     update.message.reply_text("You said: " + user_says)
    
def register_monitoring_user(update, context):
    logger.info("User {} registered for {}".format(update.effective_user["id"],update.callback_query.data)) 
    query = update.callback_query
    code = query.data.split(' ')[-1]
    context.bot.answer_callback_query(query.id, "Ви реєструєтеся на моніторинг {}".format(code))
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
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤓 Ви підписалися на моніторинг {}. \nЯ повідомлю коли з'явиться вільне вікно доставки".format(code))  

    
def unsubscribe_monitoring_user(update, context):
    logger.info("User {} unsubscribed from {}".format(update.effective_user["id"],update.callback_query.data)) 
    query = update.callback_query
    code = query.data.split(' ')[-1]
    context.bot.answer_callback_query(query.id, "Ви відписуєтеся від моніторингу {}".format(code))
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
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ви відписалися від моніторингу {} магазин".format(code))  

    
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Що таке "+update.message.text+"? 🤔")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Я не розумію цієї команди.")

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
        logger.info("Megamarket Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            logger.info("Response Not JSON: {}".format(response.text))
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
        logger.info("Metro Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            logger.info("Response Not JSON: {}".format(response.text))
            return False
        except Exception as e:
            logging.error(e)
            return False
    else:
        logger.info("Error in response from Metro: {}".format(response.status_code)) 
        return False
    
def get_delivery_plan_novus():
    #add random to get request
    rand_number = np.random.rand()
    #Get delivery schedule plan
    url = "https://stores-api.zakaz.ua/stores/48201029/delivery_schedule/plan/?coords=50.468081,30.430879&some_value={}".format(rand_number)
    #coords: 50.4679482,30.431043899999963
    headers = {"authority":"stores-api.zakaz.ua"
               ,"path":"/stores/48201029/delivery_schedule/plan/?coords=50.4679482,30.431043899999963"
               ,"origin":"https://novus.zakaz.ua"
               ,"referer":"https://novus.zakaz.ua/uk/"
               ,"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
               ,"x-chain":"novus"}
    try:
        response = requests.get(url, headers=headers) #, timeout=5
    except requests.exceptions.ConnectionError:
        logger.info("Novus Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            logger.info("Response Not JSON: {}".format(response.text))
            return False
        except Exception as e:
            logging.error(e)
            return False
    else:
        logger.info("Error in response from Novus: {}".format(response.status_code)) 
        return False
    
def get_delivery_plan_ashan():
    #add random to get request
    rand_number = np.random.rand()
    #Get delivery schedule plan
    url = "https://stores-api.zakaz.ua/stores/48246401/delivery_schedule/plan/?coords=50.4679482,30.4310439&some_value={}".format(rand_number)
    #coords: 50.4679482,30.431043899999963
    headers = {"authority":"stores-api.zakaz.ua"
               ,"path":"/stores/48246401/delivery_schedule/plan/?coords=50.4679482,30.4310439"
               ,"origin":"https://beta.auchan.zakaz.ua"
               ,"referer":"https://beta.auchan.zakaz.ua/uk/"
               ,"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
               ,"x-chain":"auchan"}
    try:
        response = requests.get(url, headers=headers) #, timeout=5
    except requests.exceptions.ConnectionError:
        logger.info("Novus Connection refused")
        return False    
    # print the response status code
    print(response.status_code)
    if response.status_code==200:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            logger.info("Response Not JSON: {}".format(response.text))
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
    updater.dispatcher.add_handler(CallbackQueryHandler(register_monitoring_user, pattern=r'^monitoringstore ')) 
    updater.dispatcher.add_handler(CallbackQueryHandler(unsubscribe_monitoring_user, pattern=r'^unsubscribestore ')) 
    updater.dispatcher.add_handler(CommandHandler('stop_monitoring', stop_monitoring))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, text))
    updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    #error logging handler
    updater.dispatcher.add_error_handler(error)


    # Run bot
    updater.start_polling()
    
    # Start monitoring in thread
    global monitoring  
    monitoring = Monitoring(updater) # create parallel thread
    monitoring.daemon = True # stop the thread if the main thread quits
    monitoring.start()
    #print(threading.active_count())
    
        
    # Stop the Bot when Ctrl+C received
    updater.idle()


if __name__ == '__main__':
    logger.info("Starting bot")
    main()

