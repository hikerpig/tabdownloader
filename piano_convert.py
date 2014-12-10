#-*- coding: utf-8 -*-
#!/usr/bin/env python
from PIL import Image
import os
import argparse

ALLOW_EXT = [
  'gif',
  'png',
]

OUTPUT_DIR = 'output'

class TabConverter:
  """
  把从虫虫钢琴网上下下来的gif转成背景白色的可以看的图片
  """
  input_dir = '.'
  output_dir = 'output'

  def __init__(self, input_dir, output_dir):
    self.input_dir = input_dir
    self.ouput_dir = output_dir

  def convert(self):

    raw_names = os.listdir(self.input_dir)
    names = []
    if not os.path.isdir(self.ouput_dir):
      os.mkdir(self.ouput_dir)

    for name in raw_names:
      for ext in ALLOW_EXT:
        if name.find(ext) > -1:
          names.append(name)
          break

    for name in names:
      #cwd = os.getcwd()
      #name = os.path.join(cwd, 'input', name)

      inputName = os.path.join(self.input_dir, name)
      outputName = os.path.join(self.output_dir, name)
      print "Processing ", name

      img = Image.open(inputName)
      img2 = Image.new('RGBA', img.size, (255, 255, 255))
      img2.paste(img, img2)
      fmt = 'gif'
      for ext in ALLOW_EXT:
        if name.find(ext) > -1:
          fmt = ext
          break
      img2.save(outputName, fmt)
      print "Output is", outputName

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Tab pics converter for ChongChong Music")
  parser.add_argument('-i', dest="input_dir", default='.'
      , help="Input directory")
  parser.add_argument('-o', action="store", dest="output_dir", default='output'
      , help="Output directory")

  args = parser.parse_args()

  converter = TabConverter(args.input_dir, args.output_dir)
  converter.convert()

