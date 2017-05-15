# -*- coding: UTF-8 -*-
import requests
import sys,os
import re
from bs4 import BeautifulSoup
import urllib
import time
import calendar
import sqlite3

now_url = None


def save(img_urls, title,push_count,folder):
    if img_urls:
        try:
            dname = folder + '/' + '[' + str(push_count) + ']' + title.strip()
            if os.path.exists(dname) == False:
                os.makedirs(dname)
            for img_url in img_urls:
                if img_url.split('//')[1].startswith('m.'):
                    img_url = img_url.replace('//m.', '//i.')
                if not img_url.split('//')[1].startswith('i.'):
                    img_url = img_url.split('//')[0] + '//i.' + img_url.split('//')[1]
                if not img_url.endswith('.jpg'):
                    img_url += '.jpg'
                fname = img_url.split('/')[-1]
                
                if os.path.exists(os.path.join(dname, fname)):
                    print("The file already exists : %s" % os.path.join(dname, fname))
                else:
                    print("begin : %s file_name : %s" % (img_url,fname))
                    urllib.request.urlretrieve(img_url, os.path.join(dname, fname))
                    print("end   : %s file_name : %s" % (img_url,fname))
        except Exception as e:
            print(e)

def parse(dom):
    soup = BeautifulSoup(dom, 'html.parser')
    links = soup.find(id='main-content').find_all('a')
    img_urls = []
    for link in links:
        if re.match(r'^https?://(i.)?(m.)?imgur.com', link['href']):
            img_urls.append(link['href'])
    return img_urls
    
def get_web_page(url):
    resp = requests.get(
        url=url,
        cookies={'over18': '1'}
    )
    if resp.status_code != 200:
        print('Invalid url:', resp.url)
        return None
    else:
        return resp.text

def get_articles(dom, date):
    global page_date
    soup = BeautifulSoup(dom, 'html.parser')

    articles = []
    divs = soup.find_all('div', 'r-ent')
    count = 0
    for d in divs:
        if count == 0:
            page_date = d.find('div', 'date').string.strip(' ')
            count += 1
#            print(page_date)
        if d.find('div', 'date').string.strip(' ') == date:

            push_count = 0
            if d.find('div', 'nrec').string:
                try:
                    #print(d.find('div', 'nrec').string)
                    if d.find('div', 'nrec').string == '爆':
                        push_count = 100
                    else:
                        push_count = int(d.find('div', 'nrec').string)
                except ValueError:
                    pass
       
            if d.find('a'): 
                href = main_url + d.find('a')['href']
                title = d.find('a').string
                articles.append({
                    'title': title,
                    'href': href,
                    'push_count': push_count
                })
    return articles

def start_download(url,folder,date):
    global now_url
    global date_tag

    pages = get_web_page(url)
    pages_res = get_articles(pages,date)

    print("page_date : %s" % page_date)
    print("date      : %s" % date)

    if len(pages_res) != 0:
        for page_res in pages_res:
            page = get_web_page(page_res['href'])
            img_urls = parse(page)
            if len(img_urls) > 0:
                print("title_download_begin : %s" % page_res['title'])
                save(img_urls,page_res['title'],page_res['push_count'],folder)
                print("title_download_end   : %s" % page_res['title'])
    
    if page_date != date and date_tag is True:  
        print("%s END" % date)  
        return
    elif page_date != date:
        previous_page_url = get_previous_page_url(url)
        now_url = previous_page_url
        start_download(previous_page_url,folder,date)
    elif page_date == date:
        date_tag = True
        previous_page_url = get_previous_page_url(url)
        now_url = previous_page_url
        start_download(previous_page_url,folder,date)

    

def get_previous_page_url(url):
    pages = get_web_page(url)
    soup = BeautifulSoup(pages,'html.parser')

    return main_url + soup.find(text='‹ 上頁').find_previous()['href']

def db_test():
    conn = sqlite3.connect(db_name)

    print("Opened database successfully")


def help():
    print("=========================================================")
    print(" ")
    print("Function 1:")
    print(" ")
    print("     python main.py download ptt_board folder date   ")
    print(" ")
    print("     ex:python main.py download Linux ~/Document 9/08")
    print(" ")
    print("Function 2:")
    print(" ")
    print("     python main.py download_month ptt_board folder month")
    print(" ")
    print("     ex:python main.py download_month Linux ~/Document 2")
    print("                                                Jerry Lin")
    print("=========================================================")

if __name__ == "__main__":

    main_url = 'https://www.ptt.cc'
    page_date = None
    db_name = 'test.db'
    
    if len(sys.argv) == 5 and sys.argv[1] == "download"\
        and sys.argv[2] != "" and sys.argv[3] != "" and sys.argv[4] != "":
        url = 'https://www.ptt.cc/bbs' + '/' + sys.argv[2] + '/index.html'
        if get_web_page(url) is None:
            print('ptt_board input error')
        
        date_tag = False
        start_download(url,sys.argv[3],sys.argv[4])
    elif len(sys.argv) == 5 and sys.argv[1] == "download_month"\
        and sys.argv[2] != "" and sys.argv[3] != "" and sys.argv[4] != "":
        url = 'https://www.ptt.cc/bbs' + '/' + sys.argv[2] + '/index.html'
        now_url = url
        if get_web_page(url) is None:
            print('ptt_board input error')
        year = time.strftime("%Y")
        monthRange = calendar.monthrange(int(year),int(sys.argv[4]))
        for i in range(monthRange[1],0,-1):
            date = sys.argv[4] + '/' + str(i).zfill(2)
            
            date_tag = False
            start_download(now_url,sys.argv[3],date) 
    elif len(sys.argv) == 2:
        if os.path.exists(db_name):
            db_test()
        else:
            print("DB isn't exist")
    else:
        help()

    #previous_page_url = get_previous_page_url(url)

    #print(previous_page_url)

    
















