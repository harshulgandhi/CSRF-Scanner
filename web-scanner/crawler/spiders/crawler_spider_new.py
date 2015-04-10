from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from crawler.items import CrawlerItem
from scrapy.http import Request
import scrapy
from scrapy.http import FormRequest
from scrapy import log
from crawler.items import CrawlerItem
from url_map import UrlMap
from scrapy.http.cookies import CookieJar

class CrawlerSpider(scrapy.Spider):
	name = "crawler"
	allowed_domains = ["app4.com"]
	start_urls = ['https://app4.com']
	counter = 0
	parse_link = start_urls[0]
	urlMapO = UrlMap()
	f = open("crawler/allLinks.txt","w")


	def start_requests(self):
		self.printText("CALLING START_REQUESTS***********************************")
		return [scrapy.FormRequest(self.start_urls[0], 
			formdata={'username': 'admin@admin.com', 'password': 'admin', 'dologin':'1'},
			callback=self.after_login)]

    # 'log' and 'pwd' are names of the username and password fields
    # depends on each website, you'll have to change those fields properly
    # one may use loginform lib https://github.com/scrapy/loginform to make it easier
    # when handling multiple credentials from multiple sites.
	def parse(self, response):
		#self.f.write(str(response))
		# cookieJar = response.meta.setdefault('cookie_jar', CookieJar())
		# cookieJar.extract_cookies(response, response.request)
		# self.printText("COOKIE IS ==> " + str(cookieJar._cookies))
		# resp = FormRequest.from_response(
	 #        response,
	 #        formdata={'username': 'admin@admin.com', 'password': 'admin','dologin':'1'},
	 #        callback=self.after_login,
	 #        #meta = {'dont_merge_cookies': True, 'cookie_jar': cookieJar}
	 #    )
		return response

	def after_login(self, response):
	    # check login succeed before going on
	    self.printText(str(response.body))
	    if "ERROR: Invalid username" in response.body:
	        self.log("Login failed", level=log.ERROR)
	        return
	        
	    # continue scraping with authenticated session...
	    else:
	    	self.printText("Successfully logged in to APP4")
	        self.log("Login succeed!", level=log.DEBUG)
	        	
	        #index.php is the page that gets loaded as soon as we log in.
	        #This is manual thing for now, we will have to make this generic
	        link = "https://app4.com/index.php"
	        self.urlMapO.addUrl(link)
	        return Request(url=link,
	                       callback=self.parse_page)


    # example of crawling all other urls in the site with the same
    # authenticated session.
	def parse_page(self, response):
	    """ Scrape useful stuff from page, and spawn new requests
	    """
	    hxs = HtmlXPathSelector(response)

	    # i = CrawlerItem()
	    # find all the link in the <a href> tag
	    links = hxs.select('//a/@href').extract()
	    print "this is the first list of link"
	    print "***********************************\n"
	    for link in links:
	    	print link + "\n"
	    print "***********************************\n"
	    self.printText("Links length is : "+str(len(links)))
	    # Yield a new request for each link we found
	    # #this may lead to infinite crawling...
	    for link in links:
	    	parse_link=parse_link+"/"+link	
		self.printText("THIS IS A LINK=> " + link)

	        #only process external/full link
		if link.find("http") > -1:
				
			if self.checkUrlStatus(link) == 1:
				continue
			else:
				self.f.write(str(link))
				resp = Request(url=link, callback=self.parse_page) 
				#self.f.write(str(resp))
				self.urlMapO.addUrl(link)
				yield resp
		else:		
			if self.checkUrlStatus(parse_link) == 1:
				continue
			else:
				self.f.write("\n"+str(parse_link))
				resp = Request(url=parse_link, callback=self.parse_page) 
				#self.f.write("\n"+str(resp))
				self.urlMapO.addUrl(parse_link)
				yield resp
		if parse_link.endswith("/"+link):
    			parse_link = parse_link[:-(len(link)+1)]



            
	    item = CrawlerItem()
	    item["title"] = hxs.select('//title/text()').extract()[0]
	    item["url"] = response.url
	    self.urlMapO.printMap()
	    yield self.collect_item(item)



	def collect_item(self, item):
	    return item

	def checkUrlStatus(self,url):
		return self.urlMapO.getUrlStatus(url)

	def printText(self,text):
		print text
		print "=======================================================================================\n"

''' 
this part of code was self written. Now we are using
sample code provided by module facilitator

def parse(self,response):
	print "URL COUNTER => ",self.counter
	allLinks = Selector(response).xpath('//a[*]/@href')
	f = open("allLinks.txt","w")
	f1 = open("responses.html","w")
	for link in allLinks:
		print "LINK ==> ",str(link.extract())
		if not link.extract().startswith('http://'):
			link = self.start_urls[0] + link.extract()
		else:
			link = link.extract()
		f.write(str(link)+"")
		self.counter+=1
		resp =Request(link, callback=self.parse) 
		f1.write(str(resp))
		yield resp



def parse(self,response):
	#menuItems = response.css("#questions > div")
	menuItems = Selector(response).xpath('//*[@id="jsn-pos-mainmenu"]/div[2]/div/div/ul/li')
	allLinks = Selector(response).xpath('//a[*]/@href')
	allLinks2 = Selector(response).xpath('//link[*]/@href')
	f = open("allLinks.txt","w")
	for link in allLinks:
		f.write(str(link)+"")
	for link in allLinks2:
		f.write(str(link)+"")
	print "*****************Menu item received*******************"
	print "len(allLinks) ==> ",len(allLinks)
	i=0
	for menuItem in menuItems:
		print "**************Printing items***********************"
		i+=1
		item = CrawlerItem()
		item['url']	= menuItem.xpath('//*[@id="jsn-pos-mainmenu"]/div[2]/div/div/ul/li['+str(i)+']/a/@href').extract()[0]
		item['title'] = menuItem.xpath('//*[@id="jsn-pos-mainmenu"]/div[2]/div/div/ul/li['+str(i)+']/a/span/text()[1]').extract()[0]
		print str(item['url'])
		yield item

'''
