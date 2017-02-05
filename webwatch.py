"""
Easy to use website monitoring script.

Markus Konrad <post@mkonrad.net>, February 2017

Checks if certain parts of a website have changed in comparison to the last time
the script was called. Best to use in cronjobs.

The main function to use is check_site(label, url, selector). "selector" is the CSS
selector for the website part(s) that you want to monitor.

Example usage:

import webwatch

webwatch.MAIL_SENDER = 'webwatch@example.com'
webwatch.MAIL_RECEIVER = 'notify_me@example.com'

webwatch.init()

webwatch.check_site('spiegel', 'http://www.spiegel.de/', 'div.teaser')

webwatch.finish()
"""

import sys
import os
import pickle
import hashlib
import smtplib

import requests
from bs4 import BeautifulSoup


SEND_MAIL = True
PREVSTATES_FILE = 'prevstates.pickle'

MAIL_SMTP_HOST = 'localhost'
MAIL_SENDER = 'webwatch@localhost'
MAIL_RECEIVER = 'notify_me@localhost'

MAIL_MESSAGE_TPL = """From: {sender}
To: {receiver}
Subject: webwatch - {status} - {label}

webwatch.py result - status is '{status}' for '{label}'
checked URL: {url}
"""

errors_occurred = False
smtp_conn = None

def init():
	global smtp_conn
	
	if SEND_MAIL:
		try:
			smtp_conn = smtplib.SMTP(MAIL_SMTP_HOST)
		except smtplib.SMTPException:
			errprint("error creating SMTP connection to host '%s'" % MAIL_SMTP_HOST)
			sys.exit(255)
	else:
		smtp_conn = None


def errprint(*args, **kwargs):
	global errors_occurred
	
	print(*args, file=sys.stderr, **kwargs)
	errors_occurred = True


def send_mail(status, label, url):
	msg = MAIL_MESSAGE_TPL.format(sender=MAIL_SENDER,
		receiver=MAIL_RECEIVER,
		status=status,
		label=label,
		url=url)
	
	if smtp_conn:
		try:
			smtp_conn.sendmail(MAIL_SENDER, [MAIL_RECEIVER], msg)
		except smtplib.SMTPException:
			errprint('error sending email via SMTP. wanted to send message: %s' % msg)
	else:
		print('- would send mail -')
		print('sender:', MAIL_SENDER)
		print('receiver:', MAIL_RECEIVER)
		print('message:')
		print(msg)
		print()


def check_site(label, url, selector, **kwargs):
	"""
	Check the website at *url* for changes. It will then scrape the website at *url*,
	extract its textual contents at *selector* and generate a sha256 hash from these
	contents. This hash will be compared with a hash that was generated at the previous
	run and has been loaded from a pickle file *prevstates.pickle*. If it's not the same
	hash, a notification email will be sent.
	
	additional optional arguments:
	- process_content_str: a function to process the textual contents and transform it
	                       in some way, e.g. stripping parts of the text
    - custom_request: a function to generate a custom HTTP request with `url`. it must
                      return a "requests" request object
	"""
	process_content_str = kwargs.pop('process_content_str', None)
	custom_request = kwargs.pop('custom_request', None)

	print("fetching website for '%s' from URL '%s'..." % (label, url))
	
	if custom_request:
		r = custom_request(url)
	else:
		r = requests.get(url)
	
	if r.status_code > 399:
		send_mail("problem fetching website - HTTP status code '%d'" % r.status_code, label, url)

	print("> parsing website content (selector is '%s')" % selector)
	soup = BeautifulSoup(r.text, 'html.parser')
	elems = soup.select(selector)

	if not elems:
		send_mail("no elements for selector '%s'" % selector, label, url)
		return

	print("> condensing content from %d website element(s)" % len(elems))

	all_str = []
	for e in elems:
		all_str.extend(e.stripped_strings)
	content_str = ''.join(all_str)
	
	if process_content_str:
		content_str = process_content_str(content_str)
	
	#print("> condensed content string:")
	#print(content_str)

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


def finish():
	if smtp_conn:
		smtp_conn.quit()
