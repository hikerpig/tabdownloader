#-*- coding: utf-8 -*-
#!/usr/bin/env python
from PIL import Image
import os
#import ipdb


ALLOW_EXT = [
    'gif',
    'png',
    ]

OUTPUT_DIR = 'output'

def main():
    """
    把从虫虫钢琴网上下下来的gif转成背景白色的可以看的图片
    """

    raw_names = os.listdir('.')
    #print raw_names
    names = []
    if not os.path.isdir(OUTPUT_DIR):
      os.mkdir(OUTPUT_DIR)

    for name in raw_names:
      for ext in ALLOW_EXT:
        if name.find(ext) > -1:
          names.append(name)
          break


    for name in names:
      #cwd = os.getcwd()
      #name = os.path.join(cwd, 'input', name)
      #ipdb.set_trace()
      img = Image.open(name)
      img2 = Image.new('RGBA', img.size, (255, 255, 255))
      img2.paste(img, img2)
      fmt = 'gif'
      for ext in ALLOW_EXT:
        if name.find(ext) > -1:
          fmt = ext
          break
      img2.save('%s/%s'%(OUTPUT_DIR, name), fmt)

if __name__ == '__main__':
  main()

