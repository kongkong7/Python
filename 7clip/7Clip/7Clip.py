#-*- coding:utf-8 -*-

import win32api
import win32con
import win32gui
import win32ui
import win32clipboard


# from ftplib import FTP_TLS
from ftplib import FTP
import sys
import os.path

from xml.etree.ElementTree import ElementTree, Element, SubElement, parse
from datetime import datetime

import threading
import struct
import pythoncom

class Singleton(object): 
    _instance = None
    def __new__(cls, *args, **kwargs): 
        if not cls._instance: 
            cls._instance = super(Singleton, cls).__new__( 
                                cls, *args, **kwargs) 
        return cls._instance

    def get_instance(self):
        return self._instance 

class ConfigMgr(Singleton): 
    configfile = ''
    historyfile = ''
    bitmapfile = ''
    downloaddir = ''

    ip = ''
    port = 0
    id = ''
    pwd = ''
  
    def __init__(self): 
        self.configfile = 'config.xml'
        configFile = open(self.configfile, 'rb')

        tree = parse(configFile)
        confg = tree.getroot()        

        self.historyfile = confg.find("HistoryFile").text
        self.bitmapfile = confg.find("BitmapFile").text
        self.downloaddir = confg.find("DownloadDir").text

        self.ip = confg.find("IP").text
        self.port = int(confg.find("Port").text)
        self.id = confg.find("ID").text
        self.pwd = confg.find("Pass").text

    def get_configfile(self):
        return self.configfile
    def get_historyfile(self):
        return self.historyfile
    def get_bitmapfile(self):
        return self.bitmapfile
    def get_downloaddir(self):
        return self.downloaddir
    def get_ip(self):
        return self.ip
    def get_port(self):
        return self.port
    def get_id(self):
        return self.id
    def get_pwd(self):
        return self.pwd

class wFTP(Singleton):
    ftps = None

    def __init__(self):
        config = ConfigMgr()
        self.ip = config.get_ip()
        self.port = config.get_port()
        self.id = config.get_id()
        self.pwd = config.get_pwd()

        self.historyfile = config.get_historyfile()
        self.downloaddir = config.get_downloaddir()

    def connect(self):
        try:
            self.ftps = FTP()
            self.ftps.connect(self.ip, self.port)
            self.ftps.login(self.id, self.pwd)
            print(self.ftps.getwelcome())

            # 추후 옵션값으로 변경(없으면 생성)
            self.ftps.cwd("/Clipboard")
            return True
        except:
            self.ftps.close()
            return False

    def upload(self):
        try:
            historyFile = open(self.historyfile, 'rb')
            print('ftp opened')

            # xml 파싱
            tree = parse(historyFile)
            clip = tree.getroot()
            type = clip.find("type")

            if type.text == "file":
                datas = clip.findall("data")
                i = 1

                for data in datas:
                    datafile = open(data.text, 'rb')
                    self.ftps.storbinary('STOR ' + os.path.basename(data.text).encode('cp949'), datafile)    
                    print('ftp #%d file upload' % i)
                    i += 1
            elif type.text == "bitmap":
                data = clip.find("data")
                datafile = open(data.text, 'rb')
                self.ftps.storbinary('STOR ' + os.path.basename(data.text).encode('cp949'), datafile)    
                print('ftp bitmap file upload')
            else:
                pass

            self.ftps.storbinary('STOR ' + self.historyfile, open(self.historyfile, 'rb'))
            print('ftp history file upload')
        except:
            self.ftps.close()
        finally:
            historyFile.close()
            print('Upload!!!')

    def download(self):
        try:        
            historyFile = open(self.historyfile, 'wb')
            print('ftp opened')
        
            self.ftps.retrbinary('RETR ' + self.historyfile, historyFile.write)
            historyFile.close()
        
            print('ftp history file download')
        
            DownDir = os.getcwd() + self.downloaddir
            if os.path.exists(DownDir) is False:
                os.mkdir(DownDir)
        
            historyFile = open(self.historyfile, 'rb')
            # xml 파싱
            tree = parse(historyFile)
            clip = tree.getroot()
            type = clip.find("type")

            if type.text == "file":
                datas = clip.findall("data")
                i = 1
                for data in datas:
                    dataFile = open(DownDir + os.path.basename(data.text), 'wb').write
                    self.ftps.retrbinary('RETR ' + os.path.basename(data.text).encode('cp949'), dataFile)
                    print('ftp #%d file download' % i)
                    i += 1
            elif type.text == "bitmap":
                data = clip.find("data")
                dataFile = open(DownDir + os.path.basename(data.text), 'wb').write
                self.ftps.retrbinary('RETR ' + os.path.basename(data.text).encode('cp949'), dataFile)
                print('ftp bitmap file download')
            else:
                pass
        except:
            self.ftps.close()
        finally:
            historyFile.close()
            print('Download!!!')
    def clear(self):
        try:
            #디렉토리 삭제
            #dirlist=[]
            #self.ftps.dir('-d','*/',lambda L:dirlist.append(L.split()[-1]))
            #for dir in dirlist:
            #    print(dir)
            #    self.ftps.rmd(dir)
            filelist = self.ftps.nlst()

            for file in filelist:
                print(file)
                self.ftps.delete(file)
        except:
            self.ftps.close()
        finally:
            print('Clear!!!')

class wClip():
    historyfile = ''
    bitmapfile = ''
    downloaddir = ''

    def __init__(self):
        config = ConfigMgr()
        self.historyfile = config.get_historyfile()
        self.bitmapfile = config.get_bitmapfile()
        self.downloaddir = config.get_downloaddir()

        win32clipboard.OpenClipboard()

    def save_clipboard(self):
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
            self.save_text()
        elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
            self.save_file()
        elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_BITMAP):
            self.save_bitmap()
        else:
            print("Error")

    def save_xml(self, type, data):
        clip = Element("clip", encoding = "utf-8")
        clip.attrib["date"] = datetime.now().isoformat()

        SubElement(clip, "type").text = type
        if type == "file":
            for file in data:
                SubElement(clip, "data").text = file
        else:
            SubElement(clip, "data").text = data.decode('euc-kr')

        ElementTree(clip).write(self.historyfile)

    def save_text(self):
        clipData = win32clipboard.GetClipboardData(win32con.CF_TEXT)
        self.save_xml("text", clipData)

    def save_file(self):
        clipData = win32clipboard.GetClipboardData(win32con.CF_HDROP)
        self.save_xml("file", clipData)

    def save_bitmap(self):
        clipData = win32clipboard.GetClipboardData(win32con.CF_BITMAP)

        bmpInfo = win32gui.GetObject(clipData)

        dcDC = win32gui.CreateCompatibleDC(None)
        win32gui.SelectObject(dcDC, clipData)

        win32clipboard.CloseClipboard()

        mfcDC = win32ui.CreateDCFromHandle(dcDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, bmpInfo.bmWidth, bmpInfo.bmHeight)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (bmpInfo.bmWidth, bmpInfo.bmHeight), mfcDC, (0, 0), win32con.SRCCOPY)

        saveBitMap.SaveBitmapFile(mfcDC, self.bitmapfile)
    
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
    
        self.save_xml("bitmap", self.bitmapfile)

    def set_clipboard(self):
        try:
            historyFile = open(self.historyfile, 'rb')

            # xml 파싱
            tree = parse(historyFile)
            clip = tree.getroot()
            type = clip.find("type")

            win32clipboard.EmptyClipboard()
        
            if type.text == "text":
                data = clip.find("data")
                win32clipboard.SetClipboardData(win32con.CF_TEXT, data.text.encode('euc-kr'))
            elif type.text == "file":
                datas = clip.findall("data")
                files = ''
                for data in datas:
                    files += (os.getcwd() + self.downloaddir + os.path.basename(data.text) + '\0').encode('euc-kr')

                stg = pythoncom.STGMEDIUM()
                format = 'lllll{0}s'.format(len(files))
                pack = struct.pack(format, 20, 0, 0, 0, 0, files)
                stg.set(pythoncom.TYMED_HGLOBAL, pack)

                win32clipboard.SetClipboardData(win32con.CF_HDROP, stg.data)
            elif type.text == "bitmap":
                data = clip.find("data")
            
                bitmap = None
                flags = win32con.LR_DEFAULTSIZE | win32con.LR_LOADFROMFILE
                filename = (os.getcwd() + self.downloaddir + os.path.basename(data.text)).encode('euc-kr')
                bitmap = win32gui.LoadImage(0, filename, win32con.IMAGE_BITMAP, 0, 0, flags)
        
                win32clipboard.SetClipboardData(win32con.CF_BITMAP, bitmap)
            else:
                pass
        finally:
            win32clipboard.CloseClipboard()
            historyFile.close()

    def replace_text(self):
        clipData = win32clipboard.GetClipboardData(win32con.CF_TEXT)
        win32clipboard.EmptyClipboard()
        clipData = clipData.replace('\r\n', ', ')
        win32clipboard.SetClipboardData(win32con.CF_TEXT, clipData)

if __name__=='__main__':
    wclip = wClip()
    
    if sys.argv[1] == 're':
        wclip.replace_text()
    else:
        wftp = wFTP()
        if True == wftp.connect():
            if sys.argv[1] == 'up':
                wclip.save_clipboard()
                wftp.upload()
            elif sys.argv[1] == 'down':
                wftp.download() 
                wclip.set_clipboard()
            elif sys.argv[1] == 'clear':
                wftp.clear()
            else:
                print('Invalid command')
        else:
            print('Cat not connect FTP server!!!')