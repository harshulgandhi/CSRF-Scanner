import urllib
import json
import urllib2
from time import time
from lxml import html
from urlparse import urlparse

class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_303(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl
    http_error_300 = http_error_303
    http_error_301 = http_error_303
    http_error_302 = http_error_303
    http_error_307 = http_error_303


class AttackApplication(object):

	def __init__(self,filename):
		self.filename = filename
		self.fileobj = open(self.filename,"r")

	def login(self,url,dataU):

		dataU = urllib.urlencode(dataU)
		req = urllib2.Request(url,dataU)
		res = urllib2.urlopen(req)
		cook = res.info()['Set-Cookie']	
		return cook

	def resolveParam(self,param):
		paramType = param["typeparameter"][0]

		if paramType == "reset" or paramType == "submit" :
			return ("","","")

		paramName = param["name"]
		if paramType == "text":
			paramValue = "astha"
		else:
			if param["value"] != "":
				paramValue = param["value"]
			else:
				paramValue = "naman"

		return (paramType,paramName,paramValue)

	def prepareUrl(self,url,parameters):

		sep = "?"
		for param in parameters:
			(pType,pName,pValue) = self.resolveParam(param)
			if pType != "": 
				url += sep+pName+"="+pValue
				sep = "&"

		return url

	def postUrl(self,parameters):
		paraList = ""
		values = {}
	        if parameters:
        	    for param in parameters:
            		(pType,pName,pValue) = self.resolveParam(param)
			if pType != "":
				values[pName]=pValue
        	return values

        def makeRequestLink(self,url):
        
            opener = urllib2.build_opener(NoRedirectHandler())
            urllib2.install_opener(opener)
            req = urllib2.Request(url)
            req.add_header("Cookie",self.cookie)
            res = urllib2.urlopen(req)
            return res.getcode()

	def makeRequest(self,url,method,parameters,isLogin):
  		
		res=""

		if method.upper() == "GET":
			url = self.prepareUrl(url,parameters)
			try:
				req = urllib2.Request(url)
				if isLogin == True:
					req.add_header("Cookie", self.cookie)
				try:
					start = time()
					res = urllib2.urlopen(req)
					tt = time() - start
					print tt
				except urllib2.URLError, e:
  					return (False,e.code)
  				else:
  					return (True,res)	

			except Exception, e:
				print "Exception in makeRequest"
				print url
				print e
				exit()

		else:
			dataU = self.postUrl(parameters)
			print dataU
			dataU = urllib.urlencode(dataU)
			try:
				req = urllib2.Request(url,dataU)
				if isLogin == True:
					req.add_header("Cookie", self.cookie)
				try:
					start = time()
					res = urllib2.urlopen(req)
					tt = time() - start
					print tt
				except urllib2.URLError, e:
  					return (False,e.code)
  				else:
  					(True,res)
  			except Exception, e:
				print "Exception in makeRequest Post"
				print url
				print e
				exit()
		return (True,res)


	def getRequestData(self,jsonObj):

		return (jsonObj["url"],jsonObj["method"],jsonObj["referer"],jsonObj["action"],jsonObj["requestType"],jsonObj["parameters"])


	def compareForm(self,res1,res2,act):
		tree = html.fromstring(res1)
		form1 = tree.xpath('//form[@action="'+act+'"]')

		if len(form1) == 0: #Note that this means that csrf not possible
			return True
		html1 = html.tostring(form1[0]).strip()

		tree = html.fromstring(res2)
		form2 = tree.xpath('//form[@action="'+act+'"]')
		if len(form2) == 0: #Note that this means that csrf not possible
			return True
		html2 = html.tostring(form2[0]).strip()

		return html1==html2

	def loginlogincheck(self,url,target,action,requestType):
		
		contlogin = ""
		contnlogin = ""
		(rstatlogin, reslogin) = self.makeRequest(url,"Get",[],True)
	 	if rstatlogin == True:
	 		contlogin = reslogin.read().strip()
	 	elif rstatlogin == False:
	 		return False
	 	
		(rstatnlogin, resnlogin) = self.makeRequest(url,"Get",[],True)
	 	if rstatnlogin == True:
	 		contnlogin = resnlogin.read().strip()
	 	elif rstatnlogin == False:
	 		return True 
		#If it is link directly compare the string
		if requestType.upper() == "LINK":
			if contlogin == contnlogin:
				return True
			else:
				return False
		#else if it is form then need to compare the form
		elif requestType.upper() == "FORM":
			compres = self.compareForm(contlogin,contnlogin,action)
			return compres
			
	def loginnotlogincheck(self,url,target,action,requestType):
		contlogin = ""
		contnlogin = ""
		(rstatlogin, reslogin) = self.makeRequest(url,"Get",[],True)
	 	if rstatlogin == True:
	 		contlogin = reslogin.read().strip()
	 	elif rstatlogin == False:
	 		return False

		(rstatnlogin, resnlogin) = self.makeRequest(url,"Get",[],False)
	 	if rstatnlogin == True:
	 		contnlogin = resnlogin.read().strip()
	 	elif rstatnlogin == False:
	 		return True 
		#If it is link directly compare the string
		if requestType.upper() == "LINK":
			if contlogin == contnlogin:
				return False
			else:
				return True
		#else if it is form then need to compare the form
		elif requestType.upper() == "FORM":
			compres = self.compareForm(contlogin,contnlogin,action)
			return not compres
			

	def attack(self):
		self.count =0
		attackSuccessList = []
		jsonstr = self.fileobj.read()
		jsonObj = json.loads(jsonstr)
		jsonArray = jsonObj["data"]

		for reqObj in jsonArray:
		 	self.count += 1
                        (url,method,referer,action,requestType,parameters) = self.getRequestData(reqObj)
		 	if self.count == 1:
		 		print "Logging in"
		 		loginData = self.postUrl(parameters)
				self.cookie = self.login(url,loginData)
				continue

			if requestType.upper() == "LINK":
			    # Do action for checking the exploits in Links
			    print "Checking CSRF in Links"
                            print str(url)
                            if url.find('database.php') != -1:
		                print "Skipping "+str(url)+" due to filtered keyword"
                                continue
                            rescode = self.makeRequestLink(url)
                            print str(rescode)
                	    if rescode == 302:
                                print "CSRF possible in "+str(self.count)
                                attackSuccessList.append(self.count)
                	    else:
                		print "CSRF not possible in "+str(self.count)
                             


			else: 
                            print "Checking CSRF in Forms"
		 	    #(url,method,referer,action,requestType,parameters) = self.getRequestData(reqObj)	
		 	    res1 = self.loginnotlogincheck(referer,url,action,requestType)
		 	    if res1 == True:
		 		    res2 = self.loginlogincheck(referer,url,action,requestType)
		 		    if res2 == True:
					   
		 			    (rstatus, res3) = self.makeRequest(url,method,parameters,"True")
		 			    if rstatus == True:
		 				    print "CSRF possible in "+str(self.count)
                                                    attackSuccessList.append(self.count) 
		 			    else:
		 				    print "CSRF not possible in "+str(self.count)+" condition 3 fails"
		 		    else:
		 			    print "CSRF not possible in "+str(self.count)+" condition 2 fails"
		 	    else:
		 		    print "CSRF not possible in "+str(self.count)+" condition 1 fails"

		return attackSuccessList

if __name__ == "__main__":

	obj = AttackApplication("requests.json")
	attackSuccessList = obj.attack()
	print "Successful Attacks Lists"
	print attackSuccessList


