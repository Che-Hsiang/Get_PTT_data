# -*- coding: UTF-8 -*-
import sys,os
import re
import urllib
import time
import calendar
import sqlite3
import datetime
import json
import sys
from time import sleep
from pyquery import PyQuery as pq
from random import randint

main_url = 'https://www.ptt.cc'
db_name = 'ptt.db'

headers1 = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
headers2 = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
headers3 = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
headers4 = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
headers5 = {'User-Agent':'Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36'}
headers = [headers1,headers2,headers3,headers4,headers5]

def start_download_data(target_board,target_url,target_date,target_folder,continue_flag = False):

    print('本頁網址為: %s' % target_url)

    if continue_flag is True or continue_flag == 'True':
        write_flag(target_board,target_url,target_date,target_folder)
    else:
        print('本次不寫入flag')

    print('準備開始爬文章標題')
    dom = pq(url=target_url,cookies={'over18' : '1'},headers=headers[randint(0,len(headers)-1)])
    print('文章標題取得完畢')

    if target_url[-10:] == 'index.html':
        contents = dom('.r-list-container').children('.r-list-sep').prev_all('.r-ent')
    else:
        contents = dom('.r-list-container').children('.r-ent')

    #上一頁
    pre_page = main_url + dom('.wide').eq(1).attr('href')
    target_date_len =  len(target_date)
    date_list = []
    for content in contents.items():
        #取得文章標題內容
        web_date = get_web_data(content)
        if web_date is None:
            print('此文已被刪除,繼續爬下一篇')
        else:
            #若是該文章為 投票、公告、水桶之類的，就跳過不擷取
            try:
                web_detail_data_html = web_date['article_url']
                print('準備爬取 %s 文章' % web_detail_data_html)
                #文章代碼
                article_code = web_detail_data_html.strip('.html').strip(target_url_head)
                web_date['article_code'] = article_code
                web_date['board_name'] = target_board
                web_date['post_version'] = get_post_version(web_date['article_code'])

                #取得文章內容
                web_detail_data = get_web_detail_data(web_detail_data_html)
                yymmdd_date = web_detail_data['post_date'][:10]

                date_list.append(yymmdd_date[:target_date_len])

                #取得推文內容
                web_detail_push_data = get_web_detail_push_data(web_detail_data_html,yymmdd_date)

                ptt_data = {}
                ptt_data = web_date.copy()
                ptt_data.update(web_detail_data)
                ptt_data.update(web_detail_push_data)

            except Exception as e:
                print(e)
                print('此 %s 有問題，跳過此文章' % web_detail_data_html)
                pass

            else:
                #新增資料到DB
                insert_article_data_to_db(ptt_data,article_code)
                insert_push_data_to_db(ptt_data,article_code)
                insert_url_data_to_db(ptt_data,article_code)

        timeNum = randint(1,5)
        print('倒數 %s 秒後開始' % timeNum)
        time.sleep(timeNum)

    old_date = date_list[0]
    newDate = date_list[len(date_list)-1]

    if target_date > old_date:
        print('結束爬文')
    else:
        print('準備爬上一頁')
        start_download_data(target_board,pre_page,target_date,target_folder,continue_flag)

#寫入現在的flag
def write_flag(target_board,target_url,target_date,target_folder):
    file_name = target_board
    try:
        print('準備寫入flag')
        f = open(file_name,'w')
        f.write(target_board)
        f.write('\n')
        f.write(target_url)
        f.write('\n')
        f.write(target_date)
        f.write('\n')
        f.write(target_folder)
        print('flag寫入完畢')
    except Exception as e:
        print('寫入flag發生了一些問題')
        print(e)
    finally:
        f.close()

#讀取上次的flag
def read_flag(flag):
    try:
        print('準備讀取flag')
        f = open(flag,'r')
        flag = f.readlines()
        print('flag讀取完畢')
        return flag
    except Exception as e:
        print(e)
        print('讀取flag發生了一些問題')
    finally:
        f.close()

#取得文章版本
def get_post_version(article_code):
    try:
        print('取得文章版本中')
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        sql =   """select ad.article_code,max(post_version) as max_version
                    from article_data as ad
                    where ad.article_code = '%s'
                    group by ad.article_code
                """ % article_code
        cur.execute(sql)
        res = cur.fetchone()
        print('文章版本取得完畢')
        if res is None:
            return '0'
        else:
            return res[1] + 1
    except Exception as e:
        print(e)
        print('文章版本取得發生一些問題')
        return '0'
    finally:
        conn.close()

#取得文章推文內容
#去除 ' 單引號，用@代替
def get_web_detail_push_data(web_detail_data_html,yymmdd_date):
    print('取得推文內容中')
    dom = pq(url=web_detail_data_html,cookies={'over18' : '1'},headers=headers[randint(0,len(headers)-1)])
    push_datas = dom('.push')
    push_data_list = []
    count = 0
    for push_data in push_datas.items():
        count = count + 1
        push_data_dict = {}
        push_data_dict['push_no'] = count
        push_data_dict['push_tag'] = push_data('.push-tag').text()
        push_data_dict['push_id'] = push_data('.push-userid').text()
        push_data_dict['push_text'] = push_data('.push-content').text().replace("'","''")
        push_data_dict['push_date'] = yymmdd_date + ' ' + push_data('.push-ipdatetime').text()[-5:]
        push_data_list.append(push_data_dict)

    push_data_dicts = {}
    push_data_dicts['web_detail_push_data']= push_data_list
    print('推文內容取得完畢')
    return push_data_dicts


#取得文章的內容與內容網址
#去除 ' 單引號，用@代替
def get_web_detail_data(web_detail_data_html):
    print('取得文章內容中')
    dom = pq(url=web_detail_data_html,cookies={'over18' : '1'},headers=headers[randint(0,len(headers)-1)])

    #取得po文時間
    post_date = time_format_transfer(dom('.article-meta-value').eq(3).text())

    get_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    #取得文章內的網址
    web_urls = dom('#main-content').remove('.richcontent').find('a')
    urls = []
    for web_url in web_urls.items():
        urls.append(web_url.attr('href'))
    #將最後本文的網址去掉
    urls.pop()

    #取得文章的內文
    article = dom('#main-content').remove('*').text().replace("'",'@')

    article = article.replace('\n','<br>')

    #po文時間，文章內容，網址們
    web_detail_dict = {
                        'post_date'          :   post_date,
                        'article_content'    :   article,
                        'urls'              :   urls,
                        'get_date'           :   get_date
                    }
    print('文章內容取得完畢')
    return web_detail_dict

#取得每頁文章標題列的內容
def get_web_data(target_content):
    try:
        print('取得文章標題內容中')
        nrec = target_content('.nrec').children().text()
        mmdd_date = target_content('.date').text()
        html = main_url + target_content('.title').children().attr('href')
        title = target_content('.title').children().text().replace("'","''")
        author = target_content('.author').text()

        nrec = nrec.strip(' ')

        if nrec == '爆':
            nrec = 99
        elif nrec == '':
            nrec = 0
        elif nrec.find('X') > 0:
            nrec = int(nrec.strip('X'))
            nrec = nrec - 2 * nrec

        #推數、月日時間、連結網址、標題、作者
        web_dict =   {
                              'article_nrec'    :   nrec,
                              'mmdd_date':   mmdd_date,
                              'article_url'    :   html,
                              'article_title'   :   title,
                              'author_id'  :   author
                    }
    except:
        return None
    else:
        print('文章標題內容取得完畢')
        return web_dict

#新增文章資料至db
def insert_article_data_to_db(ptt_data,article_code):
    try:
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        print('DB連線建立中')

        print('確認文章資料')
#        print(ptt_data)

        article_data_sql =    """insert into article_data (board_name,article_code,article_url,article_title,author_id,article_content,article_nrec,post_version,post_date,get_date)
                                select '%(board_name)s','%(article_code)s','%(article_url)s','%(article_title)s','%(author_id)s','%(article_content)s','%(article_nrec)s','%(post_version)s','%(post_date)s','%(get_date)s'
                                where not exists
                                (select 1
                                from article_data
                                where board_name = '%(board_name)s'
                                and article_code = '%(article_code)s'
                                and article_title = '%(article_title)s'
                                and article_content = '%(article_content)s'
                                and article_nrec = '%(article_nrec)s'
                                );
                            """ % ptt_data

        cur.execute(article_data_sql)

        checkArticleRes =  cur.rowcount

#        if checkArticleRes > 0:
#            print('文章資料確認完畢')
#        else:
#            print('文章資料已存在，故跳過新增此文章')
        print('準備新增文章資料')
        conn.commit()
        print('資料新增完畢')
        conn.close()
    except Exception as e:
        print(e)
        print('###########################糟糕 sql 指令出了些問題##############################')
        conn.rollback()
        conn.close()
        print("三秒後重新執行")
        sleep(3)
        insert_article_data_to_db(ptt_data,article_code)

#新增推文資料到DB
def insert_push_data_to_db(ptt_data,article_code):
    try:

        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        print('DB連線建立中')

        print('確認推文資料')
        for push_data in ptt_data['web_detail_push_data']:
            push_data['article_code'] = article_code
            push_datasql =   """insert into push_data (article_code,push_no,push_id,push_text,push_tag,push_date)
                               select '%(article_code)s','%(push_no)s','%(push_id)s','%(push_text)s','%(push_tag)s','%(push_date)s'
                               where not exists
                               (select 1
                               from push_data
                               where article_code = '%(article_code)s'
                               and push_no = '%(push_no)s'
                               and push_id = '%(push_id)s'
                               and push_text = '%(push_text)s'
                               and push_tag = '%(push_tag)s'
                               and push_date = '%(push_date)s'
                               );
                            """ % push_data

            cur.execute(push_datasql)

            check_push_res = cur.rowcount

#            if check_push_res > 0:
#                print('第 %s 推文資料新增成功' % push_data['push_no'])
#            else:
#                print('第 %s 推文資料已存在，故跳過此推文' % push_data['push_no'])

        print('準備新增推文資料')
        conn.commit()
        print('資料新增完畢')
        conn.close()
    except Exception as e:
        print(e)
        print('###########################糟糕 sql 指令出了些問題##############################')
        conn.rollback()
        conn.close()
        print("三秒後重新執行")
        sleep(3)
        insert_push_data_to_db(ptt_data,article_code)

#新增url資料到DB
def insert_url_data_to_db(ptt_data,article_code):
    try:
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        print('DB連線建立中')

        print('確認url資料')
        for url_data in ptt_data['urls']:
            url_dataSql =    """insert into url_data (article_code,url_link,url_owner_id)
                               select '%(article_code)s','%(url_link)s','%(url_owner_id)s'
                               where not exists
                               (select 1
                               from url_data
                               where article_code = '%(article_code)s'
                               and url_link = '%(url_link)s'
                               and url_owner_id = '%(url_owner_id)s'
                               );
                            """ % ({'article_code':article_code,'url_link':url_data,'url_owner_id':ptt_data['author_id']})
            cur.execute(url_dataSql)

            check_url_res = cur.rowcount

#            if check_url_res > 0:
#                print('url: %s 準備新增' % url_data)
#            else:
#                print('url: %s 已存在，故跳過此url' % url_data)

        print('準備新增url資料')
        conn.commit()
        print('資料新增完畢')
        conn.close()
    except Exception as e:
        print(e)
        print('###########################糟糕 sql 指令出了些問題##############################')
        conn.rollback()
        conn.close()
        print("三秒後重新執行")
        sleep(3)
        insert_url_data_to_db(ptt_data,article_code)

#確認db檔是否存在，若不存在則創db
def check_db_exist():
    if os.path.exists(db_name) is False:
        print('DB不存在,即將建立DB')
        create_db()
    else:
        print('DB存在')

def create_db():
    #print(create_table.sql)
    f = open('ptt.db','w')
    f.close()
    s = open('create_table.json')
    sql = json.load(s)
    s.close()
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(sql['article_data'])
    cur.execute(sql['push_data'])
    cur.execute(sql['url_data'])
    conn.commit()
    conn.close()
    print('DB建立完畢')

def time_format_transfer(oriTime):

    datatime_format = "%a %b %d %H:%M:%S %Y"
    ori_time_str = time.strptime(oriTime,datatime_format)
    new_time_str = time.strftime("%Y-%m-%d %H:%M:%S", ori_time_str)

    return new_time_str

def help():
    print('===========================================================================')
    print('python3 main_pyquery.py target_board target_date target_folder continue_flag')
    print('')
    print('範例：')
    print('     python3 main_pyquery.py Stock 2008 test True')
    print('')
    print('格式:')
    print('    target_board  = MAC or Beauty')
    print('    target_date   = 2017-07-01 or 2017-07 or 2017')
    print('    target_folder = ~/Download')
    print('    continue_flag = True or False')
    print('說明:')
    print('    target_date : 2017-07-01  = 2017-01-01 ~ 現在')
    print('    target_date : 2017-07     = 2017-07    ~ 現在')
    print('    target_date : 2017        = 2017       ~ 現在')
    print('')
    print('===========================================================')
    print('python3 main_pyquery.py from_last_url board_flag')
    print('')
    print('範例：')
    print('    python3 main_pyquery.py from_last_url Stock')
    print('')
    print('===========================================================')
    print('需安裝套件如下：')
    print('pyquery')
    print('urllib3')
    print('===========================================================')



if __name__ == "__main__":

    if len(sys.argv) == 5 and sys.argv[1] is not None and sys.argv[2] is not None and sys.argv[3] is not None and sys.argv[4] is not None:
        check_db_exist()
        target_url_head = 'https://www.ptt.cc/bbs/' + sys.argv[1] + '/'
        target_url = 'https://www.ptt.cc/bbs/' + sys.argv[1] + '/index.html'
        start_download_data(sys.argv[1],target_url,sys.argv[2],sys.argv[3],sys.argv[4])
    elif len(sys.argv) == 3 and sys.argv[1] == 'from_last_url' and sys.argv[2] is not None:
        check_db_exist()
        pre_url = read_flag(sys.argv[2])
        target_url_head = 'https://www.ptt.cc/bbs/' + pre_url[1].strip('\n') + '/'
        target_url = 'https://www.ptt.cc/bbs/' + pre_url[1].strip('\n') + '/index.html'
        start_download_data(pre_url[0].strip('\n'),pre_url[1].strip('\n'),pre_url[2].strip('\n'),pre_url[3].strip('\n'),True)
    else:
        help()
