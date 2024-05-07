#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import cv2
import pytesseract
from glob import glob
import re
import string
import warnings
warnings.filterwarnings('ignore')


def cleanText(txt):
    whitespace = string.whitespace
    punctuation = "!#$%&\'()*+:;<=>?[\\]^`{|}~"
    tableWhitespace = str.maketrans('', '', whitespace)
    tablePunctuation = str.maketrans('', '', punctuation)
    text = str(txt)
    removewhitespace = text.translate(tableWhitespace)
    removepunctuation = removewhitespace.translate(tablePunctuation)
    return str(removepunctuation)


def getPredictions(image):
    # extract data using Pytesseract
    custom_config = r'-l kor --oem 1 --psm 6'
    tessData = pytesseract.image_to_data(image, config=custom_config)
    # convert into dataframe
    tessList = list(map(lambda x: x.split('\t'), tessData.split('\n')))
    df = pd.DataFrame(tessList[1:], columns=tessList[0])
    df.dropna(inplace=True)  # drop missing values
    df['text'] = df['text'].apply(cleanText)

    # filter out empty text rows
    df_clean = df.query('text != ""')

    # convert dtype for bounding box calculations
    df_clean[['left', 'top', 'width', 'height']] = df_clean[['left', 'top', 'width', 'height']].astype(int)

    # draw bounding box and put text
    img_bb = image.copy()
    for index, row in df_clean.iterrows():
        l, t, w, h = row['left'], row['top'], row['width'], row['height']
        r, b = l + w, t + h
        cv2.rectangle(img_bb, (l, t), (r, b), (0, 255, 0), 2)
        cv2.putText(img_bb, row['text'], (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

    return img_bb

