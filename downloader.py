#-*- coding: utf-8 -*-
import requests
import lxml.etree as etree
import argparse
import sys, os
import urlparse
#import termcolor
import ipdb
import shutil
import re

###########
#  Utils  #
###########

class NotFoundError(Exception):
    "404 Error"
    def __init__(self, url):
        self.url = url
    def __str__(self):
      return repr(self.url)


#################
#  Downloaders  #
#################

# Used for downloading multiple urls' tab
# TODO: different site, different xpath rules
class TabDownloader:
    urls=[]
    start_index = 1
    data_dir = 'data'
    tmp_dir = 'tmp'
    imgurl_pattern = '\d+.(?P<ext>png|gif)'

    def __init__(self, urls):
        if type(urls) == str:
            urls = [urls]
        self.urls = urls

    def start_download(self):
        if len(self.urls):
          if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)
          if not os.path.isdir(self.data_dir):
            os.mkdir(self.data_dir)

        for url in self.urls:
            htmlFilename = url.split('/').pop()
            htmlFilepath = os.path.join(self.tmp_dir, htmlFilename)
            if os.path.isfile(htmlFilepath):
              f = open(htmlFilepath)
              content = ''.join(f.readlines())
              f.close()
            else:
              print "Requesting for ", url
              response = requests.get(url)
              content = response.content
              f = open(htmlFilepath, 'w')
              f.writelines(content)
              f.close()

            ht = etree.HTML(content)

            keywordEle = ht.xpath("//meta[@name='keywords']").pop()
            keywords = keywordEle.get('content')
            tabname = keywords.split(',')[0]
            print "tabname is", tabname

            imgEle = ht.xpath("//div[@id='upid']/img")
            if not len(imgEle):
                print "Error: there is no tab image in this page"
                exit()
            imgEle = imgEle.pop()
            src = imgEle.get('src')

            urlTupples = urlparse.urlparse(url)
            scheme = urlTupples.scheme
            hostname = urlTupples.hostname
            imgUrl = urlparse.urljoin(scheme + '://' + hostname, src)

            hasMore = True
            index = self.start_index
            try:
              while hasMore:
                # -----------
                m = re.search(self.imgurl_pattern, imgUrl)
                if not m:
                  hasMore = False
                  break
                ext = m.group('ext')
                match_str = m.group()
                _url = imgUrl.replace(match_str, str(index)+'.'+ext)
                print "Downloading image: ", _url
                # TODO: gevent ?
                # TODO: 可以循环推出全部图片的url, 用正则?
                img_downloader = ImageDownloader(_url)
                img_downloader.tabname = tabname
                img_downloader.data_dir = self.data_dir
                img_downloader.download()
                index += 1
            except NotFoundError as err:
              print "Not found file", err
              print "Download ended"

    def options(self):
        options = {}
        for attr in ['start_index', 'data_dir', 'urls']:
            options[attr] = getattr(self, attr)
        return options


class ImageDownloader:
    url=''
    data_dir = 'data'
    tabname = 'tab'

    def __init__(self, url):
        self.url = url

    def download(self):
        name = self.url.split('/')[-1]

        name_to_save = self.tabname + '_' + name
        filename = os.path.join(self.data_dir, name_to_save)
        if os.path.isfile(filename):
            print "File: ", name_to_save, " already exists"
            return

        response = requests.get(self.url, stream=True)
        if not response.ok:
            if response.status_code == 404:
                raise NotFoundError(self.url)


        print "Saving file ", filename
        with open(filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

        del response

    def options(self):
        options = {}
        for attr in ['tabname', 'data_dir', 'urls']:
            options[attr] = getattr(self, attr)
        return options


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Tab pics converter for ChongChong Music")
    parser.add_argument('-d', dest="data_dir", default='input',
            help='Directory to store downloaded files')
    parser.add_argument('-t', dest="temp_dir", default='tmp',
            help="Directory to store temp files. default to 'tmp'")
    if len(sys.argv) < 2:
        print "Please enter at least the url"
        exit()

    argList = sys.argv[2:]
    argObj = parser.parse_args(argList)
    #print argObj
    url = sys.argv[1]
    urlTupples = urlparse.urlparse(url)

    downloader = TabDownloader(url)
    downloader.data_dir = argObj.data_dir
    downloader.start_download()

