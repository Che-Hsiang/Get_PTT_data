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
from pyquery import PyQuery as pq
from random import randint

mainUrl = 'https://www.ptt.cc'
dbName = 'ptt.db'

def startDownloadData(targetBoard,targetUrl,targetDate,targetFolder):
    print('開始爬文章')
    print('1')
    dom = pq(url=targetUrl,cookies={'over18' : '1'})
    print('2')
    if targetUrl[-10:] == 'index.html':
        contents = dom('.r-list-container').children('.r-list-sep').prev_all('.r-ent')
    else:
        contents = dom('.r-list-container').children('.r-ent')
    print('3')
    pttDatas = []
    print('4')
    #上一頁
    prePage = mainUrl + dom('.wide').eq(1).attr('href')
    print(prePage)
    print('5')
    targetDateLen =  len(targetDate)
    print('6')
    dateList = []
    print('7')
    for content in contents.items():
        webData = getWebData(content)
        if webData is None:
            print('此文已被刪除,繼續爬下一篇')
        else:
            webDetailDataHtml = webData['articleUrl']
            print('準備爬取 %s 文章' % webDetailDataHtml)
            #文章代碼
            articleCode = webDetailDataHtml.strip('.html').strip(targetUrlHead)
            webData['articleCode'] = articleCode
            webData['boardName'] = targetBoard
            webData['postVersion'] = getPostVersion(webData['articleCode'])

            webDetailData = getWebDetailData(webDetailDataHtml)

            yymmddDate = webDetailData['postDate'][:10]

            dateList.append(yymmddDate[:targetDateLen])
            
            webDetailPushData = getWebDetailPushData(webDetailDataHtml,yymmddDate)

            pttData = {}
            pttData = webData.copy()
            pttData.update(webDetailData)
            pttData.update(webDetailPushData)
            pttDatas.append(pttData)

            insertArticleDataToDb(pttData,articleCode)
            insertPushDataToDb(pttData,articleCode)
            insertUrlDataToDb(pttData,articleCode)
        timeNum = randint(1,5)
        print('倒數 %s 秒後開始' % timeNum)
        time.sleep(timeNum)
      
    oldDate = dateList[0]
    newDate = dateList[len(dateList)-1]

    if targetDate > oldDate:
        print('結束爬文')
    else:
        print('準備爬上一頁')
        startDownloadData(targetBoard,prePage,targetDate,targetFolder)


#取得文章版本
def getPostVersion(articleCode):
    try:
        conn = sqlite3.connect(dbName)
        cur = conn.cursor()
        print('DB連線建立中')
        sql =   """
                        select ad.articleCode,max(postVersion) as maxVersion
                        from articleData as ad
                        where ad.articleCode = '%s'
                        group by ad.articleCode
                """ % articleCode
        cur.execute(sql)
        print('準備取得文章版本')
        res = cur.fetchone()
        print('文章版本已取得')
        if res is None:
            return '0'
        else:
            return res[1] + 1
    except:
        return None
    finally:
        conn.close()

#取得文章推文內容
#去除 ' 單引號，用@代替
def getWebDetailPushData(webDetailDataHtml,yymmddDate):
    dom = pq(url=webDetailDataHtml,cookies={'over18' : '1'})
    pushDatas = dom('.push')
    pushDataList = []
    count = 0
    for pushData in pushDatas.items():
        count = count + 1
        pushDataDict = {}
        pushDataDict['pushNo'] = count
        pushDataDict['pushTag'] = pushData('.push-tag').text()
        pushDataDict['pushId'] = pushData('.push-userid').text()
        pushDataDict['pushText'] = pushData('.push-content').text().replace("'",'@')
        pushDataDict['pushDate'] = yymmddDate + ' ' + pushData('.push-ipdatetime').text()[-5:]
        pushDataList.append(pushDataDict)

    pushDataDicts = {}
    pushDataDicts['webDetailPushData']= pushDataList

    return pushDataDicts


#取得文章的內容與內容網址
#去除 ' 單引號，用@代替
def getWebDetailData(webDetailDataHtml):
    dom = pq(url=webDetailDataHtml,cookies={'over18' : '1'})

    #取得po文時間
    postDate = timeFormatTransfer(dom('.article-meta-value').eq(3).text())

    getDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    #取得文章內的網址
    webUrls = dom('#main-content').remove('.richcontent').find('a')
    urls = []
    for webUrl in webUrls.items():
        urls.append(webUrl.attr('href'))
    #將最後本文的網址去掉
    urls.pop()

    #取得文章的內文
    article = dom('#main-content').remove('*').text().replace("'",'@')

    article = article.replace('\n','<br>')

    #po文時間，文章內容，網址們
    webDetailDict = {
                        'postDate'          :   postDate,
                        'articleContent'    :   article,
                        'urls'              :   urls,
                        'getDate'           :   getDate
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

        nrec = nrec.strip(' ')

        if nrec == '爆':
            nrec = 99
        elif nrec == '':
            nrec = 0
        elif nrec.find('X') > 0:
            nrec = int(nrec.strip('X'))
            nrec = nrec - 2 * nrec

        #推數、月日時間、連結網址、標題、作者
        webDict =   {
                              'articleNrec'    :   nrec,
                              'mmddDate':   mmddDate,
                              'articleUrl'    :   html,
                              'articleTitle'   :   title,
                              'authorId'  :   author
                    }
    except:
        return None
    else:
        return webDict

#新增文章資料至db
def insertArticleDataToDb(pttData,articleCode):
    try:
        conn = sqlite3.connect(dbName)
        cur = conn.cursor()
        print('DB連線建立中')

        print('準備新增文章資料')
#        print(pttData)

        articleDataSql =    """insert into articleData (boardName,articleCode,articleUrl,articleTitle,authorId,articleContent,articleNrec,postVersion,postDate,getDate)
                                select '%(boardName)s','%(articleCode)s','%(articleUrl)s','%(articleTitle)s','%(authorId)s','%(articleContent)s','%(articleNrec)s','%(postVersion)s','%(postDate)s','%(getDate)s'
                                where not exists
                                (select 1 
                                from articleData 
                                where boardName = '%(boardName)s'
                                and articleCode = '%(articleCode)s'
                                and articleTitle = '%(articleTitle)s'
                                and articleContent = '%(articleContent)s'
                                and articleNrec = '%(articleNrec)s'
                                );
                            """ % pttData

        cur.execute(articleDataSql)

        checkArticleRes =  cur.rowcount

        if checkArticleRes > 0:
            print('文章資料新增完畢')
        else:
            print('文章資料已存在，故跳過新增此文章')

        conn.commit()
    except Exception as e:
        print(e)
        print('###########################糟糕 sql 指令出了些問題##############################')
        conn.rollback()
    finally:
        conn.close()

#新增推文資料到DB
def insertPushDataToDb(pttData,articleCode):
    try:

        conn = sqlite3.connect(dbName)
        cur = conn.cursor()
        print('DB連線建立中')

        print('準備新增推文資料')
        for pushData in pttData['webDetailPushData']:
            pushData['articleCode'] = articleCode
            pushDataSql =   """insert into pushData (articleCode,pushNo,pushId,pushText,pushTag,pushDate)
                               select '%(articleCode)s','%(pushNo)s','%(pushId)s','%(pushText)s','%(pushTag)s','%(pushDate)s'
                               where not exists
                               (select 1
                               from pushData
                               where articleCode = '%(articleCode)s'
                               and pushNo = '%(pushNo)s'
                               and pushId = '%(pushId)s'
                               and pushText = '%(pushText)s'
                               and pushTag = '%(pushTag)s'
                               and pushDate = '%(pushDate)s'
                               );
                            """ % pushData

            cur.execute(pushDataSql)

            checkPushRes = cur.rowcount

            if checkPushRes > 0:
                print('第 %s 推文資料新增成功' % pushData['pushNo'])
            else:
                print('第 %s 推文資料已存在，故跳過此推文' % pushData['pushNo'])

        print('推文資料新增完畢')

        conn.commit()
    except Exception as e:
        print(e)
        print('###########################糟糕 sql 指令出了些問題##############################')
        conn.rollback()
    finally:
        conn.close()

#新增url資料到DB
def insertUrlDataToDb(pttData,articleCode):

    try:

        conn = sqlite3.connect(dbName)
        cur = conn.cursor()
        print('DB連線建立中')

        print('準備新增url資料')
        for urlData in pttData['urls']:
            urlDataSql =    """insert into urlData (articleCode,urlLink,urlOwnerId)
                               select '%(articleCode)s','%(urlLink)s','%(urlOwnerId)s'
                               where not exists
                               (select 1
                               from urlData
                               where articleCode = '%(articleCode)s'
                               and urlLink = '%(urlLink)s'
                               and urlOwnerId = '%(urlOwnerId)s'
                               );
                            """ % ({'articleCode':articleCode,'urlLink':urlData,'urlOwnerId':pttData['authorId']})
            cur.execute(urlDataSql)

            checkUrlRes = cur.rowcount

            if checkUrlRes > 0:
                print('url: %s 新增成功' % urlData)
            else:
                print('url: %s 已存在，故跳過此url' % urlData)

        print('url資料新增完畢')

        conn.commit()
    except Exception as e:
        print(e)
        print('###########################糟糕 sql 指令出了些問題##############################')
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
    cur.execute(sql['urlData'])
    conn.commit()
    conn.close()
    print('DB建立完畢')

def timeFormatTransfer(oriTime):

    datatimeFormat = "%a %b %d %H:%M:%S %Y"
    oriTimeStr = time.strptime(oriTime,datatimeFormat)
    newTimeStr = time.strftime("%Y-%m-%d %H:%M:%S", oriTimeStr) 

    return newTimeStr

def help():
    print('===========================================================')
    print('python3 main_pyquery.py targetBoard targetDate targetFolder')
    print(''
    print('格式:')
    print('    targetBoard  = MAC or Beauty')
    print('    targetDate   = 2017-07-01 or 2017-07 or 2017')
    print('    targetFolder = ~/Download')
    print('說明:')
    print('    targetDate : 2017-07-01  = 2017-01-01 ~ 現在')
    print('    targetDate : 2017-07     = 2017-07    ~ 現在')
    print('    targetDate : 2017        = 2017       ~ 現在')
    print('===========================================================')

                 

if __name__ == "__main__":

    if len(sys.argv) == 4 and  sys.argv[1] is not None and sys.argv[2] is not None and sys.argv[3] is not None:
        checkDbExist()
        targetUrlHead = 'https://www.ptt.cc/bbs/' + sys.argv[1] + '/'
        targetUrl = 'https://www.ptt.cc/bbs/' + sys.argv[1] + '/index.html'
        startDownloadData(sys.argv[1],targetUrl,sys.argv[2],sys.argv[3])
    else:
        help()

    
















