import json
import urllib3
from pip._vendor import html5lib
from bs4 import BeautifulSoup
from lxml import etree
import sqlite3 
import random
import sys
import time
import gc

sys.setrecursionlimit(10**6)

connection = sqlite3.connect('database2.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS links (
	title text,
	date text,
    page_num text,
    url_end text,
    parsed_int bool
);
''')

connection.commit()
connection.close()

with open("config.json","r") as config:
    data = json.load(config)

print(f'Started at {data["toi"]["started"]}')

def next(current_page):
    current_page = current_page - 1
    global data
    if data["toi"]["max"] < current_page:
        with open('config.json', 'r+') as config:
            data = json.load(config)
            data['toi']['current'] = current_page 
            config.seek(0)        
            json.dump(data, config, indent=4)
            config.truncate()
    
    return current_page


def insert_to_db(sql_data):
    conn = sqlite3.connect("database2.db")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO links(title,date,page_num,url_end,parsed_int) VALUES (?,?,?,?,?)",
    sql_data)

    conn.commit()
    conn.close()

def parse(soup,current_page,start):
    dom = etree.HTML(str(soup))
    node_date = dom.xpath('/html/body/div[1]/table[2]/tbody/tr[2]/td[1]/div[2]/b')
    get_list_articles_1 = dom.xpath('/html/body/div[1]/table[2]/tbody/tr[2]/td[1]/div[3]/table/tbody/tr[2]/td[1]/span/a')
    get_list_articles_2 = dom.xpath('/html/body/div[1]/table[2]/tbody/tr[2]/td[1]/div[3]/table/tbody/tr[2]/td[3]/span/a')
    
    current_date = ""
    for x in node_date:
        current_date = x.text
    print(current_date)
    head_array = []
    for x in get_list_articles_1:
        #insert_to_db(x.text,current_date,current_page,x.get("href"))
        e = (x.text, current_date, current_page, x.get("href"),False)
        head_array.append(e)
        #print(current_date)
        #pass
        #print(x.text)
        #print(x.get("href"))

    for x in get_list_articles_2:
        e = (x.text, current_date, current_page, x.get("href"),False)
        head_array.append(e)

        #insert_to_db(x.text,current_date,current_page,x.get("href"))
        #print(x.text)
        #print(x.get("href"))
    insert_to_db(head_array)
    del get_list_articles_1
    del get_list_articles_2
    del head_array
    gc.collect()
    end = time.time()
    print("Time taken for function: ", end - start)
    


def get_list(current_page):
    start = time.time()
    print(f"Current page at {current_page}")
    http = urllib3.PoolManager()
    url = data["toi"]["url"]
    url = str.replace(url,"$placeholder$",str(current_page),1)
    print(url)
    passed = True
    try:
        response = http.request('GET',url,timeout=30.0,retries=10)
    except urllib3.exceptions.ConnectTimeoutError:
        passed = False
        print("Connection timedout, retrying.")
        get_list(current_page)
    except urllib3.exceptions.RequestError:
        passed = False
        print("Error with setting up request. Closing.")
    
    if passed == True:
        soup = BeautifulSoup(response.data, "html5lib")
        response.release_conn()
        parse(soup,current_page,start)
        gc.collect()
        #get_list((next(current_page)))
        

    
    #request = http.request('GET',)


if __name__ == '__main__':
    current_page = data["toi"]["current"]
    max_ = data["toi"]["max"]
    #get_list(current_page)

    while current_page > max_:
        get_list(current_page)
        current_page = next(current_page)
    