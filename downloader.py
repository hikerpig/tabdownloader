#-*- coding: utf-8 -*-
import requests
import argparse
import sys, os
import urlparse
import ipdb
import shutil
import re
import gevent
from gevent import monkey
from gevent.pool import Pool as Pool
from BeautifulSoup import BeautifulSoup

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
    data_dir = 'data'
    tmp_dir = 'temp'

    def __init__(self, urls):
        if type(urls) == str:
            urls = [urls]
        self.urls = urls

    def parse(self, content):
      '''
      parse contents
      @return {dict}
        'tabname': {str}
        'pic_srcs': {list}
      '''
      soup = BeautifulSoup(content, fromEncoding='gb18030')
      headEle = soup.html
      titleEle = headEle.title

      if titleEle:
        title_text = titleEle.text
        tabname = title_text.split('-')[0]
      else:
        keywordEle = headEle.find(attrs={'name': re.compile("keywords$")})
        keywords = keywordEle.get('content')
        tabname = keywords.split(',')[0]
      print "tabname is", tabname

      # find script that contains the urls
      script_tags = headEle.findAll('script',language=re.compile('javascript'))
      script_content = script_tags[0].string

      # get picurls out
      picurl_pattern = re.compile('picurl\.length.*img.*\>\";[\r\n]$', re.MULTILINE | re.DOTALL)
      matched_string = picurl_pattern.search(script_content)
      if not matched_string:
        print "no matched_string"
        return
      matched_string = matched_string.group()
      lines = matched_string.split('\n')

      img_tag_lines = lines[1].split(';')[:-1]
      url_pattern = re.compile('src=.?\"(?P<img_url>.+).+\"\s\>\"')

      pic_srcs = []
      for tag_line in img_tag_lines:
          _matches = url_pattern.search(tag_line)
          if _matches:
              pic_srcs.append(_matches.group('img_url'))

      return {
          'tabname': tabname,
          'pic_srcs': pic_srcs
      }


    # TODO: 参考grequests, 应该使用requests的Session, 暂时都是unsent的状态
    #       然后再用gevent的spawn来send ?
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

            parsed_dict = self.parse(content)
            pic_srcs = parsed_dict['pic_srcs']
            tabname = parsed_dict['tabname']

            imgs_length = len(pic_srcs)

            urlTupples = urlparse.urlparse(url)
            scheme = urlTupples.scheme
            hostname = urlTupples.hostname

            # for test
            #pages_num = 0

            jobs = []
            for pic_src in pic_srcs:
                # -----------
                _url = urlparse.urljoin(scheme + '://' + hostname, pic_src)
                print "Downloading image: ", _url
                img_downloader = ImageDownloader(_url)
                img_downloader.tabname = tabname
                img_downloader.data_dir = self.data_dir
                job = gevent.spawn(img_downloader.download)
                jobs.append(job)

        return gevent.joinall(jobs)

    def options(self):
        options = {}
        for attr in ['data_dir', 'urls']:
            options[attr] = getattr(self, attr)
        return options


class ImageDownloader:
    url=''
    data_dir = 'data'
    tabname = 'tab'
    filename = 'tab_image'

    def __init__(self, url):
        self.url = url

    def download(self):
        # TODO: seperate save and parse method
        name = self.url.split('/')[-1]

        name_to_save = self.tabname + '_' + name
        filename = os.path.join(self.data_dir, name_to_save)
        self.filename = filename
        if os.path.isfile(filename):
            print "File: ", name_to_save, " already exists"
            return

        response = requests.get(self.url, stream=True)
        if not response.ok:
            if response.status_code == 404:
                del response
                raise NotFoundError(self.url)
        gevent.sleep(0)
        self.response = response
        self.save()
        del self

    def save(self):
        print "Saving file ", self.filename
        with open(self.filename, 'wb') as out_file:
            shutil.copyfileobj(self.response.raw, out_file)
        return self

    def options(self):
        options = {}
        for attr in ['tabname', 'data_dir', 'urls']:
            options[attr] = getattr(self, attr)
        return options


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Tab pics converter for ChongChong Music")
    parser.add_argument('-d', dest="data_dir", default='input',
            help='Directory to store downloaded files')
    parser.add_argument('-t', dest="temp_dir", default='temp',
            help="Directory to store temp files. default to 'temp'")
    if len(sys.argv) < 2:
        print "Please enter at least the url"
        exit()

    argList = sys.argv[2:]
    argObj = parser.parse_args(argList)
    #print argObj
    url = sys.argv[1]
    urlTupples = urlparse.urlparse(url)

    monkey.patch_dns()

    downloader = TabDownloader(url)
    downloader.data_dir = argObj.data_dir
    downloader.start_download()

