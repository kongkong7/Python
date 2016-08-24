#-*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup
from mechanize import Browser
import re

import sys
import os
from xml.etree.ElementTree import ElementTree, Element, SubElement, parse
import json, urllib2
import shutil
from guessit import guessit
import logging

reload(sys)
sys.setdefaultencoding('utf-8')

def getunicode(soup):
    body=''
    if isinstance(soup, unicode):
        soup = soup.replace('&#39;', "'")
        soup = soup.replace('&quot;', '"')
        soup = soup.replace('&nbsp;', ' ')
        body = body + soup
    else:
        if not soup.contents:
            return ''
        con_list = soup.contents
        for con in con_list:
            body = body + getunicode(con)
    return body

def imdb_info(title):
    movie = title
    movie_search = '+'.join(movie.split())

    base_url = 'http://www.imdb.com/find?q='
    url = base_url+movie_search+'&s=all'

    title_search = re.compile('/title/tt\d+')

    br = Browser()
    #br.set_proxies({'http':'http://username:password@proxy:port', 'https':'https://username:password@proxy:port'})

    br.open(url)

    link = br.find_link(url_regex = re.compile(r'/title/tt.*'))
    res = br.follow_link(link)
    
    soup = BeautifulSoup(res.read())
    
    movie_title = getunicode(soup.find('title'))
    rate = soup.find('span', itemprop='ratingValue')
    rating = getunicode(rate)
    
    actors=[]
    actors_soup = soup.findAll('a', itemprop='actors')
    for i in range(len(actors_soup)):
        actors.append(getunicode(actors_soup[i]))
    
    des = soup.find('meta', {'name':'description'})['content']

    genre=[]
    subtext = soup.find('div', {'class':'subtext'})
    r = subtext.find('', {'title':True})['title']
    genrelist = subtext.findAll('a', {'href':True})
    
    for i in range(len(genrelist)-1):
        genre.append(getunicode(genrelist[i]))
    release_date = getunicode(genrelist[-1])

    print movie_title, rating+'/10.0'
    print 'Relase Date:', release_date
    print 'Rated', r
    print ''
    print 'Genre:',
    print ', '.join(genre)
    print '\nActors:',
    print ', '.join(actors)
    print '\nDescription:'
    print des

DAUM_MOVIE_SRCH   = "http://movie.daum.net/data/movie/search/v2/%s.json?size=20&start=1&searchText=%s"

#DAUM_MOVIE_DETAIL = "http://m.movie.daum.net/data/movie/movie_info/detail.json?movieId=%s"
#DAUM_MOVIE_CAST   = "http://m.movie.daum.net/data/movie/movie_info/cast_crew.json?pageNo=1&pageSize=100&movieId=%s"
#DAUM_MOVIE_PHOTO  = "http://m.movie.daum.net/data/movie/photo/movie/list.json?pageNo=1&pageSize=100&id=%s"

#DAUM_TV_DETAIL    = "http://m.movie.daum.net/tv/main.json?tvProgramId=%s"
#DAUM_TV_CAST      = "http://m.movie.daum.net/data/movie/tv/cast_crew.json?pageNo=1&pageSize=100&tvProgramId=%s"
#DAUM_TV_PHOTO     = "http://m.movie.daum.net/data/movie/photo/tv/list.json?pageNo=1&pageSize=100&id=%s"
#DAUM_TV_EPISODE   = "http://m.movie.daum.net/tv/episode?tvProgramId=%s"

media_ext = ('.avi', '.wmv', '.mp4', '.mpg', '.mpeg', '.mkv', '.ts')
subtitles_ext = ('.smi', '.srt')

def daum_info(pCate, pTitle, pYear):
    url = DAUM_MOVIE_SRCH % (pCate, urllib2.quote(pTitle))
    response = urllib2.urlopen(url)
    data = json.load(response)
    items = data['data']
    
    max_score = 0
    media_info = {}
    if items:
        for item in items:
            year = item['prodYear']
            title = item['titleKo']
            id = str(item['tvProgramId'] if pCate == 'tv' else item['movieId'])
            if year == pYear:
              score = 95
            elif len(items) == 1:
              score = 80
            elif (year + 1) == pYear:
              score = 50
            else:
              score = 10

            sub_category = ''
            country = ''
            if pCate == 'tv':
                sub_category = item['genres'][0]['genreName']
                country = item['countries'][0]['countryKo']

            if max_score < score:
                media_info = {'id':id, 'cate':pCate, 'title':title, 'year':year, 'score':score, 'sub_category':sub_category, 'country':country}
                max_score = score

                #print('ID=%s, media_name=%s, title=%s, year=%s, score=%d, sub_category=%s, country=%s' %(id, pTitle, title, year, score, sub_category, country))
        if max_score == 10 and pCate == 'movie':
            media_info = daum_info('tv', pTitle, pYear)
        elif max_score == 10 and pCate == 'tv':
            print u'프로그램 정보를 찾을수 없습니다.'
            return
    else:
        if pCate == 'movie':
            media_info = daum_info('tv', pTitle, pYear)
        else:
            print u'프로그램 정보를 찾을수 없습니다.'
            return

    return media_info


#1. 파일명 100%일치
#2. 제목, 시즌, 회차
def search_subtitles(pDir, pFileName):
    subtitles_path = ''
    for (path, dir, files) in os.walk(pDir):
        for file in files:
            filename = os.path.splitext(file)[0].lower()
            ext = os.path.splitext(file)[1].lower()
            if ext in subtitles_ext:
                if filename == pFileName:
                    subtitles_path = os.path.join(path, file)
    return subtitles_path.decode('euc-kr')

def copy_file(pType, pSrc, pDec):
    try:
        if pType is True:
            shutil.copy(pSrc, pDec)
            type = '복사'
        else:
            shutil.move(pSrc, pDec)
            type = '이동'

        logger.info("[%s]를 [%s]로 %s 했습니다.!" %(pSrc, pDec, type))
    except:
        logger.error("[%s]를 [%s]로 %s 실패 했습니다.!!!" %(pSrc, pDec, type))

#타이틀에 간혹 HTML tag 가 들어간것이 있어 제거
def html2text(html):
    soup = BeautifulSoup(html)
    text_parts = soup.findAll(text=True)
    return ''.join(text_parts)

if __name__ == '__main__':
    # 1. 설정파일에 지정된 디렉토리를 읽어 파일명을 파싱후 파일정보를 생성
    #   - 디렉토리 : Downz, Moviez, TV Showz, Etcz
    #
    # 2. 다음(네이버)에서 파일명, 년도로 검색 후 있으면 부가정보를 생성 및 수정
    #   - 파일명으로 영화 우선 검색 후 못찾으면 TV 프로그램 검색
    #   - 매칭 조건에 따라 등급을 정하고 미달은 기타 디렉토리로 이동 후 표시
    #
    # 3. 메타파일에서 조건에 따라 검색 후 있으면 해당 디렉토리에 이동, 없으면 디렉토리를 생성 후 이동
    #   - 파일 : 영상파일(avi, wmv, mp4, mpg, mpeg, mkv)과 자막파일(smi, srt)만 검색
    #   - 조건 : 제목, 년도
    #   - 자막 : 파일명과 동일하면 이동, 제목만 동일하면 이름변경 후 이동
    # 4. 모니터링
    #
    # 추가기능
    #   - 스케쥴 기능추가
    #   - 포스터 및 부가정보등을 다운로드 하여 메타파일 및 DB화
    #   - 음악, 만화등 다른컨텐츠도 자동화(각각 별도 프로세스 필요)
    #   - 앱에서 직접 확인 및 재생

    # 환경설정 파일 읽어오기
    configfile = open('config.xml', 'rb')

    tree = parse(configfile)
    config = tree.getroot()        

    downloaddir = config.find("DownloadDir").text

    moviezdir = config.find("MoviezDir").text
    tvshowdir = config.find("TVShowzDir").text
    etcdir = config.find("EtcDir").text

    is_category = config.find("SubCategory").text.lower() == 'true'
    is_copy = config.find("CopyType").text.lower() == 'true'

    # 로거 인스턴스를 만든다
    logger = logging.getLogger('moverLog')
    # 포매터를 만든다
    fomatter = logging.Formatter('%(asctime)s %(levelname)s\t: %(message)s')
    # 스트림과 파일로 로그를 출력하는 핸들러를 각각 만든다.
    fileHandler = logging.FileHandler('./workinfo.log')
    # 각 핸들러에 포매터를 지정한다.
    fileHandler.setFormatter(fomatter)
    # 로거 인스턴스에 스트림 핸들러와 파일핸들러를 붙인다.
    logger.addHandler(fileHandler)
    # 로거 인스턴스로 로그를 찍는다.
    logger.setLevel(logging.INFO)

    # 지정된 디렉토리에서 파일검색 후 파일명으로 기본 메타데이터 생성
    # 기본 메타데이터로 웹(다음, 네이버)에서 상세 메타데이터 생성
    # 생성된 메타데이로 지정된 디렉토리로 이동 및 추가 메타데이터 생성
    for (path, dir, files) in os.walk(downloaddir):
        for file in files:
            filename = os.path.splitext(file)[0].lower()
            if 'sample' == filename:
                pass
            ext = os.path.splitext(file)[1].lower()
            if ext in media_ext:
                try:
                    #print("%s/%s" % (path, file))
                    fileinfo = guessit(file, '-Y')
                    #print fileinfo
                    title = str(fileinfo['title'].decode('euc-kr'))
                
                    # 년도찾기 영화는 년도만 존재하며 TV는 Date로 존재한다.
                    # TV는 국내는 날짜로 외국은 시즌으로 존재한다.
                    for info in fileinfo:
                        if 'year' == info:
                            year = fileinfo[info]
                            break;
                        elif 'date' == info:
                            year = fileinfo[info].year
                            break;
                        elif 'season' == info:
                            season = fileinfo[info]
                            title = '%s %s' % (title, season)
                        else:
                            year = 0

                    media_info = daum_info('movie', title, year)

                    if media_info:
                        #move_media()
                        cate = media_info['cate']
                        title = re.sub("[\/:*?\"<>]|", "", html2text(media_info['title']))
                        year = media_info['year']
                        if 'movie' == cate:
                            work_dir =  moviezdir                       
                            media_dir = os.path.join(work_dir, title + ' (%s)' %(year))
                        elif 'tv' == cate:
                            work_dir =  tvshowdir
                            sub_category = media_info['sub_category']

                            if 0 < len(sub_category):
                                if is_category is True:
                                    work_dir = os.path.join(work_dir, sub_category)
                                    if os.path.exists(work_dir) is False:
                                        os.mkdir(work_dir)
                            media_dir = os.path.join(work_dir, title)
                    else:
                        work_dir =  etcdir
                        media_dir = os.path.join(work_dir, title.decode('utf8'))


                    if os.path.exists(work_dir) is False:
                        os.mkdir(work_dir)

                    if os.path.exists(media_dir) is False:
                        os.mkdir(media_dir)

                    media_path = os.path.join(path.decode('euc-kr'), file.decode('euc-kr'))
                    print media_path
                    sub_path = search_subtitles(downloaddir, filename)
                    print sub_path

                    #파일이 존재하는지 검사
                    if os.path.exists(os.path.join(media_dir, file.decode('euc-kr'))) is False:
                        copy_file(is_copy, media_path, media_dir)
                    if 0 < len(sub_path):
                        sub_file = os.path.basename(sub_path)
                        if os.path.exists(os.path.join(media_dir, sub_file)) is False:
                            copy_file(is_copy, sub_path, media_dir)
                except Exception as ex: 
                    print("%s : %s : %s" % (path, file, ex))
