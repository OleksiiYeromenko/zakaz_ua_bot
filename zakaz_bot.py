#!/usr/bin/python3
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, CallbackQueryHandler, PicklePersistence
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from telegram.error import NetworkError, Unauthorized, TimedOut
import logging
import os
#from time import time
from datetime import datetime, timedelta
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
FURSHET_USERS_PICKLE = os.path.join(dn,"furshet_users.pkl")
LOG = os.path.join(dn,"zakaz_ua_bot.log")

CHAIN_USERS_PICKLE_DICT = {'Megamarket':MM_USERS_PICKLE, 
                           'Metro':METRO_USERS_PICKLE, 
                           'Novus':NOVUS_USERS_PICKLE, 
                           'Ashan':ASHAN_USERS_PICKLE, 
                           'Furshet':FURSHET_USERS_PICKLE}

CHAIN_STORES_DICT = {'Megamarket':{'48267601':"МегаМаркет на Суркова 3",
                                   '48267602':"МегаМаркет 'Космополіт' на В.Гетьмана 6",
                                   'Vyshhorod':"Магамаркет - Вишгород", 
                                   'Vyshneve':"МегаМаркет - Вишневе", 
                                   'Irpin':"МегаМаркет - Ірпінь", 
                                   'Brovary':"МегаМаркет - Бровари", 
                                   'Boryspil':"МегаМаркет - Бориспіль"},
                     'Metro':{'48215610':"METRO на Григоренка 43",
                              '48215611':"METRO Теремки на Кільцева 1В",
                              '48215633':"METRO Троещина на С.Лифаря 2А",
                              '48215612':"METRO Одеса",
                              '48215614':"METRO Дніпро",
                              '48215618':"METRO Запоріжжя",
                              '48215621':"METRO Вінниця",
                              '48215632':"METRO Харків",
                              '48215637':"METRO Львів",
                              '48215639':"METRO Житомир",
                            'Vyshhorod':"METRO - Вишгород", 
                            'Vyshneve':"METRO - Вишневе", 
                            'Irpin':"METRO - Ірпінь", 
                            'Brovary':"METRO - Бровари", 
                            'Boryspil':"METRO - Бориспіль"},
                     'Novus':{'482010105':"NOVUS SkyMall на пр.Ватутіна 2Т",
                              '48201029':"NOVUS на Кільцева 12",
                              '48201070':"NOVUS на Здолбунівська 7",
                            'Vyshhorod':"NOVUS - Вишгород", 
                            'Vyshneve':"NOVUS - Вишневе", 
                            'Irpin':"NOVUS - Ірпінь", 
                            'Brovary':"NOVUS - Бровари", 
                            'Boryspil':"NOVUS - Бориспіль"},
                     'Ashan':{'48246403':"Ашан на Кільцева 4",
                              '48246401':"Ашан Петрівка на пр. С.Бандери 15А",
                              '48246414':"Ашан Rive Gauche на Здолбунівська, 17",
                              '48246409':"Ашан Львів",
                              '48246414':"Ашан Рівне",
                              '48246416':"Ашан Одеса",
                              '48246429':"Ашан Дніпро",
                            'Vyshhorod':"Ашан - Вишгород", 
                            'Vyshneve':"Ашан - Вишневе", 
                            'Irpin':"Ашан - Ірпінь", 
                            'Brovary':"Ашан - Бровари", 
                            'Boryspil':"Ашан - Бориспіль", 
                            'Obukhiv':"Ашан - Обухів"},
                     'Furshet':{'48215514':"Фуршет Нивки",
                                '48215518':"Фуршет Інженерна",
                                '48215525':"Фуршет Райдужна",
                                '48215556':"Фуршет Атмосфера"}}
#CHAIN_STORES_ALIAS_DICT = {} 
CHAIN_LINK_DICT = {'Megamarket':"https://megamarket.zakaz.ua/uk/",
                   'Metro':"https://beta.metro.zakaz.ua/uk",
                   'Novus':"https://novus.zakaz.ua/uk/",
                   'Ashan':"https://beta.auchan.zakaz.ua/uk/",
                   'Furshet':"https://furshet.zakaz.ua/uk/"}


#Support different delivery schedule from the same stores but for suburb
SUBURB_STORES = {
    'Megamarket':{
        'Vyshhorod': '48267602', 
         'Vyshneve':'48267602', 
         'Irpin':'48267602', 
         'Brovary':'48267601', 
         'Boryspil':'48267601'},
    'Metro':{
        'Vyshhorod': '48215633', 
         'Vyshneve':'48215611', 
         'Irpin':'48215633', 
         'Brovary':'48215610', 
         'Boryspil':'48215610'},
    'Novus':{
        'Vyshhorod': '482010105', 
         'Vyshneve':'48201029', 
         'Irpin':'482010105', 
         'Brovary':'48201070', 
         'Boryspil':'48201070'},
    'Ashan':{
        'Vyshhorod': '48246401', 
         'Vyshneve':'48246403', 
         'Irpin':'48246401', 
         'Brovary':'48246414', 
         'Boryspil':'48246414', 
         'Obukhiv':'48246403'}}
    
SUBURB_COORDINATES = {
    'Vyshhorod': '50.582268,30.4908301', 
     'Vyshneve':'50.387402, 30.375242', 
     'Irpin':'50.5215594,30.2447725', 
     'Brovary':'50.50481130000001,30.7848282', 
     'Boryspil':'50.3501905,30.9564207', 
     'Obukhiv':'50.1304974,30.6550965'}


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
                    self.init_status[str(chain_id)+"_"+str(store_id)]
                except:
                    self.init_status[str(chain_id)+"_"+str(store_id)] = False   
                if len(store_users_dict)>0:
                    logger.info('Checking {}, {}, {}, monitoring users: {}'.format(chain_id,store_id,store_description,len(store_users_dict)))
                    #check if it's suburb - use another function
                    if store_id[0].isdigit():
                        del_plan = get_delivery_plan(chain_id, store_id)
                    else:
                        del_plan = get_delivery_plan_suburb(chain_id, store_id)
                    status = check_status_stores(del_plan)
                    if status[0]:
                        logger.info('Free slot in {}, {}'.format(chain_id,store_id))               
                        if self.init_status[str(chain_id)+"_"+str(store_id)] != status[2]:
                            for usr in store_users_dict.keys():
                                try:
                                    self.updater.bot.send_message(chat_id=usr, text="😎 Є вільний слот в графіку доставки {}. Найближчий {}, {} \n{} \nЯ повідомлю про зміни.".format(store_description,status[1],status[2],store_link), disable_web_page_preview=True)
                                except Unauthorized:
                                    logger.info("User {}, {} blocked bot, removing from subscription list".format(usr, store_users_dict[usr])) 
                                    # delete users from subscription list if he blocked bot
                                    try:
                                        with open(CHAIN_USERS_PICKLE_DICT[chain_id], 'rb') as f:
                                                stores = pickle.load(f)
                                    except:
                                        stores = {}
                                    try:
                                        registered_users = stores[store_id]
                                        registered_users.pop(usr, None)
                                        stores.update({store_id:registered_users})
                                    except:
                                        stores.update({store_id:{}})
                                    with open(CHAIN_USERS_PICKLE_DICT[chain_id], 'wb') as f:
                                        pickle.dump(stores, f)
                                    logger.info("{} {} user dict: {}".format(chain_id, store_id, stores[store_id])) 
                                except TimedOut:
                                    logger.info("Message sending timed out..")                         
                    elif self.init_status[str(chain_id)+"_"+str(store_id)] != False:
                        for usr in store_users_dict.keys():
                            try:
                                self.updater.bot.send_message(chat_id=usr, text="😕 Більше немає вільних слотів в графіку доставки {}. Повідомлю коли з’явиться.".format(store_description))
                            except Unauthorized:
                                    logger.info("User blocked bot: {},{}".format(usr, store_users_dict[usr])) 
                            except TimedOut:
                                    logger.info("Message sending timed out..") 
                    self.init_status[str(chain_id)+"_"+str(store_id)] = status[2] 
                    
    def run(self):
        while self.running:
            # Zakaz.ua store monitoring
            for chain_id, chain_pickle in CHAIN_USERS_PICKLE_DICT.items():
                try:
                    with open(chain_pickle, 'rb') as f:
                            chain_stores = pickle.load(f)
                except:
                    chain_stores = {}
                self.store_check_free_slot_(chain_id, chain_stores) 
            # Make less frequent checks at night
            current_time = datetime.now().strftime("%H:%M")
            if (int(current_time[:2])>8)&(int(current_time[:2])<23):
                time.sleep(300+np.random.randint(-5,5))
            else:
                time.sleep(1800+np.random.randint(-5,5))

##############################################################     
    
# Define command handlers
def start(update, context):
    logger.info("User {} started bot".format(update.effective_user["id"])) #update.message.chat_id
    update.message.reply_text('Привіт, {}'.format(update.message.from_user.first_name))
    #custom keyborad
    custom_keyboard = [['/start', '/select_chain'],['/status', '/help']]  #/donate
    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard, resize_keyboard=True, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id
                             , text="""Цей бот створений для моніторингу доступних слотів у графіку доставки магазинів на zakaz.ua (мережі Мегамаркет, Метро, Новус, Ашан та Фуршет). 
    Нажаль, через різні конфігурації зон доставки серед магазинів та їх не відповідність до адміністративного поділу, моніторинг встановлюється по найближчим магазинами а не за районами.
    Оберіть мережу та магазини для відслідковування у /select_chain"""
                             , reply_markup=reply_markup)
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
    Цей бот створений для моніторингу доступних слотів у графіку доставки магазинів на zakaz.ua (мережі Мегамаркет, Метро, Новус, Ашан та Фуршет).
Нажаль, через різні конфігурації зон доставки серед магазинів та їх не відповідність до адміністративного поділу, моніторинг встановлюється по найближчим магазинами а не за районами.
Supported commands:
/start - Привітання
/select_chain - Стежити за наявними місцями в графіку доставки магазинів
/status - Перевірити статус підписки на магазини
/help - Опис бота, команд
/donate - Допомогти проекту

Автор боту: @oyeryomenko""")

def text(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text+" 😃")  #chat_id=update.message.chat_id
    

def select_chain(update, context):
    store_list = ['Megamarket', 'Ashan', 'Novus', 'Metro', 'Furshet']       
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
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket 48267602')],
                     [InlineKeyboardButton(checkIcon+" МегаМаркет Вишгород", callback_data='monitor_store Megamarket Vyshhorod'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket Vyshhorod')],
                     [InlineKeyboardButton(checkIcon+" МегаМаркет Вишневе", callback_data='monitor_store Megamarket Vyshneve'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket Vyshneve')],
                     [InlineKeyboardButton(checkIcon+" МегаМаркет Ірпінь", callback_data='monitor_store Megamarket Irpin'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket Irpin')],
                     [InlineKeyboardButton(checkIcon+" МегаМаркет Бровари", callback_data='monitor_store Megamarket Brovary'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket Brovary')],
                     [InlineKeyboardButton(checkIcon+" МегаМаркет Бориспіль", callback_data='monitor_store Megamarket Boryspil'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Megamarket Boryspil')]
                    ]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        #context.bot.send_message(chat_id=query.message.chat_id, text='Встановіть моніторинг вільних слотів доставки по найближчим магазинам, що найвирогідніше обслуговують ваш район:', reply_markup=reply_markup) 
        #update.message.reply_text('Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup)   
    
    elif code=='Metro':    
        inline_kb = [[InlineKeyboardButton(checkIcon+" METRO на Григоренка 43", callback_data='monitor_store Metro 48215610'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215610')],
                     [InlineKeyboardButton(checkIcon+" METRO Теремки", callback_data='monitor_store Metro 48215611'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215611')],
                     [InlineKeyboardButton(checkIcon+" METRO Троещина", callback_data='monitor_store Metro 48215633'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215633')],
                     [InlineKeyboardButton(checkIcon+" METRO Вишгород", callback_data='monitor_store Metro Vyshhorod'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro Vyshhorod')],
                     [InlineKeyboardButton(checkIcon+" METRO Вишневе", callback_data='monitor_store Metro Vyshneve'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro Vyshneve')],
                     [InlineKeyboardButton(checkIcon+" METRO Ірпінь", callback_data='monitor_store Metro Irpin'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro Irpin')],
                     [InlineKeyboardButton(checkIcon+" METRO Бровари", callback_data='monitor_store Metro Brovary'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro Brovary')],
                     [InlineKeyboardButton(checkIcon+" METRO Бориспіль", callback_data='monitor_store Metro Boryspil'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro Boryspil')],
                     [InlineKeyboardButton(checkIcon+" METRO Одеса", callback_data='monitor_store Metro 48215612'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215612')],
                     [InlineKeyboardButton(checkIcon+" METRO Дніпро", callback_data='monitor_store Metro 48215614'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215614')],
                     [InlineKeyboardButton(checkIcon+" METRO Запоріжжя", callback_data='monitor_store Metro 48215618'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215618')],
                     [InlineKeyboardButton(checkIcon+" METRO Вінниця", callback_data='monitor_store Metro 48215621'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215621')],
                     [InlineKeyboardButton(checkIcon+" METRO Харків", callback_data='monitor_store Metro 48215632'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215632')],
                     [InlineKeyboardButton(checkIcon+" METRO Львів", callback_data='monitor_store Metro 48215637'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215637')],     
                     [InlineKeyboardButton(checkIcon+" METRO Житомир", callback_data='monitor_store Metro 48215639'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Metro 48215639')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        #context.bot.send_message(chat_id=query.message.chat_id, text='Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup) 
     
    elif code=='Novus':    
        inline_kb = [[InlineKeyboardButton(checkIcon+" NOVUS SkyMall", callback_data='monitor_store Novus 482010105'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus 482010105')],
                     [InlineKeyboardButton(checkIcon+" NOVUS на Кільцева 12", callback_data='monitor_store Novus 48201029'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus 48201029')],
                     [InlineKeyboardButton(checkIcon+" NOVUS Здолбунівська 7Г", callback_data='monitor_store Novus 48201070'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus 48201070')],
                     [InlineKeyboardButton(checkIcon+" NOVUS Вишгород", callback_data='monitor_store Novus Vyshhorod'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus Vyshhorod')],
                     [InlineKeyboardButton(checkIcon+" NOVUS Вишневе", callback_data='monitor_store Novus Vyshneve'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus Vyshneve')],
                     [InlineKeyboardButton(checkIcon+" NOVUS Ірпінь", callback_data='monitor_store Novus Irpin'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus Irpin')],
                     [InlineKeyboardButton(checkIcon+" NOVUS Бровари", callback_data='monitor_store Novus Brovary'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus Brovary')],
                     [InlineKeyboardButton(checkIcon+" NOVUS Бориспіль", callback_data='monitor_store Novus Boryspil'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Novus Boryspil')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        #context.bot.send_message(chat_id=query.message.chat_id, text='Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup) 
        
    elif code=='Ashan':    
        inline_kb = [[InlineKeyboardButton(checkIcon+" Ашан на Кільцева 4", callback_data='monitor_store Ashan 48246403'), 
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246403')],
                     [InlineKeyboardButton(checkIcon+" Ашан Петрівка", callback_data='monitor_store Ashan 48246401'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246401')],
                     [InlineKeyboardButton(checkIcon+" Ашан Rive Gauche", callback_data='monitor_store Ashan 48246414'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246414')],
                     [InlineKeyboardButton(checkIcon+" Ашан Вишгород", callback_data='monitor_store Ashan Vyshhorod'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan Vyshhorod')],
                     [InlineKeyboardButton(checkIcon+" Ашан Вишневе", callback_data='monitor_store Ashan Vyshneve'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan Vyshneve')],
                     [InlineKeyboardButton(checkIcon+" Ашан Ірпінь", callback_data='monitor_store Ashan Irpin'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan Irpin')],
                     [InlineKeyboardButton(checkIcon+" Ашан Бровари", callback_data='monitor_store Ashan Brovary'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan Brovary')],
                     [InlineKeyboardButton(checkIcon+" Ашан Бориспіль", callback_data='monitor_store Ashan Boryspil'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan Boryspil')],
                     [InlineKeyboardButton(checkIcon+" Ашан Обухів", callback_data='monitor_store Ashan Obukhiv'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan Obukhiv')],
                     [InlineKeyboardButton(checkIcon+" Ашан Львів", callback_data='monitor_store Ashan 48246409'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246409')],
                     [InlineKeyboardButton(checkIcon+" Ашан Рівне", callback_data='monitor_store Ashan 48246414'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246414')],
                     [InlineKeyboardButton(checkIcon+" Ашан Одеса", callback_data='monitor_store Ashan 48246416'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246416')],
                     [InlineKeyboardButton(checkIcon+" Ашан Дніпро", callback_data='monitor_store Ashan 48246429'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Ashan 48246429')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
        #context.bot.send_message(chat_id=query.message.chat_id, text='Оберіть на який магазин що здійснює доставку підписатися:', reply_markup=reply_markup) 

    elif code=='Furshet':
        inline_kb = [[InlineKeyboardButton(checkIcon+" Фуршет Нивки", callback_data='monitor_store Furshet 48215514'), 
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Furshet 48215514')],
                     [InlineKeyboardButton(checkIcon+" Фуршет Інженерна", callback_data='monitor_store Furshet 48215518'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Furshet 48215518')],
                     [InlineKeyboardButton(checkIcon+" Фуршет Райдужна", callback_data='monitor_store Furshet 48215525'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Furshet 48215525')],
                     [InlineKeyboardButton(checkIcon+" Фуршет Атмосфера", callback_data='monitor_store Furshet 48215556'),
                      InlineKeyboardButton(crossIcon+" Відписатися", callback_data='unsubscribe_store Furshet 48215556')]]
        reply_markup = InlineKeyboardMarkup(inline_kb)
    context.bot.send_message(chat_id=query.message.chat_id, text='Встановіть моніторинг вільних слотів доставки zakaz.ua по найближчим магазинам, що найвирогідніше обслуговують ваш район:', reply_markup=reply_markup, disable_web_page_preview=True) 


def register_monitoring_user(update, context):
    logger.info("User {} registered for {}".format(update.effective_user["id"],update.callback_query.data)) 
    query = update.callback_query
    store_code = query.data.split(' ')[-1]
    chain_code = query.data.split(' ')[-2]
    context.bot.answer_callback_query(query.id, "Ви реєструєтеся на моніторинг {}, магазин {}".format(chain_code, store_code))
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
    
    elif chain_code=='Furshet':
        # save users to pickle (open existing)
        try:
            with open(FURSHET_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users[update.effective_chat.id] = (update.effective_user["first_name"], update.effective_user["last_name"])
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{update.effective_chat.id:(update.effective_user["first_name"], update.effective_user["last_name"])}})
        with open(FURSHET_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Furshet {} user dict: {}".format(store_code, stores[store_code])) 
    store_description = CHAIN_STORES_DICT[chain_code][store_code]
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤓 Ви підписалися на моніторинг {}.".format(store_description))
    #Check current status immediately:
    if store_code[0].isdigit():
        del_plan = get_delivery_plan(chain_code, store_code)
    else:
        del_plan = get_delivery_plan_suburb(chain_code, store_code)
    status = check_status_stores(del_plan)
    if status[0]:
        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text="😊 Пощастило! Зараз є вільний слот в графіку доставки - {}, {} \n{} \nЯ повідомлю про зміни.".format(status[1],status[2],CHAIN_LINK_DICT[chain_code]), disable_web_page_preview=True)
        except:
            pass
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нажаль наразі немає вільних слотів в графіку доставки. \nЯ повідомлю коли з'явиться вільне вікно.")
                     
                     
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

    elif chain_code=='Furshet':
        # save users to pickle (open existing)
        try:
            with open(FURSHET_USERS_PICKLE, 'rb') as f:
                    stores = pickle.load(f)
        except:
            stores = {}
        try:
            registered_users = stores[store_code]
            registered_users.pop(update.effective_chat.id, None)
            stores.update({store_code:registered_users})
        except:
            stores.update({store_code:{}})
        with open(FURSHET_USERS_PICKLE, 'wb') as f:
            pickle.dump(stores, f)
        logger.info("Furshet {} user dict: {}".format(store_code, stores[store_code]))    
    store_description = CHAIN_STORES_DICT[chain_code][store_code]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ви відписалися від моніторингу {}".format(store_description))  
    
# Show subscription status
def status(update, context):
    status_list = []
    display_status=""
    usr = update.effective_chat.id
    for chain_name, chain_pickle in CHAIN_USERS_PICKLE_DICT.items():
        try:
            with open(chain_pickle, 'rb') as f:
                chain_stores = pickle.load(f)
        except:
                chain_stores = {}
        for store_id, users_dicts in chain_stores.items():
            store_description = CHAIN_STORES_DICT[chain_name][store_id]
            if usr in users_dicts.keys():
                status_list.append((chain_name, store_id, store_description))
                display_status=display_status + store_description +"\n"

    if len(status_list)>0:
        context.bot.send_message(chat_id=usr, text='Ви підписані на наступні магазини: \n{}'.format(display_status))
        crossIcon = u"\u274C"
        inline_kb = [[InlineKeyboardButton(crossIcon+" "+s[2],callback_data='unsubscribe_store {} {}'.format(s[0],s[1]))] for s in status_list]
        reply_markup = InlineKeyboardMarkup(inline_kb)       
        context.bot.send_message(chat_id=usr, text='Відписатися?', reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=usr, text='Ви не підписані на жоден магазин')             
                     
# Stop monitoring Thread        
def stop_monitoring(update, context): #t=monitoring
    if update.effective_chat.id==109458488:
        global monitoring  
        update.message.reply_text('OK, end monitoring...')
        monitoring.running = False # stop the thread    
        logger.info("MONITORING STOPPED!!!") 
    else:
        logger.info("User {} {} {} tried to stop monitoring".format(update.effective_user["id"],update.effective_user["first_name"], update.effective_user["last_name"])) 
    
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

def get_delivery_plan_suburb(chain_id, city):
    #get coords:
    coords = SUBURB_COORDINATES[city]
    #get store_id:
    store_id = SUBURB_STORES[chain_id][city]
    
    #Get delivery schedule plan
    url = "https://stores-api.zakaz.ua/stores/"+store_id+"/delivery_schedule/plan/?coords="+coords
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
    updater.dispatcher.add_handler(CommandHandler('status', status))
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