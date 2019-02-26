#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 10:03:16 2019

@author: toddbilsborough

Tracks quotes and their sources and generates citations in different styles
"""

import datetime
import logging
import os
import pandas as pd
from shutil import copy

log_format_string = ("%(asctime)s - "
                     "%(levelname)s - "
                     "%(funcName)s - "
                     "%(message)s")
logging.basicConfig(level=logging.INFO, 
                    filename='log.txt', 
                    filemode='a', 
                    format=log_format_string,
                    datefmt='%y-%b-%d %H:%M:%S')

BOOK_FIELDS = {
        '1': 'Author',
        '2': 'Title',
        '3': 'Article Title',
        '4': 'Editor',
        '5': 'Translator',
        '6': 'Publisher',
        '7': 'City',
        '8': 'Year'
        }

QUOTE_FIELDS = {
        '1': 'Book',
        '2': 'Page Number',
        '3': 'Tags',
        '4': 'Text',
        '5': 'Notes'
        }

def load_books():
    """load the books database into a dataframe"""
    multiindex = ['Author', 'Title']
    try:
        books = pd.read_csv('books.csv', index_col=multiindex)
        books.sort_index(inplace=True)
    except IOError:
        print("Books file not found")
        logging.error("Books file not found")
        return None
    return books

def load_quotes():
    """load the quotes database into a dataframe"""
    try:
        quotes = pd.read_csv('quotes.csv', index_col=0)
        quotes.sort_index(inplace=True)
    except IOError:
        print("Quotes file not found")
        logging.error("Quotes file not found")
        return None
    return quotes

def backup_files():
    """Back up data files"""
    ts = datetime.datetime.today()
    day = ts.day if int(ts.day) > 9 else "0{}".format(ts.day)
    month = ts.month if int(ts.month) > 9 else "0{}".format(ts.month)
    timestamp = "_{}{}{}".format(ts.year, month, day)
    newpath = r'backups/backup{}/'.format(timestamp) 
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    print(r"Backing up data files to /backups/backup{}".format(timestamp))
    copy('books.csv', newpath)
    copy('quotes.csv', newpath)
    print("Backup completed")
    logging.info("backed up data files")

def add_book():
    """add a book to the database"""
    fields = {}
    for index, field in BOOK_FIELDS.items():
        data = input("{}: ".format(field))
        fields[field] = data
    append_frame = pd.DataFrame(data=[fields.values()],
                                      columns=BOOK_FIELDS.values())
    append_frame.set_index(keys=['Author', 'Title'], inplace=True)
    books = load_books()
    try:
        books = books.append(append_frame, verify_integrity=True)
    except ValueError:
        print("Already in books database")
        logging.error("%s already in books database", fields['Title'])
        return None
    for field, data in fields.items():
        print("{}: {}".format(field, data))
    conf = input("All correct? ").lower()
    if conf == 'q':
        return None
    if conf != 'y':
        field = input("Field to edit: ")
        try:
            fields[field] = input("{}: ".format(field))
        except KeyError:
            print("No such field")
            return None
    books.to_csv('books.csv')
    print("File saved")
    logging.info("books database saved")
    
def quotes_from_text():
    """Add quotes to database from text file"""
    bu = input("Updating collection. Backup first? ").lower()
    if bu == 'y':
        backup_files()
    with open('quotes.txt', mode='r') as in_file:
        text = in_file.read().split('\n')
    # Initialize fields
    fields = {key: None for key in QUOTE_FIELDS.values()}
    # Text needs to be an empty string for appending
    fields['Text'] = ""
    # Notes needs to be an empty string so it can be omitted
    fields['Notes'] = ""
    books = load_books()
    for line in text:
        if line == "" or line == "\n":
            continue
        # If it's line for a field...
        if line[0] == '*':
            # Split off the field name, which comes before the colon
            line = line.split(': ')
            if line[0][1].lower() == 'p':
                line[0] = '*Page Number'
            # Rejoin, in case there are colons in the field data
            fields[line[0][1:]] = ': '.join(line[1:])
            continue
        # Otherwise it's the actual text of the quote
        else:
            fields['Text'] = line
            if any([val is None for val in fields.values()]):
                print("Missing fields")
                continue
            if fields['Book'] not in [index[1] for index in books.index]:
                print("Missing book")
                continue
            append_frame = pd.DataFrame(data=[fields.values()],
                                        columns=QUOTE_FIELDS.values())
            for field, data in fields.items():
                print("{}: {}".format(field, data))
            conf = input("All correct? ").lower()
            if conf == 'q':
                print("Quitting")
                return None
            if conf != 'y':
                continue
            else:
                # Append. Field data except for notes is maintained unless
                # changed
                quotes = load_quotes()
                quotes = quotes.append(append_frame)
                quotes.reset_index(drop=True, inplace=True)
                quotes.to_csv('quotes.csv')
                print("Added quote\n")
                # Re-initialize notes
                fields['Notes'] = ""
    print("No more quotes")
    conf = input("Clear file? Type 'CLEAR' to clear")
    if conf == 'CLEAR':
        with open('quotes.txt', mode='w') as out_file:
            out_file.write("")