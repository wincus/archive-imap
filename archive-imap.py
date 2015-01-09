#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:syntax=on:tabstop=4:set nowrap
'''
Modo de uso:
1. Configurar las variables:
	c.server 
	c.user 
	c.password 
	c.ssl 
	c.mapping 

2. ejecutar: python archive-mail -n
   (el parámetro -n evita que se hagan modificaciones en el buzón)
3. ejecutar: python archive-mail
   (se realizan los cambios)
'''

__AUTHOR__="wincus at gmail.com"
__LICENSE__="gpl"
__DATE__="lun mar 16 12:32:03 ART 2009"

import imaplib, sys, re

class Config:
	pass

def logger(string):
	sys.stdout.write("[%s]\n" % string)

def selectMailbox(handle,mailbox):
	logger("selecting %s" % mailbox)
	try:
		typ,data = handle.select(mailbox)
		return typ == "OK"
	except:
		return False

def createMailbox(handle,mailbox,dryrun=True):
	if not dryrun:
		logger("creating mailbox %s" % mailbox)
		typ,data = handle.create(mailbox)
		return typ == "OK"
	else:
		logger("(not really!) creating mailbox %s" % mailbox)
		return True

def copyContent(handle,set,target,dryrun=True):
	if not dryrun:
		logger("copy %s subset to %s" % (set,target))
		typ,data = handle.copy(set,target)
		return typ == "OK"
	else:
		logger("(not really!) copy %s subset to %s" % (set,target))
		return True

def delContent(handle,set,dryrun=True):
	if not dryrun:
		logger("deletting %s subset" % set)
		typ,data = handle.store(set, "+FLAGS", "\\Deleted")
		return typ == "OK"
	else:
		logger("(not really!) deletting %s subset" % set)
		return True

def expungeContent(handle,dryrun=True):
	if not dryrun:
		logger("expunge mailbox")
		typ,data = handle.expunge()
		return typ == "OK"
	else:
		logger("(not really!) expunge mailbox")
		return True

def main(argv=None):

	c = Config()
	c.server = "mail.domain.org"
	c.user = "user@fomain.org"
	c.password = "secretpassword"
	c.ssl = False
	c.debug = 3
	c.mailboxes = []
	c.root = "INBOX"
	c.dryrun = False
	c.mapping = {
		"archivo-2010" : "01-Jan-2010 1-Jan-2011",
		"archivo-2009" : "01-Jan-2009 1-Jan-2010",
		"archivo-2008" : "01-Jan-2008 1-Jan-2009",
		"archivo-2007" : "01-Jan-2007 1-Jan-2008",
		"archivo-2006" : "01-Jan-2006 1-Jan-2007",
		"archivo-2005" : "01-Jan-2005 1-Jan-2006",
		"archivo-2004" : "01-Jan-2004 1-Jan-2005",
		"archivo-2003" : "01-Jan-2003 1-Jan-2004",
		"archivo-2002" : "01-Jan-2002 1-Jan-2003",
		"archivo-2001" : "01-Jan-2001 1-Jan-2002",
		"archivo-2000" : "01-Jan-2000 1-Jan-2001",
	}
	c.exclude = ["Trash","TrashFolder"]

	if len(sys.argv) == 2 and sys.argv[1] == "-n": c.dryrun = True

	try:
		logger("conecting to server %s" % c.server)
		if c.ssl:
			M = imaplib.IMAP4_SSL(c.server)
		else:
			M = imaplib.IMAP4(c.server)
	except:
		logger("error conecting to %s" % c.server)
		sys.exit(1)

	try:
		logger("sending username %s " % c.user)
		M.login(c.user, c.password)
	except:
		logger("Usuario o contraseña no válidos")
		sys.exit(2)

	logger("setting debug level to %s " % c.debug)
	M.debug = c.debug
	logger("retrieving folders")
	if not selectMailbox(M,"INBOX"):
		logger("error selecting mailbox INBOX")
	typ, data = M.list()

	for item in data:
		regexp = re.match("[(]\\\\(.+)[)]\s+\"(?P<separator>.+)\"\s+\"(?P<mailbox>.+)\"\s*", item)
		c.separator = regexp.group("separator")
		mailbox = regexp.group("mailbox")
		if not len(filter(lambda x: x in " ".join(c.mapping.keys()), mailbox.split(c.separator))):
			if not mailbox in c.exclude:
				c.mailboxes.append(mailbox)

	for mailbox in c.mailboxes: 
		if not selectMailbox(M,mailbox): 
			logger("Error: can't select mailbox: %s" % mailbox)
			continue
		for archivemailbox in c.mapping.keys():    
			logger("searching mails sent between %s and %s in %s" % (c.mapping[archivemailbox].split(" ")[0],c.mapping[archivemailbox].split(" ")[1],mailbox))
			typ, data = M.search(None, "ALL", "SEEN", "SENTSINCE", c.mapping[archivemailbox].split(" ")[0], "SENTBEFORE", c.mapping[archivemailbox].split(" ")[1],"UNFLAGGED")
			target = data.pop().split()
			if typ == "OK" and len(target):
				logger("got %s" % len(target))
				if mailbox == c.root:
					mynewmailbox = ""
				else:
					mynewmailbox = c.separator + mailbox.replace(c.root + c.separator,"")
				c.archivemailbox = c.root+c.separator+archivemailbox+mynewmailbox
				createMailbox(M,c.archivemailbox,c.dryrun)
				if not copyContent(M,",".join(target),c.archivemailbox,c.dryrun):
					continue
				else:
					if delContent(M,",".join(target),c.dryrun): expungeContent(M,c.dryrun)
						
	M.close()
	M.logout()
	sys.exit(0)

if __name__ == "__main__":
    main()

