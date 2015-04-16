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
from loginform import fill_login_form
import re
from json import dumps

MAXURLCOUNT = 99

class CrawlerSpider(scrapy.Spider):
	name = "crawler"
	allowed_domains = []
	start_urls = []
	LinkCount = 0
	FormCount = 0
	counter = 0
	urlMapO = UrlMap()
	formMapO = UrlMap()
	dupLinkMapO = UrlMap()
	f = open("/home/user/CSRF-Scanner/web-scanner/crawler/allLinks.txt","w")
	f1 = open("/home/user/CSRF-Scanner/web-scanner/crawler/response-url.txt","w")
	formwriter = open ("crawler/forms.json","w")
	linkwriter = open("crawler/links.json","w")
	login_user = ''
	login_pass= ''

	def __init__(self):
		self.login_user = raw_input("Enter username : ")
		
		self.login_pass = raw_input("Enter password : ")
		
		startUrl = raw_input("Enter login page : ")
		self.start_urls.append(startUrl)
		needle="(app.)"
		heystack= self.start_urls[0]
		dom = re.search(needle,heystack)
		self.allowed_domains.append(str(dom.group(0))+".com")
	'''
	Function gets called automatically in the beginning,
	it is only called once.
	Logs in the application
	'''
	def parse(self,response):
		if self.start_urls[0].find('app8.com') > -1:
			self.printText(self.login_user)
			self.printText(self.login_pass)
			return scrapy.FormRequest.from_response(response, 
				formdata={  'email': self.login_user, 'password': self.login_pass},
				method="POST",
				dont_filter=True,
				callback=self.after_login)
		else:
			args, url, method = fill_login_form(response.url, response.body, self.login_user, self.login_pass)
			self.printText("args "+str(args))
			self.printText("url "+str(url))
			self.printText("Method "+str(method))
			self.printText("Printing login response")
			self.printText(response)
			return scrapy.FormRequest(url,method=method,formdata=args,dont_filter=True,callback=self.after_login)

	'''
	Call back function after
	login
	'''
	def after_login(self, response):
		# check login succeed before going on
		self.printText("Beginning to scrape website")
		self.printText(str(response.body))
		self.printText("Response url "+str(response.url))
		if "ERROR: Invalid username" in response.body:
			self.log("Login failed", level=log.ERROR)
			#return
			
		# continue scraping with authenticated session...
		else:
			self.printText("Successfully logged in to APP")
			self.log("Login succeed!", level=log.DEBUG)
				
		link = response.url
		self.urlMapO.addUrl(link)
		return Request(url=link,callback=self.parse_page)


	# crawling all other urls in the site with the same
	# authenticated session.
	def parse_page(self, response):
		""" Scrape useful stuff from page, and spawn new requests
		"""
		print "MAXURLCOUNT "+str(MAXURLCOUNT)
		if self.urlMapO.getDupUrlCount(get_base_url(response)) > MAXURLCOUNT:
		    return
		self.printText("Inside parse page function")
		hxs = HtmlXPathSelector(response)
		linkWithOnClick2 = hxs.select('//a[@onclick]/@href').extract()
	   
		for li in linkWithOnClick2:
			self.printText("Found link with onClick : "+str(li))
			if li.find("http") > -1:
				self.printText("Found link with on")
				if self.checkUrlStatus(li) != 1:
					self.urlMapO.addUrl(li)
					self.f.write("\n"+str(li))
					self.linkFileWriter(link,get_base_url(response))

			else:
				self.printText("Writing executable links to text file")
				liCmplt = urljoin_rfc(get_base_url(response),li)
				if self.checkUrlStatus(liCmplt) != 1:
					self.urlMapO.addUrl(liCmplt)
					self.f.write("\n"+str(liCmplt))
					self.linkFileWriter(liCmplt,get_base_url(response))

		links = hxs.select('//a/@href').extract()

		# Yield a new request for each link we found

		for link in links:
			self.printText("THIS IS A LINK=> " + link)
			#only process external/full link
			if link.find("http") > -1:
				#checkUrlStatus calls another class where
				#we are maintaining a map to check if
				#a url has been visited.
				#Infinite crawling avoidance.		
				self.printText("Base url found i == "+str(link))
				link = self.httpFixer(link)
				if self.checkUrlStatus(link) == 1 or link.find('logout.php')>-1:
					continue
				else:
					self.linkFileWriter(link,get_base_url(response))
					self.f.write("\n"+str(link))
					self.urlMapO.addUrl(link)
					resp = Request(url=link, callback=self.parse_page)
					yield resp
			else:
				# constructing page url by getting
				# base url of current page for ex
				#('http://appx.com/admin') and
				# concatenating href link ('/status.php')
				link = urljoin_rfc(get_base_url(response),link)
				self.printText("Base url found i == "+str(get_base_url(response)))
				
				if self.checkUrlStatus(link) == 1 or link.find('logout.php')>-1:
					continue
				else:
					self.linkFileWriter(link,get_base_url(response))
					self.f.write("\n"+str(link))
					self.urlMapO.addUrl(link)
					resp = Request(url=link, callback=self.parse_page) 
					#self.f.write("\n"+str(resp))
					yield resp

		forms = response.selector.xpath('//form')

		for form in forms:
			uniquestring = ""
			if form.xpath('./@action'):
				li = form.xpath('./@action').extract()[0]
				if li.find("http") > -1:
					url = li    
				else:   
					url = urljoin_rfc(get_base_url(response),li)

				if form.xpath('.//@method'):
					method = form.xpath('.//@method').extract()[0]
				else:
					method = "GET"
				uniquestring = uniquestring+url
				uniquestring = uniquestring+method
				
				parameterslist = []
				parameters = form.xpath('.//input')
				for parameter in parameters:

					# Extracting type parameter
					if parameter.xpath('.//@type'): 
						typeparameter = parameter.xpath('.//@type').extract()[0]
					
					# Extracting name parameter 
					if parameter.xpath('.//@name'):
						name = parameter.xpath('.//@name').extract()[0]
					else:
						name = ''
						
					uniquestring = uniquestring + name                
						
					if parameter.xpath('.//@value'):
						value = parameter.xpath('.//@value').extract()
					else:
						value = ''

					formparameter = {'typeparameter':typeparameter,'name':name,'value':value}
					parameterslist.append(formparameter)


				if self.checkifformPresent(uniquestring) != 1:      
					self.formFileWriter(url,response.url,method,parameterslist)
					self.formMapO.addUrl(uniquestring)

	def collect_item(self, item):
		return item

	def checkUrlStatus(self,url):
		return self.urlMapO.getUrlStatus(url)

	def checkifformPresent(self,string):
		return self.formMapO.getUrlStatus(string)

	def printText(self,text):
		print text
		print "=======================================================================================\n"

	def printPage(self,body,name):
		fo = open(name,"w")
		fo.write(body)
		fo.close

	def httpFixer(self,link):
		if link.find("http:///") > -1:
			return link.replace("http:///","http://",1)
		elif link.find("https:///")>-1:
			return link.replace("https:///","https://",1)
		else:
			return link

	def linkFileWriter(self,link,referer,status):
		if url.find('?') != -1:
		    self.LinkCount = self.LinkCount+1
		    requestType = 'Link'
		    method = 'Get'
		    parameters = []
		    injectionPoint = {'url':link,'referer':referer,'status':status,'requestType':requestType,'method':method,'parameters':parameters}
		    self.linkwriter.write(dumps(injectionPoint, file, indent=4))
		return
	def loginFormFileWriter(self,link,method,parameters):
		requestType = 'Login'
		referer = ''
		LoginForm = {'url':link,'referer':referer,'requestType':requestType,'method':method,'parameters':parameters}
		self.linkwriter.write(dumps(LoginForm, file, indent=4))
		return 
	
	def formFileWriter(self,link,referer,method,parameters):
		self.FormCount=self.FormCount+1
		requestType = 'Form'
		injectionPoint =  {'url':link,'referer':referer,'requestType':requestType,'method':method,'parameters':parameters}
		self.formwriter.write(dumps(injectionPoint,file,indent=4))
		return

	def spider_closed(self, spider):
		
		print "Spider closed\n"
		print "Link count =" + self.LinkCount+"\n"
		print "Form Count =" + self.FormCount+"\n"
		self.formwriter.close()
		self.linkwriter.close()
