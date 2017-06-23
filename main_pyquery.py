# -*- coding: UTF-8 -*-
import sys,os
import re
import urllib
import time
import calendar
import sqlite3
import datetime
import json
from pyquery import PyQuery as pq
from random import randint
mainUrl = 'https://www.ptt.cc'
dbName = 'ptt.db'

def startDownloadData(targetBoard,targetDate,targetFolder):
    print('開始爬文章')
    targetUrl = 'https://www.ptt.cc/bbs/' + targetBoard + '/index.html'
    targetUrlHead = 'https://www.ptt.cc/bbs/' + targetBoard + '/'
    dom = pq(url=targetUrl,cookies={'over18' : '1'})
    contents = dom('.r-list-container').children('.r-list-sep').prev_all('.r-ent')
    pttDatas = []
    for content in contents.items():

        webData = getWebData(content)
        if webData is None:
            print('此文已被刪除,繼續爬下一篇')
        else:
            webDetailDataHtml = webData['articleUrl']
            print(webDetailDataHtml)
            #文章代碼
            articleCode = webDetailDataHtml.strip('.html').strip(targetUrlHead)
            webData['articleCode'] = articleCode
            webData['boardName'] = targetBoard

            webDetailData = getWebDetailData(webDetailDataHtml)

            timeNum = randint(1,3)
            time.sleep(timeNum)

            pttData = {}
            pttData = webData.copy()
            pttData.update(webDetailData)
            pttDatas.append(pttData)
#    print(pttDatas)
    insertDataToDb(pttDatas)

#取得文章的內容與內容網址
def getWebDetailData(webDetailDataHtml):
    dom = pq(url=webDetailDataHtml,cookies={'over18' : '1'})

    #取得po文時間
    postDate = dom('.article-meta-value').eq(3).text()

    #取得文章內的網址
    webUrls = dom('#main-content').remove('.richcontent').find('a')
    urls = []
    for webUrl in webUrls.items():
        urls.append(webUrl.attr('href'))
    #將最後本文的網址去掉
    urls.pop()

    #取得文章的內文
    article = dom('#main-content').remove('*').text()

    #po文時間，文章內容，網址們
    webDetailDict = {
                        'postDate'  :   postDate,
                        'article'   :   article,
                        'urls'      :   urls
                    }

    return webDetailDict

#取得每頁文章標題列的內容
def getWebData(targetContent):
    try:
        nrec = targetContent('.nrec').children().text()
        mmddDate = targetContent('.date').text()
        html = mainUrl + targetContent('.title').children().attr('href')
        title = targetContent('.title').children().text()
        author = targetContent('.author').text()

        #推數、月日時間、連結網址、標題、作者
        webDict =   {
                              'nrec'    :   nrec,
                              'mmddDate':   mmddDate,
                              'articleUrl'    :   html,
                              'title'   :   title,
                              'authorId'  :   author
                    }
    except:
        return None
    else:
        return webDict

def insertDataToDb(pttDatas):
    print('準備新增資料')
    checkDbExist()
    try:
        conn = sqlite3.connect(dbName)
        cur = conn.cursor()
        print('DB連線建立中')
        for pttData in pttDatas:
            print('爬尋資料中')
            print(pttData)
            sql =   """
                        insert into articleData (boardName,articleCode,articleUrl,title,authorId,article,nrec)
                        values('%(boardName)s','%(articleCode)s','%(articleUrl)s','%(title)s','%(authorId)s','%(article)s','%(nrec)s');
                    """ % pttData
            print(sql)
            cur.execute(sql)
        conn.commit()
    except :
        print('糟糕 sql 指令出了些問題')
        conn.rollback()
    finally:
        conn.close()

#確認db檔是否存在，若不存在則創db
def checkDbExist():
    if os.path.exists(dbName) is False:
        print('DB不存在,即將建立DB')
        createDb()
    else:
        print('DB存在')

def createDb():
    #print(create_table.sql)
    f = open('ptt.db','w')
    f.close()
    s = open('create_table.json')
    sql = json.load(s)
    s.close()
    conn = sqlite3.connect(dbName)
    cur = conn.cursor()
    cur.execute(sql['articleData'])
    cur.execute(sql['pushData'])
    conn.commit()
    conn.close()
    print('DB建立完畢')

if __name__ == "__main__":
    targetBoard = 'Beauty'
    targetDate = '20170618'
    targetFolder = '~/Download/ptt_data/test_folder'
#    checkDbExist()
    startDownloadData(targetBoard,targetDate,targetFolder)
#    startDownloadImage()

    
















