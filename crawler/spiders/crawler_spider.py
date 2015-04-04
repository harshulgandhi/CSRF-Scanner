from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from crawler.items import CrawlerItem
from scrapy.http import Request
import scrapy
from scrapy.http import FormRequest
from scrapy import log

class CrawlerSpider(Spider):
	name = "crawler"
	allowed_domains = ["app4.com"]
	start_urls = ['https://app4.com']
	counter = 0
	f = open("allLinks.txt","w")

    # 'log' and 'pwd' are names of the username and password fields
    # depends on each website, you'll have to change those fields properly
    # one may use loginform lib https://github.com/scrapy/loginform to make it easier
    # when handling multiple credentials from multiple sites.
	def parse(self, response):
	    return FormRequest.from_response(
	        response,
	        formdata={'username': 'admin@admin.com', 'password': 'admin'},
	        callback=self.after_login
	    )

	def after_login(self, response):
	    # check login succeed before going on
	    self.printText(str(response))
	    if "ERROR: Invalid username" in response.body:
	        self.log("Login failed", level=log.ERROR)
	        return
	        
	    # continue scraping with authenticated session...
	    else:
	    	self.printText("Successfully logged in to APP4")
	        self.log("Login succeed!", level=log.DEBUG)
	        
	        #index.php is the page that gets loaded as soon as we log in.
	        #This is manual thing for now, we will have to make this generic
	        return Request(url="https://app4.com/index.php",
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

	    # Yield a new request for each link we found
	    # #this may lead to infinite crawling...
	    for link in links:
			print "THIS IS A LINK" + link
	        #only process external/full link
			if link.find("http") > -1:
				self.f.write(str(link))
				yield Request(url=link, callback=self.parse_page)
			else:
				link = start_urls[0] + link
				self.f.write(str(link))

            
	    item = LinkItem()
	    item["title"] = hxs.select('//title/text()').extract()[0]
	    item["url"] = response.url
	    yield self.collect_item(item)



	def collect_item(self, item):
	    return item


	def printText(self,text):
		print "=======================================================================================\n"
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
		f.write(str(link)+"\n")
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
		f.write(str(link)+"\n")
	for link in allLinks2:
		f.write(str(link)+"\n")
	print "*****************Menu item received*******************"
	print "len(allLinks) ==> ",len(allLinks)
	i=0
	for menuItem in menuItems:
		print "**************Printing items***********************\n"
		i+=1
		item = CrawlerItem()
		item['url']	= menuItem.xpath('//*[@id="jsn-pos-mainmenu"]/div[2]/div/div/ul/li['+str(i)+']/a/@href').extract()[0]
		item['title'] = menuItem.xpath('//*[@id="jsn-pos-mainmenu"]/div[2]/div/div/ul/li['+str(i)+']/a/span/text()[1]').extract()[0]
		print str(item['url'])
		yield item

'''