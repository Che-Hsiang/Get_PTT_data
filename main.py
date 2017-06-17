# -*- coding: UTF-8 -*-
import requests
import sys,os
import re
from bs4 import BeautifulSoup
import urllib
import time
import calendar
import sqlite3
import datetime



def save(img_urls, title,author,push_count,folder):
    if img_urls:
        try:
            dname = folder + '/' + title.strip() + '_' + author.strip()
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
                    print("end")
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

def get_articles(dom, date_target):
    global page_date
    time.sleep(3)
    soup = BeautifulSoup(dom, 'html.parser')

    articles = []
    divs = soup.find_all('div', 'r-ent')
    if len(page_date) > 0:
        del page_date[:]

    for d in divs:
        try:
            if d.find('a').string.split(']')[0] != '[公告':
                the_page = d.find('div', 'date').string.strip(' ')

                if the_page not in page_date:
                    page_date.append(the_page)

                if d.find('div', 'date').string.strip(' ') == date_target:

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
                        author = d.find('div','author').string
                        articles.append({
                            'title': title,
                            'href': href,
                            'author': author,
                            'push_count': push_count
                        })
        except:
            continue
    return articles

def start_download(url,folder,date_target):
    global now_url
    global date_tag

    pages = get_web_page(url)
    pages_res = get_articles(pages,date_target)
#    print("now_url    : %s" % now_url)
    print("page_date  : %s" % page_date)
    print("date_target: %s" % date_target)
#    print("date_tag   : %s" % date_tag)
#    print("pages_res : %s" % len(pages_res))
    if len(pages_res) != 0:
        for page_res in pages_res:
            page = get_web_page(page_res['href'])
            img_urls = parse(page)
            if len(img_urls) > 0:
                #print("title_download_begin : %s" % page_res['title'])
                save(img_urls,page_res['title'],page_res['author'],page_res['push_count'],folder)
                #print("title_download_end   : %s" % page_res['title'])

    #上一頁日期正確，且本頁不正確，結束程式
    if date_target not in page_date and date_tag is True:
        print("%s END" % date_target)  
        return
    #日期正確，且該頁有多個日期
    if date_target in page_date and len(page_date) > 1:
        #且日期為最小值，繼續往上一頁找
        if page_date.index(date_target) == 0:
            date_tag = True
            previous_page_url = get_previous_page_url(url)
            now_url = previous_page_url
            start_download(previous_page_url,folder,date_target)
        #若日期不為最小值，終止搜尋
        else:
            print("%s END" % date_target)  
            return
    #日期正確，且該頁只有一個日期，繼續往上一頁找
    elif date_target in page_date and len(page_date) == 1:
        date_tag = True
        previous_page_url = get_previous_page_url(url)
        now_url = previous_page_url
        start_download(previous_page_url,folder,date_target)
    #若日期不等，查找上一頁
    elif date_target not in page_date:
        previous_page_url = get_previous_page_url(url)
        now_url = previous_page_url
        start_download(previous_page_url,folder,date_target)

def get_previous_page_url(url):
    pages = get_web_page(url)
    soup = BeautifulSoup(pages,'html.parser')

    return main_url + soup.find(text='‹ 上頁').find_previous()['href']

def db_test():
    conn = sqlite3.connect(db_name)

    print("Opened database successfully")

#def check_date():


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
    page_date = []
    db_name = 'test.db'
    now_url = None

    if len(sys.argv) == 5 and sys.argv[1] == "download"\
        and sys.argv[2] != "" and sys.argv[3] != "" and sys.argv[4] != "":
        url = 'https://www.ptt.cc/bbs' + '/' + sys.argv[2] + '/index.html'
        if get_web_page(url) is None:
            print('ptt_board input error')
        else:
            date_tag = False
            start_download(url,sys.argv[3],sys.argv[4])
    elif len(sys.argv) == 5 and sys.argv[1] == "download_month"\
        and sys.argv[2] != "" and sys.argv[3] != "" and sys.argv[4] != "":
        url = 'https://www.ptt.cc/bbs' + '/' + sys.argv[2] + '/index.html'
        now_url = url
        if get_web_page(url) is None:
            print('ptt_board input error')
        else:
            year = time.strftime("%Y")
            today = datetime.date.today()
            today_m = today.month

            if (str(today_m) == str(sys.argv[4])): 
                month_max = today.day
            else:       
                monthRange = calendar.monthrange(int(year),int(sys.argv[4]))
                month_max = monthRange[1]

            for i in range(month_max,0,-1):
                date_target = sys.argv[4] + '/' + str(i).zfill(2)
                date_tag = False
                start_download(now_url,sys.argv[3],date_target) 
        print('download_month END')
    elif len(sys.argv) == 2:
        if os.path.exists(db_name):
            db_test()
        else:
            print("DB isn't exist")
    else:
        help()

    #previous_page_url = get_previous_page_url(url)

    #print(previous_page_url)

    
















