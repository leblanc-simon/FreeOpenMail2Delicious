# -*- coding: utf-8 -*-

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.



# Notifier example from tutorial
#
# See: http://github.com/seb-m/pyinotify/wiki/Tutorial
#

# import pyinotofy to check the new mail
import pyinotify

# import smtplib and email module to parse email
import smtplib
from email.parser import Parser
from email.header import decode_header

# gestion des accents
from unidecode import unidecode

# import urllib2 to call the delicious API
import urllib, urllib2

# import sys for exception (but my application can't raise :-))
import sys

# login/password to delicious
delicious_username = '[username]'
delicious_password = '[password]'
# path to watch
path_watch = '[path to watch]'

delicious_url      = 'https://api.del.icio.us/v1/posts/add'

wm = pyinotify.WatchManager() # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY # watched events




'''
Encoding the login/pass for an HTTP Authentification

@param  string  user        username
@param  string  password    password
@return string              the encoding string for authentification
'''
def encodeUserData(user, password):
    return "Basic " + (user + ":" + password).encode("base64").rstrip()


'''
Parse the mail and add the datas to delicious

@param  string  file    The filename to parse
'''
def parse_mail(file):
    # Open the mail
    with open(file, 'rb') as fp:
        # Convert file to mail.message object
        mail = Parser().parse(fp)
        
        # init the vars
        url = ''
        title = ''
        description = ''
        shared = 'yes'
        tags_tuple = decode_header(mail['subject'])
        tags = ''
        for tag in tags_tuple:
            if len(tag) == 2:
                if tag[1] != None:
                    tags += tag[0].decode(tag[1]).encode('iso-8859-1') + ' '
                else:
                    tags += tag[0].encode('iso-8859-1') + ' '
        
        # check if the bookmark must be private or public
        if '[' + 'private' + ']' in tags:
            shared = 'no'
            tags = tags.replace('[' + 'private' + ']', '')
        
        # parse the mail to get the text/plain content
        for part in mail.walk():
            if part.get_content_type() == 'text/plain':
                # get the content of the mail
                message = part.get_payload(None, True)
                try:
                    message = message.decode(mail.get_content_charset('iso-8859-1')).encode('iso-8859-1')
                except:
                    pass
                    
                message = message.split('\n')
                
                # get url, title and description
                nb_line = 0
                for line in message:
                    if ('http://' in line.strip() or 'https://' in line.strip()) and nb_line == 0:
                        url = line.strip()
                    elif nb_line == 1:
                        title = line.strip().replace('\n', ' ')
                    else:
                        description += line.strip().replace('\n', ' ') + ' '
                    
                    nb_line += 1
        
        # if one url and one title found, add the link to delicious
        if url != '' and title != '':
            # encode the parameters
            params = urllib.urlencode({'url' : url, 'description' : unidecode(title), 'extended': unidecode(description), 'tags' : unidecode(tags), 'shared' : shared})
            
            # create request
            req = urllib2.Request(delicious_url + '?' + params)
            
            # add http authentification
            req.add_header('Authorization', encodeUserData(delicious_username, delicious_password))
            
            # call delicious api
            res = urllib2.urlopen(req)
            
            # read response and print it
            response = res.read()
            print response
            
            # if response is wrong, print the url called
            if 'something went wrong' in response:
                print delicious_url + '?' + params
        
        else:
            print 'url or title is null'


'''
Class managing the files notifications

@see: http://github.com/seb-m/pyinotify/wiki/Tutorial
'''
class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Create:", event.pathname
        parse_mail(event.pathname)
    
    def process_IN_MODIFY(self, event):
        print "Modify:", event.pathname
        parse_mail(event.pathname)

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname


################################################################################
#
#                               MAIN PROGRAM
#
################################################################################

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch(path_watch, mask, rec=True)

notifier.loop()
