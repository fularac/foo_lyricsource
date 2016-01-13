#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from robobrowser import RoboBrowser
import argparse
from bs4 import element
import io
import logging

'''
スクレイピングのための基底クラス
'''
class scraper_base:

    '''
    beautifulsoupのnodeを指定してそのタグ以下の内容をテキストで返す
    buf    StringIO:テキストを戻すためのバッファ
    '''
    def get_text(self,node,buf):
        if isinstance(node,element.Tag):
            if node.name == "br":
                buf.write("\n")
            for e in node.contents:
                self.get_text(e,buf)
        if isinstance(node,element.NavigableString):
            t = re.sub(r'[\n\xa0]','',node.string)
            buf.write(t)

'''
www.lyrics.azからlyricを取得
'''
class www_lyrics_az(scraper_base):
    def __init__(self,artist,song):
        self.artist = self.remove_unwanted_chars(artist)
        self.song = self.remove_unwanted_chars(song)
        
    def remove_unwanted_chars(self,s):
        s=re.sub('\(.*\)','',s) #(・・・)
        s=re.sub('\[.*\]','',s) #[・・・]
        s= re.sub('[^A-Za-z0-9 \']+',' ',s) #許可する文字:英数字、半角スペース、"'"
        s=s.strip() #前後の空白を除く
        return s
    
    def test_tag(self,tag):
        if tag.name !='a':
            return False
        buf = io.StringIO()
        self.get_text(tag, buf)
        if re.match(r'^%s$' % self.song,buf.getvalue(),re.IGNORECASE) is None:
            return False       
        return True
    
    def get_lyric(self):
        
        browser = RoboBrowser(parser="html.parser",history=True)
        browser.open('https://www.lyrics.az/')
        
        #search artist
        form = browser.get_form(action='/')
        form['keyword'].value = self.artist
        browser.submit_form(form)
        
        #click artist
        node = browser.find('a',text=re.compile(r'^%s$' % self.artist,re.IGNORECASE))
        if node is None:
            logging.warn("artist not found.artist:[%s]song:[%s]" % (self.artist,self.song))
            return ""
        browser.follow_link(node)
        
        #click "View All Songs"
        node = browser.find('a',text=re.compile(r'View All songs'))
        if node is None:
            logging.warn("[View All Songs]link not found.artist:[%s]song:[%s]" % (self.artist,self.song))
            return ""
        browser.follow_link(node)
        
        #find song
        node = browser.find(lambda tag:self.test_tag(tag))
        if node is None:
            logging.warn("song not found.artist:[%s]song:[%s]" % (self.artist,self.song))
            return ""
        browser.follow_link(node)
        
        lyrics = browser.find_all('span',id="lyrics")
        if lyrics is None or len(lyrics)==0:
            logging.warn("lyric not found.artist:[%s]song:[%s]" % (self.artist,self.song))
            return ""
        buf = io.StringIO()
        self.get_text(lyrics[0],buf)
        lyric = buf.getvalue()
        if lyric.startswith("We haven't lyrics of this song."):
            logging.warn("lyric not found.artist:[%s]song:[%s]" % (self.artist,self.song))
            return ""
        lyric=lyric.replace("´", "'")   #dllに返せない？文字を除く
        return lyric

if __name__ == '__main__':
    #引数
    parser = argparse.ArgumentParser()
    parser.add_argument('--artist')
    parser.add_argument('--song')
    
    args=parser.parse_args()
    logging.basicConfig(filename='get_lyric.log',level=logging.WARN,filemode = "w")
    
    obj = www_lyrics_az(args.artist,args.song) 
    
    lyric=""
    try:
        lyric=obj.get_lyric()
    except Exception as e:
        logging.error("artist:[%s]song:[%s]error:[%s]" % (obj.artist,obj.song,e))
    if len(lyric)>0:
        print(lyric,end="")
