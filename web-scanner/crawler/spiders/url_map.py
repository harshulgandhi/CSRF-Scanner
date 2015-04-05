
'''
This  class maintains a list of all the 
urls visited by crawler. Each of the url
has an associated flag which is set to 1
if that url has been visited
'''
class UrlMap():
	urlMap = {}

	def addUrl(self,url):
		self.urlMap[url] = 1

	def printMap(self):
		print "\n************************************************************************************\n"
		for key in self.urlMap:
			print key +" : "+str(self.urlMap[key])

		print "\n************************************************************************************\n"

	def getUrlStatus(self,url):
		if url in self.urlMap:
			return self.urlMap[url]
		else:
			return 0

