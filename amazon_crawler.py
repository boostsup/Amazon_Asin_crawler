#!/usr/bin/env python
from lxml import html  
import Queue,csv,time,sys,urllib2
import threading
import requests
from random import choice
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient

## Mongodb
client = MongoClient('localhost', 27017)
db = client.amazon_database
collection = db.amazon_collection
posts = db.posts


#generate url list from asin number
def getUrlList():
	UrlList = []
	AsinList = csv.DictReader(open("Asinfeed.csv"))
	for i in AsinList:
		UrlList.append("http://www.amazon.com/dp/"+i['asin'])
	return UrlList

#get proxy list from txt file
def getProxyList():
	proxyList = []
	with open('./list.txt') as f:
		proxys = f.readlines()
	for i in proxys:
		if len(i) > 5:
			if i[:4] != 'http':
				proxyList.append('http://'+i.split('\n')[0])
			else:
				proxyList.append(i.split('\n')[0])
	proxyList = list(set(proxyList))
	return proxyList



hosts = getUrlList()
Max_host = len(hosts) # record the number of hosts left
Max_none = 0 #record the number of None return
proxy = getProxyList()

queue = Queue.Queue()
out_queue = Queue.Queue()

class ThreadUrl(threading.Thread):
	def __init__(self, queue, out_queue):
		threading.Thread.__init__(self)
		self.queue = queue
		self.out_queue = out_queue

	def run(self):
		while True:
			#grabs host from queue
			host = self.queue.get()

			#grabs urls of hosts and then grabs chunk of webpage
			print host
			chunk = self.AmzonParser(host)
 
			#place chunk into out queue
			self.out_queue.put(chunk)
			global Max_host 
			Max_host = Max_host - 1
 			print Max_host,' hosts has left'
			#signals to queue job is done
			self.queue.task_done()
	
	def AmzonParser(self,url):
		try:
			page = requests.get(url,headers = self._random_useragent(),proxies = {"http":"{}".format(choice(proxy))},timeout = 3)
			doc = html.fromstring(page.content)
			XPATH_NAME = '//h1[@id="title"]//text()'
			XPATH_SALE_PRICE = '//span[contains(@id,"ourprice") or contains(@id,"saleprice")]/text()'
			XPATH_ORIGINAL_PRICE = '//td[contains(text(),"List Price") or contains(text(),"M.R.P") or contains(text(),"Price")]/following-sibling::td/text()'
			XPATH_CATEGORY = '//a[@class="a-link-normal a-color-tertiary"]//text()'
			XPATH_AVAILABILITY = '//div[@id="availability"]//text()'
			RAW_NAME = doc.xpath(XPATH_NAME)
			RAW_SALE_PRICE = doc.xpath(XPATH_SALE_PRICE)
			RAW_CATEGORY = doc.xpath(XPATH_CATEGORY)
			RAW_ORIGINAL_PRICE = doc.xpath(XPATH_ORIGINAL_PRICE)
			RAw_AVAILABILITY = doc.xpath(XPATH_AVAILABILITY)
			NAME = ' '.join(''.join(RAW_NAME).split()) if RAW_NAME else None
			SALE_PRICE = ' '.join(''.join(RAW_SALE_PRICE).split()).strip() if RAW_SALE_PRICE else None
			CATEGORY = ' > '.join([i.strip() for i in RAW_CATEGORY]) if RAW_CATEGORY else None
			ORIGINAL_PRICE = ''.join(RAW_ORIGINAL_PRICE).strip() if RAW_ORIGINAL_PRICE else None
			AVAILABILITY = ''.join(RAw_AVAILABILITY).strip() if RAw_AVAILABILITY else None
			if not ORIGINAL_PRICE:
				ORIGINAL_PRICE = SALE_PRICE
			if page.status_code!=200:
				return self.AmzonParser(url)
			data = {
					'NAME':NAME,
					'SALE_PRICE':SALE_PRICE,
					'CATEGORY':CATEGORY,
					'ORIGINAL_PRICE':ORIGINAL_PRICE,
					'AVAILABILITY':AVAILABILITY,
					'URL':url,
					}
			if data['NAME'] == None or data['CATEGORY'] == None:
				global Max_none
				Max_none += 1
				print 'None happens ,Max_none is ',Max_none
				return self.AmzonParser(url)
			return data
		except requests.exceptions.RequestException as e:
			return self.AmzonParser(url)
		except:
			print "Unexpected error:", sys.exc_info()[0]
			return self.AmzonParser(url)


#generate random user agent ,otherwise amazon will block you by this!
	def _random_useragent(self):
		UAS = []
		HEADERS = {
					'User-Agent': 'Mozilla/5.0',
					'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Accept-Encoding': 'gzip, deflate',
					'Connection': 'close',
					'DNT': '1'
				}
		#if you want more user agent ,just google and add !
		with open('./ua.txt') as f:
			ua = f.readlines()
			for i in ua:
				UAS.append(i.split('\n')[0])
		HEADERS['User-Agent'] = choice(UAS)
		return HEADERS


class DatamineThread(threading.Thread):
	"""Threaded Url Grab"""
	def __init__(self, out_queue):
		threading.Thread.__init__(self)
		self.out_queue = out_queue

	def run(self):
		while True:
			#grabs host from queue
			chunk = self.out_queue.get()
			print chunk
			#insert the data to mongodb
			posts.insert(chunk)
			#signals to queue job is done
			self.out_queue.task_done()

start = time.time()

def main():
	#if you want it run more quickly ,please increase the range
	#spawn a pool of threads, and pass them queue instance
	for i in range(5):
		t = ThreadUrl(queue, out_queue)
		t.setDaemon(True)
		t.start()
		#populate queue with data
	for host in hosts:
		queue.put(host)

	for i in range(5):
		dt = DatamineThread(out_queue)
		dt.setDaemon(True)
		dt.start()


	#wait on the queue until everything has been processed
	queue.join()
	out_queue.join()
 
main()
print "Elapsed Time: %s" % (time.time() - start)