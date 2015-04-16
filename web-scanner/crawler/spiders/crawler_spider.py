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
from json import dumps


class CrawlerSpider(scrapy.Spider):
    name = "oldcrawler"
    allowed_domains = ["app4.com"]
    start_urls = ['https://app4.com']
    LinkCount = 0
    FormCount = 0
    urlMapO = UrlMap()
    formMapO = UrlMap()
    formwriter = open ("crawler/forms.json","w")
    linkwriter = open("crawler/links.json","w")


    def start_requests(self):
        return [scrapy.FormRequest(self.start_urls[0], 
            formdata={'username': 'admin@admin.com', 'password': 'admin', 'dologin':'1'},
            callback=self.after_login)]


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
            
            link = response.url
            #self.printText("Page after Login"+str(response.url))
            self.urlMapO.addUrl(link)
            return Request(url=link,callback=self.parse_page)

    def parse_page(self, response):

        hxs = HtmlXPathSelector(response)

        linkWithOnClick2 = hxs.select('//a[@onclick]/@href').extract()

        for li in linkWithOnClick2:
            self.printText("Found link with onClick : "+str(li))
            if li.find("http") > -1:
                self.printText("Found link with on")
                if self.checkUrlStatus(li) != 1:
                    self.urlMapO.addUrl(li)
                    self.linkFileWriter(link,get_base_url(response))

            else:
                liCmplt = urljoin_rfc(get_base_url(response),li)
                if self.checkUrlStatus(liCmplt) != 1:
                    self.urlMapO.addUrl(liCmplt)
                    self.linkFileWriter(liCmplt,get_base_url(response))

            self.printText("ONCLICK@href : "+str(li))
            #self.urlMapO.addUrl(linksWOC)
            #self.urlMapO.printMap()
        links = hxs.select('//a/@href').extract()

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
                    #self.f.write("\n"+str(link))
                    self.linkFileWriter(link,get_base_url(response))
                    self.urlMapO.addUrl(link)
                    resp = Request(url=link, callback=self.parse_page) 
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
                    self.linkFileWriter(link,get_base_url(response))
                    self.urlMapO.addUrl(link)
                    resp = Request(url=link, callback=self.parse_page) 
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
            else:
                url = get_base_url(response)

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
        return 

    def linkFileWriter(self,link,referer):
        self.LinkCount = self.LinkCount+1
        requestType = 'Link'
        method = 'Get'
        parameters = []
        injectionPoint = {'url':link,'referer':referer,'requestType':requestType,'method':method,'parameters':parameters}
        self.linkwriter.write(dumps(injectionPoint, file, indent=4))
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
        formwriter.close()
        linkwriter.close() 
