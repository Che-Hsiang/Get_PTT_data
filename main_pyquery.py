# -*- coding: UTF-8 -*-
import sys,os
import re
import urllib
import time
import calendar
import sqlite3
import datetime
from pyquery import PyQuery as pq
from random import randint
main_url = 'https://www.ptt.cc'
db_name = 'test.db'

def startDownloadData(targetBoard,targetDate,targetFolder):
    targetUrl = 'https://www.ptt.cc/bbs/' + targetBoard + '/index.html'
    dom = pq(url=targetUrl,cookies={'over18' : '1'})
    contents = dom('.r-list-container').children('.r-list-sep').prev_all('.r-ent')
    for content in contents.items():
        webData = getWebData(content)
        if webData is None:
            print('此文已被刪除,繼續爬下一篇')
        else:
            webDetailDataHtml = webData['html']
            print('title : %s' % webData['title'])
            print(webDetailDataHtml)
            webDetailData = getWebDetailData(webDetailDataHtml)
            print(webDetailData)
            time_num = randint(1,3)
            print('time_num : %d' % time_num)
            time.sleep(time_num)
        

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

    webDetailDict = {
                        'postDate'  :   postDate,
                        'article'   :   article,
                        'urls'      :   urls
                    }

    return webDetailDict

#取得每則po文標題列的內容
def getWebData(targetContent):
    try:
        nrec = targetContent('.nrec').children().text()
        mmddDate = targetContent('.date').text()
        html = main_url + targetContent('.title').children().attr('href')
        title = targetContent('.title').children().text()
        author = targetContent('.author').text()
        webDict =   {
                              'nrec'    :   nrec,
                              'mmddDate':   mmddDate,
                              'html'    :   html,
                              'title'   :   title,
                              'author'  :   author
                    }
    except:
        return None
    else:
        return webDict

if __name__ == "__main__":
    targetBoard = 'Beauty'
    targetDate = '20170618'
    targetFolder = '~/Download/ptt_data/test_folder'
    startDownloadData(targetBoard,targetDate,targetFolder)
#    startDownloadImage()

    
















