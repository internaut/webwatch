"""
Easy to use website monitoring script.
Checks if certain parts of a website have changed in comparison to the last time
the script was called. Best to use in cronjobs.

Example usage:

import webwatch

webwatch.MAIL_SENDER = 'webwatch@example.com'
webwatch.MAIL_RECEIVER = 'notify_me@example.com'

webwatch.check_site('spiegel', 'http://www.spiegel.de/', 'div.teaser')
"""

import sys
import os
import pickle
import hashlib
import smtplib

import requests
from bs4 import BeautifulSoup

SEND_MAIL = False
PREVSTATES_FILE = 'prevstates.pickle'

MAIL_SMTP_HOST = 'localhost'
MAIL_SENDER = 'webwatch@mkonrad.net'
MAIL_RECEIVER = 'post@mkonrad.net'

MAIL_MESSAGE_TPL = """From: {sender}
To: {receiver}
Subject: webwatch - {status} - {label}

webwatch.py result - status is '{status}' for '{label}'
checked URL: {url}
"""


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def send_mail(status, label, url):
	msg = MAIL_MESSAGE_TPL.format(sender=MAIL_SENDER,
		receiver=MAIL_RECEIVER,
		status=status,
		label=label,
		url=url)
	
	if SEND_MAIL:
		try:
			smtp_conn = smtplib.SMTP(MAIL_SMTP_HOST)
			smtp_conn.sendmail(MAIL_SENDER, [MAIL_RECEIVER], msg)         
			smtp_conn.exit()
		except smtplib.SMTPException:
			errprint('error sending email via SMTP')
			sys.exit(3)
	else:
		print('- would send mail -')
		print('sender:', MAIL_SENDER)
		print('receiver:', MAIL_RECEIVER)
		print('message:')
		print(msg)
		print()

def check_site(label, url, selector):
	print("fetching website for '%s' from URL '%s'..." % (label, url))
	r = requests.get(url)
	if r.status_code > 399:
		send_mail("problem fetching website - HTTP status code '%d'" % r.status_code, label, url)
		sys.exit(1)

	print("> parsing website content (selector is '%s')" % selector)
	soup = BeautifulSoup(r.text, 'html.parser')
	elems = soup.select(selector)

	if not elems:
		send_mail("no elements for selector '%s'" % selector, label, url)
		sys.exit(2)

	print("> condensing content from %d website element(s)" % len(elems))

	all_str = []
	for e in elems:
		all_str.extend(e.stripped_strings)
	content_str = ''.join(all_str)

	cur_hash = hashlib.sha256(content_str.encode()).hexdigest()

	if os.path.exists(PREVSTATES_FILE):
		prevstates = pickle.load(open(PREVSTATES_FILE, 'rb'))
	else:
		prevstates = {}

	prev_hash = prevstates.get(label, None)

	if prev_hash:
		if prev_hash != cur_hash:
			print('> change detected')
			send_mail('change', label, url)
		else:
			print('> no change detected')
	else:
		send_mail('no previous state', label, url)

	prevstates[label] = cur_hash
	pickle.dump(prevstates, open(PREVSTATES_FILE, 'wb'))
