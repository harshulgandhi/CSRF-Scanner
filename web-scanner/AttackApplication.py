import urllib
import json
import urllib2
from time import time
from lxml import html
from urlparse import urlparse
from json import dumps

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

'''
class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_302(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301( 
            self, req, fp, code, msg, headers)              
        result.status = code                                 
        return result                                       

    def http_error_303(self, req, fp, code, msg, headers):   
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)              
        result.status = code                                
        return result

'''
class AttackApplication(object):

	def __init__(self,inputFilename,outputFilename):
		self.filename = inputFilename
		self.fileobj = open(self.filename,"r")
		self.outputFilename = outputFilename
		self.outputfileobj = open(self.outputFilename,"w")
		self.writeOutputFileHeader()

	def login(self,url,dataU):

		dataU = urllib.urlencode(dataU)
		req = urllib2.Request(url,dataU)
		res = urllib2.urlopen(req)
		cook = res.info()['Set-Cookie']	
		return cook
        
        def writeOutputFileHeader(self):
		self.outputfileobj.write("{\"Success_Attack_Vectors\":[")

        def writeoutputFileTail(self):
	        self.outputfileobj.write("]}")

        def writeToOutputFile(self,reqObj):
                self.outputfileobj.write(dumps(reqObj, file, indent=4))
                self.outputfileobj.write(",")
                         
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

        def makeRequestLink(self,url,parameters,requestType):
        
            opener = urllib2.build_opener(NoRedirectHandler())
            urllib2.install_opener(opener)
	    if requestType.upper() == "FORM":
	        requrl = self.prepareUrl(url,parameters)
	    else:
                requrl = url
            try:	 	
                req = urllib2.Request(requrl)
                req.add_header("Cookie",self.cookie)
		try:
                    res = urllib2.urlopen(req)
                except urllib2.URLError, e:
  		    return e.code
  	        else:
  		    return res.getcode()
            except Exception, e:
	        print "Exception in makeRequest"
		print url
		print e
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
                print "Debug"   
                if res1 == "" or res2 == "":
	            return False
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

                compres = self.compareForm(contlogin,contnlogin,action)
		return compres
                    
                '''
		#If it is link directly compare the string
		if requestType.upper() == "LINK":
			if contlogin == contnlogin:
				return True
			else:
				return False
		#else if it is form then need to compare the form
		elif requestType.upper() == "FORM":
			c
		'''
	
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
                
                compres = self.compareForm(contlogin,contnlogin,action)
                return not compres
                
                # Commented as we have different handling for the Link  
                '''
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
		'''	
        def checkValidForm(self,referer,url,method,action,parameters):
            #Check 1:
            if method.upper() == "POST":
	        if len(parameters) == 0:
		    return False;
	    return True;     
	def attack(self):
		self.count =0
		#attackSuccessList = []
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
                            rescode = self.makeRequestLink(url,parameters,requestType)
                            print rescode
                	    if rescode == 302 or rescode == 303:
                                print "CSRF possible in "+str(self.count)
				self.writeToOutputFile(reqObj)
                                #attackSuccessList.append(self.count)
                	    else:
                		print "CSRF not possible in "+str(self.count)
                             
			else:
			    	 
                            print "Checking CSRF in Forms"
                            if not(self.checkValidForm(referer,url,method,action,parameters)):
                                print "CSRF not possible as invalid form request"
                                continue;    
		 	    #(url,method,referer,action,requestType,parameters) = self.getRequestData(reqObj)	
		 	    res1 = self.loginnotlogincheck(referer,url,action,requestType)
		 	    if res1 == True:
		 		    res2 = self.loginlogincheck(referer,url,action,requestType)
		 		    if res2 == True:
					    if (method.upper() == "POST"):
		 			        (rstatus, res3) = self.makeRequest(url,method,parameters,"True")
		 			        if rstatus == True:
		 				    print "CSRF possible in "+str(self.count)
                                                    self.writeToOutputFile(reqObj)
                                                    #attackSuccessList.append(self.count) 
		 			        else:
		 				    print "CSRF not possible in "+str(self.count)+" condition 3 fails"
                                            
                                            else:
                                                    rescode = self.makeRequestLink(url,parameters,requestType)
                                                    print str(rescode)
                	                            if rescode == 302 or rescode == 303:
                                                        print "CSRF possible in "+str(self.count)
                                                        self.writeToOutputFile(reqObj)
                                                        #attackSuccessList.append(self.count)
                	                            else:
                		                        print "CSRF not possible in "+str(self.count)               
		 		    else:
		 			    print "CSRF not possible in "+str(self.count)+" condition 2 fails"
		 	    else:
		 		    print "CSRF not possible in "+str(self.count)+" condition 1 fails"
                    
    
        def step3End(self):
             self.writeoutputFileTail()
             self.fileobj.close()
             self.outputfileobj.close()

if __name__ == "__main__":

	obj = AttackApplication("stage2Output.json","stage3Output.json")
	obj.attack()
        obj.step3End()


