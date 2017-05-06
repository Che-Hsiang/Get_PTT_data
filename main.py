import requests
import sys,os
import re
from bs4 import BeautifulSoup
import urllib

main_url = 'https://www.ptt.cc'

def save(img_urls, title):
    if img_urls:
        try:
            dname = title.strip()  # 用 strip() 去除字串前後的空白
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
    soup = BeautifulSoup(dom, 'html.parser')

    articles = []  # 儲存取得的文章資料
    divs = soup.find_all('div', 'r-ent')
    for d in divs:
        if d.find('div', 'date').string.strip(' ') == date:  # 發文日期正確
            # 取得推文數
            push_count = 0
            if d.find('div', 'nrec').string:
                try:
                    #print(d.find('div', 'nrec').string)
                    if d.find('div', 'nrec').string == '爆':
                        push_count = 100
                    else:
                        push_count = int(d.find('div', 'nrec').string)  # 轉換字串為數字
                except ValueError:  # 若轉換失敗，不做任何事，push_count 保持為 0
                    pass

            # 取得文章連結及標題         
            if d.find('a'):  # 有超連結，表示文章存在，未被刪除
                href = main_url + d.find('a')['href']
                title = d.find('a').string
                articles.append({
                    'title': title,
                    'href': href,
                    'push_count': push_count
                })
    return articles

def start_download(url):
    pages = get_web_page(url)

    pages_res = get_articles(pages,'5/06')
    print(len(pages_res))
    if len(pages_res) != 0:
        for page_res in pages_res:
            page = get_web_page(page_res['href'])
            img_urls = parse(page)
            print("title_download_begin : %s" % page_res['title'])
            save(img_urls,page_res['title'])
            print("title_download_end   : %s" % page_res['title'])
        previous_page_url = get_previous_page_url(url)
        start_download(previous_page_url)

def get_previous_page_url(url):
    pages = get_web_page(url)
    soup = BeautifulSoup(pages,'html.parser')

    return main_url + soup.find(text='‹ 上頁').find_previous()['href']

if __name__ == "__main__":
    url = 'https://www.ptt.cc/bbs/Beauty/index.html'
    
    start_download(url)

    print("test")
    #previous_page_url = get_previous_page_url(url)

    #print(previous_page_url)

    
















