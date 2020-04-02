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

# Link for donate
DONATE_LINK = config.DONATE_LINK


# Default stores monitoring period:
MONITORING_PERIOD = 2016 #week with 5 min interval

# Pickle to store unique users
USERS_PICKLE = os.path.join(dn,"users.pkl")
# Pickle to store megarmarket and ashan notification users
MM_USERS_PICKLE = os.path.join(dn,"megamarket_users.pkl")
METRO_USERS_PICKLE = os.path.join(dn,"metro_users.pkl")
NOVUS_USERS_PICKLE = os.path.join(dn,"novus_users.pkl")
ASHAN_USERS_PICKLE = os.path.join(dn,"ashan_users.pkl")
LOG = os.path.join(dn,"zakaz_ua_bot.log")

CHAIN_STORES_DICT = {'Megamarket':{'48267601':"МегаМаркет на Суркова 3",
                                   '48267602':"МегаМаркет 'Космополіт' на В.Гетьмана 6"},
                     'Metro':{'48215610':"METRO на Григоренка 43",
                              '48215611':"METRO Теремки на Кільцева 1В",
                              '48215633':"METRO Троещина на С.Лифаря 2А"},
                     'Novus':{'482010105':"NOVUS SkyMall на пр.Ватутіна 2Т",
                              '48201029':"NOVUS на Кільцева 12",
                              '48201070':"NOVUS на Здолбунівська 7"},
                     'Ashan':{'48246403':"Ашан на Кільцева 4",
                              '48246401':"Ашан Петрівка на пр. С.Бандери 15А"}}
CHAIN_LINK_DICT = {'Megamarket':"https://megamarket.zakaz.ua/uk/",
                     'Metro':"https://beta.metro.zakaz.ua/uk",
                     'Novus':"https://novus.zakaz.ua/uk/",
                     'Ashan':"https://beta.auchan.zakaz.ua/uk/"}

# Enable logging
logger = logging.getLogger(__name__) 
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Write log to the file
fileHandler = logging.FileHandler(LOG, encoding='utf-8') #mode='w'
#fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
# Print log to the screen
consoleHandler = logging.StreamHandler()
#consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

#######################################################
class Monitoring(Thread):
    """Class for monitoring thread"""
    def __init__(self, updater):
        super(Monitoring, self).__init__()
        self.running = True
        self.updater = updater
        self.init_status = {}

    def store_check_free_slot_(self, chain_id, chain_users_dict):
        if len(chain_users_dict)>0:
            for store_id in chain_users_dict.keys():
                store_users_dict = chain_users_dict[store_id]
                store_description = CHAIN_STORES_DICT[chain_id][store_id]
                store_link = CHAIN_LINK_DICT[chain_id]
                try:
                    self.init_status[store_id]
                except:
                    self.init_status[store_id] = False   
                logger.info('Checking {}, {}, monitoring users: {}'.format(chain_id,store_id,len(store_users_dict)))
                if len(store_users_dict)>0:
                    del_plan = get_delivery_plan(chain_id, store_id)
                    status = check_status_stores(del_plan)
                    if status[0]:
                        logger.info('Free slot in {}, {}'.format(chain_id,store_id))               
                        if self.init_status[store_id] != status[2]:
                            for usr in store_users_dict.keys():
                                try:
                                    self.updater.bot.send_message(chat_id=usr, text="😎 З'явився вільний слот в графіку доставки {}. Найближчий {}, {} \n{} \nЯ повідомлю про зміни.".format(store_description,status[1],status[2],store_link), disable_web_page_preview=True)
                                except Unauthorized:
                                    logger.info("User blocked bot: {},{}".format(usr, store_users_dict[usr])) 
                                except TimedOut:
                                    logger.info("Message sending timed out..")                         
                    elif self.init_status[store_id] != False:
                        for usr in store_users_dict.keys():
                            try:
                                self.updater.bot.send_message(chat_id=usr, text="😕 Більше немає вільних слотів в графіку доставки {}. Повідомлю коли з’явиться.".format(store_description))
                            except Unauthorized:
                                    logger.info("User blocked bot: {},{}".format(usr, store_users_dict[usr])) 
                            except TimedOut:
                                    logger.info("Message sending timed out..") 
                    self.init_status[store_id] = status[2] 
                    
    def run(self):
        while self.running:
            # Zakaz.ua store monitoring
            #Megamarket    
            try:
                with open(MM_USERS_PICKLE, 'rb') as f:
                        megamarket_stores = pickle.load(f)
            except:
                megamarket_stores = {}
            self.store_check_free_slot_('Megamarket', megamarket_stores)   
        
            #Metro    
            try:
                with open(METRO_USERS_PICKLE, 'rb') as f:
                        metro_stores = pickle.load(f)
            except:
                metro_stores = {}
            self.store_check_free_slot_('Metro', metro_stores) 
            
            #Novus  
            try:
                with open(NOVUS_USERS_PICKLE, 'rb') as f:
                        novus_stores = pickle.load(f)
            except:
                novus_stores = {}
            self.store_check_free_slot_('Novus', novus_stores)      
            
            #Ashan
            try:
                with open(ASHAN_USERS_PICKLE, 'rb') as f:
                            ashan_stores = pickle.load(f)
            except:
                ashan_stores = {}
            self.store_check_free_slot_('Ashan', ashan_stores)     
               
            time.sleep(240+np.random.randint(-5,5))
                          
##############################################################     
    
# Define command handlers
def start(update, context):
    logger.info("User {} started bot".format(update.effective_user["id"])) #update.message.chat_id
    update.message.reply_text('Привіт, {}'.format(update.message.from_user.first_name))
    #custom keyborad
    custom_keyboard = [['/start', '/help'],['/select_chain']]  #'
    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard, resize_keyboard=True, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                     text="Цей бот створений для моніторингу доступних слотів у графіку доставки магазинів на zakaz.ua (поки що - Мегамаркет, Метро, Новус та Ашан) у Києві.\nВиберіть магазин у '/select_chain'",
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
    
def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                            text="""
    Цей бот створений для моніторингу доступних слотів у графіку доставки магазинів на zakaz.ua (поки що - Мегамаркет, Метро, Новус та Ашан) у Києві.
Supported commands:
/start - Привітання
/select_chain - Стежити за наявними місцями в графіку доставки магазинів
/help - Опис бота, команд
/donate - Допомогти проекту

Автор боту: @oyeryomenko""")

def text(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text+" 😃")  #chat_id=update.message.chat_id
    

def select_chain(update, context):
    store_list = ['Megamarket', 'Ashan', 'Novus', 'Metro']       
    inline_kb = [[InlineKeyboardButton(s,callback_data="selected_chain "+s)] for s in store_list]    
    reply_markup = InlineKeyboardMarkup(inline_kb)
    update.message.reply_text('Оберіть мережу:', reply_markup=reply_markup)    

def select_store(update, context):
    
    query = update.callback_query
    code = query.data.split(' ')[-1]
    context.bot.answer_callback_query(query.id, "Ви обрали мережу {}".format(code))
    crossIcon = u"\u274C"
    checkIcon = u"\u2705"
    if code=='Megamarket': 
        inline_kb = [[InlineKeyboardButton(checkIcon+" МегаМаркет Суркова 3", callback_data='monitor_store Megamarket 48267601'), 
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket 48267601')],
                     [InlineKeyboardButton(checkIcon+" МегаМаркет Космополіт", callback_data='monitor_store Megamarket 48267602'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket 48267602')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        context.bot.send_message(chat_id=query.message.chat_id, text='Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup)   
        #update.message.reply_text('Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup)   
    
    elif code=='Metro':    
        inline_kb = [[InlineKeyboardButton(checkIcon+" METRO на Григоренка 43", callback_data='monitor_store Metro 48215610'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215610')],
                     [InlineKeyboardButton(checkIcon+" METRO Теремки", callback_data='monitor_store Metro 48215611'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215611')],
                     [InlineKeyboardButton(checkIcon+" METRO Троещина", callback_data='monitor_store Metro 48215633'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215633')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        context.bot.send_message(chat_id=query.message.chat_id, text='Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup) 

    elif code=='Novus':    
        inline_kb = [[InlineKeyboardButton(checkIcon+" NOVUS SkyMall", callback_data='monitor_store Novus 482010105'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus 482010105')],
                     [InlineKeyboardButton(checkIcon+" NOVUS на Кільцева 12", callback_data='monitor_store Novus 48201029'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus 48201029')],
                     [InlineKeyboardButton(checkIcon+" NOVUS Здолбунівська 7Г", callback_data='monitor_store Novus 48201070'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus 48201070')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        context.bot.send_message(chat_id=query.message.chat_id, text='Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup) 
        
    elif code=='Ashan':    
        inline_kb = [[InlineKeyboardButton(checkIcon+" Ашан на Кільцева 4", callback_data='monitor_store Ashan 48246403'), 
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246403')],
                     [InlineKeyboardButton(checkIcon+" Ашан Петрівка", callback_data='monitor_store Ashan 48246401'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246401')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        context.bot.send_message(chat_id=query.message.chat_id, text='Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup) 


def register_monitoring_user(update, context):
    logger.info("User {} registered for {}".format(update.effective_user["id"],update.callback_query.data)) 
    query = update.callback_query
    store_code = query.data.split(' ')[-1]
    chain_code = query.data.split(' ')[-2]
    context.bot.answer_callback_query(query.id, "Ви реєструєтеся на моніторинг {}".format(chain_code))
    if chain_code=='Megamarket':
        # save users to pickle (open existing)
        try:
            with open(MM_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{update.effective_chat.id:(update.effective_user["first_name"], update.effective_user["last_name"])}})
        with open(MM_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Megamarket {} user dict: {}".format(store_code, stores[store_code])) 

    elif chain_code=='Metro':
        # save users to pickle (open existing)
        try:
            with open(METRO_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{update.effective_chat.id:(update.effective_user["first_name"], update.effective_user["last_name"])}})
        with open(METRO_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Metro {} user dict: {}".format(store_code, stores[store_code])) 
        
    elif chain_code=='Novus':
        # save users to pickle (open existing)
        try:
            with open(NOVUS_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{update.effective_chat.id:(update.effective_user["first_name"], update.effective_user["last_name"])}})
        with open(NOVUS_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Novus {} user dict: {}".format(store_code, stores[store_code])) 
        
    elif chain_code=='Ashan':
        # save users to pickle (open existing)
        try:
            with open(ASHAN_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{update.effective_chat.id:(update.effective_user["first_name"], update.effective_user["last_name"])}})
        with open(ASHAN_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Ashan {} user dict: {}".format(store_code, stores[store_code])) 
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤓 Ви підписалися на моніторинг {}. \nЯ повідомлю коли з'явиться вільне вікно доставки".format(chain_code))  
    
def unsubscribe_monitoring_user(update, context):
    logger.info("User {} {}".format(update.effective_user["id"],update.callback_query.data)) 
    query = update.callback_query
    store_code = query.data.split(' ')[-1]
    chain_code = query.data.split(' ')[-2]
    context.bot.answer_callback_query(query.id, "Ви відписуєтеся від моніторингу {},{}".format(chain_code,store_code))
    
    if chain_code=='Megamarket':
        # save users to pickle (open existing)
        try:
            with open(MM_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users.pop(update.effective_chat.id, None)
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{}})
        with open(MM_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Megamarket {} user dict: {}".format(store_code, stores[store_code])) 
        
    elif chain_code=='Metro':
        # save users to pickle (open existing)
        try:
            with open(METRO_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users.pop(update.effective_chat.id, None)
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{}})
        with open(METRO_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Metro {} user dict: {}".format(store_code, stores[store_code])) 
        
    elif chain_code=='Novus':
        # save users to pickle (open existing)
        try:
            with open(NOVUS_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users.pop(update.effective_chat.id, None)
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{}})
        with open(NOVUS_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Novus {} user dict: {}".format(store_code, stores[store_code])) 
        
    elif chain_code=='Ashan':
        # save users to pickle (open existing)
        try:
            with open(ASHAN_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users.pop(update.effective_chat.id, None)
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{}})
        with open(ASHAN_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Ashan {} user dict: {}".format(store_code, stores[store_code])) 
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ви відписалися від моніторингу {}, {}".format(chain_code, store_code))  

# Stop monitoring Thread        
def stop_monitoring(update, context): #t=monitoring
    global monitoring  
    update.message.reply_text('OK, end monitoring...')
    monitoring.running = False # stop the thread    
    
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Що таке "+update.message.text+"? 🤔")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Я не розумію цієї команди.")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def donate(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Допомогти проекту: {}".format(DONATE_LINK), disable_web_page_preview=True)
    logger.info("User {} {} {} was up to donate".format(update.effective_user["id"],update.effective_user["first_name"], update.effective_user["last_name"])) 
    
############ Zakaz.ua scraping
def get_delivery_plan(chain_id, store_id):
    #add random to get request
    #rand_number = np.random.rand()
    #Get delivery schedule plan
    url = "https://stores-api.zakaz.ua/stores/"+store_id+"/delivery_schedule/plan/"  #&some_value={}".format(rand_number)
    headers = {"authority":"stores-api.zakaz.ua"
               ,"path":"/stores/"+store_id+"/delivery_schedule/plan/"
               #,"origin":"https://megamarket.zakaz.ua"
               #,"referer":"https://megamarket.zakaz.ua/uk/"
               ,"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
               #,"x-chain":"megamarket"
              }
    try:
        response = requests.get(url, headers=headers) #, timeout=5
    except requests.exceptions.ConnectionError:
        logger.info(chain_id+" Connection refused")
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
        logger.info("Error in response from {}: {}".format(chain_id, response.status_code)) 
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
    # Create Updater instance
    updater = Updater(token=TOKEN, use_context=True)

    # Register handlers in Dispatcher
    start_handler = CommandHandler('start', start) # start handler
    updater.dispatcher.add_handler(start_handler)   # register start handler
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('select_chain', select_chain))
    updater.dispatcher.add_handler(CallbackQueryHandler(select_store, pattern=r'^selected_chain '))     
    updater.dispatcher.add_handler(CallbackQueryHandler(register_monitoring_user, pattern=r'^monitor_store ')) 
    updater.dispatcher.add_handler(CallbackQueryHandler(unsubscribe_monitoring_user, pattern=r'^unsubscribe_store ')) 
    updater.dispatcher.add_handler(CommandHandler('stop_monitoring', stop_monitoring)) 
    updater.dispatcher.add_handler(CommandHandler('donate', donate))
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