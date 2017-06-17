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
from pyquery import PyQuery as pq
main_url = 'https://www.ptt.cc'
db_name = 'test.db'

def startDownloadData(targetBoard,targetDate,targetFolder):
    targetUrl = 'https://www.ptt.cc/bbs/' + targetBoard + '/index.html'
    dom = pq(url=targetUrl,cookies={'over18':'1'})
    contents = dom('.r-list-container').children('.r-list-sep').prev_all('.r-ent')
    for content in contents.items():
        webData = getWebData(content)
        webDetailDataHtml = webData['contentHtml']
        print(webDetailDataHtml)
        webDetailData = getWebDetailData(webDetailDataHtml)
        print(webDetailData)
        

#取得每則po文的內容
def getWebDetailData(webDetailDataHtml):
    dom = pq(url=webDetailDataHtml)
    contents = dom('.bbs-content')
    contexts = contents
    context = contexts('#main-content').remove('*').text()
    return context
#    for content in contents.items():
#        if content('div').attr('class') == 'article-metaline':
#            print(content('div').text())
#        elif content('div').attr('class') == 'push':
#            print(content('div').text())
#        else:
#        print(content('div').attr('class'))
        

#取得每則po文標題列的內容
def getWebData(targetContent):
    contentNrec = targetContent('.nrec').children().text()
    contentDate = targetContent('.date').text()
    contentHtml = main_url + targetContent('.title').children().attr('href')
    contentTitle = targetContent('.title').children().text()
    contentAuthor = targetContent('.author').text()
    contentDict = {
                          'contentNrec'   :   contentNrec,
                          'contentDate'   :   contentDate,
                          'contentHtml'   :   contentHtml,
                          'contentTitle'  :   contentTitle,
                          'contentAuthor' :   contentAuthor
                        }
    return contentDict

if __name__ == "__main__":
    targetBoard = 'stock'
    targetDate = '20170618'
    targetFolder = '~/Download/ptt_data/test_folder'
    startDownloadData(targetBoard,targetDate,targetFolder)
#    startDownloadImage()

    
















