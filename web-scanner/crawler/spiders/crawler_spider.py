from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from crawler.items import CrawlerItem
from scrapy.http import Request
import scrapy
from scrapy.http import FormRequest
from scrapy import log
from crawler.forms import FormItem
from crawler.forms import parameterItem	
from url_map import UrlMap
from scrapy.http.cookies import CookieJar

class CrawlerSpider(scrapy.Spider):
	name = "crawler"
	allowed_domains = ["app4.com"]
	start_urls = ['https://app4.com']
	counter = 0
	urlMapO = UrlMap()
	f = open("crawler/allLinks.txt","w")
	f1 = open("crawler/response-url.txt","w")

	'''
	Function gets called automatically in the beginning,
	it is only called once.
	Logs in the application
	'''
	def start_requests(self):
		return [scrapy.FormRequest(self.start_urls[0], 
			formdata={'username': 'admin@admin.com', 'password': 'admin', 'dologin':'1'},
			callback=self.after_login)]

	'''
	Below function has been commented out as it is
	not returning logged in forms
	'''
    # 'log' and 'pwd' are names of the username and password fields
    # depends on each website, you'll have to change those fields properly
    # one may use loginform lib https://github.com/scrapy/loginform to make it easier
    # when handling multiple credentials from multiple sites.
	# def parse(self, response):
	# 	self.f.write(str(response))
	# 	cookieJar = response.meta.setdefault('cookie_jar', CookieJar())
	# 	cookieJar.extract_cookies(response, response.request)
	# 	self.printText("COOKIE IS ==> " + str(cookieJar._cookies))
	# 	return FormRequest.from_response(
	#         response,
	#         formdata={'username': 'admin@admin.com', 'password': 'admin','dologin':'1'},
	#         callback=self.after_login
	#     )

	'''
	Call back function after
	login
	'''
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
	        link = self.start_urls[0]+"/index.php"
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
	    #linkWithOnClick = hxs.select('//a[@onclick]')
	    linkWithOnClick2 = hxs.select('//a[@onclick]/@href').extract()
	   
	    #for linksWOC in linkWithOnClick:
	    	# if str(linksWOC).find('onclick') > -1:
	    	# 	self.printText("ONCLICK FOUND : "+str(linksWOC))
	    	# else:
	    	#self.printText("ONCLICK : "+str(linksWOC))

	    for li in linkWithOnClick2:
	    	self.printText("Found link with onClick : "+str(li))
	    	if li.find("http") > -1:
	    		self.printText("Found link with on")
	    		self.urlMapO.addUrl(li)
	    		self.f.write("\n"+str(li))
	    	else:
	    		liCmplt = urljoin_rfc(get_base_url(response),li)
	    		self.urlMapO.addUrl(liCmplt)
	    		self.f.write("\n"+str(liCmplt))

	    	self.printText("ONCLICK@href : "+str(li))
		    #self.urlMapO.addUrl(linksWOC)
		    #self.urlMapO.printMap()
	    links = hxs.select('//a/@href').extract()

	    			
	    # Yield a new request for each link we found
	    

	    #self.f1.write(str(response.url)+"\n")
	    for link in links:
			self.printText("THIS IS A LINK=> " + link)
			
	        #only process external/full link
			if link.find("http") > -1:
				#checkUrlStatus calls another class where
				#we are maintaining a map to check if
				#a url has been visited.
				#Infinite crawling avoidance.		
				if self.checkUrlStatus(link) == 1 or link.find('logout.php')>-1:
					continue
				else:
					self.f.write("\n"+str(link))
					resp = Request(url=link, callback=self.parse_page) 
					self.urlMapO.addUrl(link)
					yield resp
			else:
				# constructing page url by getting
				# base url of current page for ex
				#('http://appx.com/admin') and
				# concatenating href link ('/status.php')
				link = urljoin_rfc(get_base_url(response),link)
				
				if self.checkUrlStatus(link) == 1 or link.find('logout.php')>-1:
					continue
				else:
					self.f.write("\n"+str(link))
					resp = Request(url=link, callback=self.parse_page) 
					#self.f.write("\n"+str(resp))
					self.urlMapO.addUrl(link)
					yield resp

            
	    item = CrawlerItem()
	    item["title"] = hxs.select('//title/text()').extract()[0]
	    item["url"] = response.url
	    #self.urlMapO.printMap() this is the map that holds each url's status
	    yield self.collect_item(item)
	    #Extracting forms from the web app
	    if response.url.find('?') == -1:
	    	forms = response.selector.xpath('//form')
	    	i=0
	    	for form in forms:
	       		formitem = FormItem()
			formitem['url'] = response.url
			formitem['action'] = forms[i].xpath('./@action').extract()
			formitem['method'] = forms[i].xpath('.//@method').extract()
			parameterslist = []
			parameters = forms[i].xpath('.//input')
			j=0
			for parameter in parameters:
				pm = parameterItem()
				pm['typeparameter'] = parameters[j].xpath('.//@type').extract()
				pm['name'] = parameters[j].xpath('.//@name').extract()
				pm['value'] = parameters[j].xpath('.//@value').extract()
				parameterslist.append(pm)
				j=j+1
			formitem['parameters'] = parameterslist
			i=i+1
			yield self.collect_item(formitem)

	def collect_item(self, item):
	    return item

	def checkUrlStatus(self,url):
		return self.urlMapO.getUrlStatus(url)

	def printText(self,text):
		print text
		print "=======================================================================================\n"

	def printPage(self,body,name):
		fo = open(name,"w")
		fo.write(body)
		fo.close

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
