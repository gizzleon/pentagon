# -*- coding: utf-8 -*-

"""
This module provides methods for SEU-JWC related operations.
This module was adpated from seu_jwc_fker.(GITHUB LINK HERE)
"""

import HTMLParser
import urlparse
import urllib
import urllib2
import cookielib
import string
import re
import time
import sys

class Agent(object):
	'''
	This class is used for packing return value of the methods below together
	'''
	def __init__(self):
		self.state = False
		self.text = ''
		self.errorMsg = ''
		self.url = ''
		self.img = None
		self.courses = []
		

def PostData(postUrl, headers, postData, timeout = 5, failtimes = 10):

	result = Agent()
	postData = urllib.urlencode(postData)
	request = urllib2.Request(postUrl, postData, headers)
	for i in range(failtimes):
		try:
			response = urllib2.urlopen(request, timeout = timeout)
			result.text = response.read()
			result.url = response.geturl()
			result.state = True
			break
		except Exception, e:
			result.errorMsg = e.message
#			print 'post failed'
			continue
	else:
		result.state = False
	return result
	
def GetData(getUrl, header, getData, timeout = 5, failtimes = 10):
	result = Agent()
	getData = urllib.urlencode(getData)
	request = urllib2.Request(getUrl, getData, header)
	for i in range(failtimes):
		try:
			response = urllib2.urlopen(request, timeout = timeout)
			result.text = response.read()
			result.url = response.geturl()
			result.state = True
			break
		except Exception, e:
			result.errorMsg = e.message
#			print 'get failed'
			continue
	else:
		result.state = False
	return result
		
def GetCaptcha(path = 'code.jpg', timeout = 5, failtimes = 10):
	result = Agent()
	for i in range(failtimes):
		try:
			result.img = urllib2.urlopen('http://xk.urp.seu.edu.cn/jw_css/getCheckCode', timeout = timeout)
			f = open(path, 'wb')
			f.write(result.img.read())
			f.close()
			result.state = True
			break
		except Exception, e:
			result.errorMsg = e.message
			continue
	else:
		result.state = False
	return result

def Initiate(timeout = 5):
	'''this method should be called before login'''
	result = Agent()
	# set cookies
	cj = cookielib.LWPCookieJar()
	cookie_support = urllib2.HTTPCookieProcessor(cj)
	opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
	urllib2.install_opener(opener)
	
	# open the login page. necessary?
	try:
		urllib2.urlopen('http://xk.urp.seu.edu.cn/jw_css/system/showLogin.action', timeout = timeout)
	except Exception, e:
		result.state = False
		result.errorMsg = e.message
		if e.message == '': # this can happen sometime
			result.errorMsg = 'an unknown error occured'
		return result
	
	result = GetCaptcha('code.jpg', timeout = timeout)
	if result.state == False:
		return result
	result.state = True
	return result

def Login(userID, password, captcha, timeout = 5, failtimes = 10):
	# need to call Initiate() first
	posturl = 'http://xk.urp.seu.edu.cn/jw_css/system/login.action' 
	header ={   
		'Host' : 'xk.urp.seu.edu.cn',   
		'Proxy-Connection' : 'keep-alive',
		'Origin' : 'http://xk.urp.seu.edu.cn',
		'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
		'Referer' : 'http://xk.urp.seu.edu.cn/jw_css/system/login.action'
		}
	data = {
		'userId' : userID,
		'userPassword' : password,  
		'checkCode' : captcha,
		'x' : '33',
		'y' : '5'
		}
	result = PostData(posturl, header, data, timeout = timeout, failtimes = failtimes)
	if result.state == False:
		return result
	
	if (result.text.find("选课批次") != -1):
		# success
		function = re.search(r'onclick="changeXnXq.*\)"', result.text) # find the function whose parameters are desired
		function = function.group()
		parameters = re.search(r"'(.*)','(.*)','(.*)'\)", function) # fetch parameters for url
		result.url = "http://xk.urp.seu.edu.cn/jw_css/xk/runXnXqmainSelectClassAction.action?Wv3opdZQ89ghgdSSg9FsgG49koguSd2fRVsfweSUj=Q89ghgdSSg9FsgG49koguSd2fRVs&selectXn=" + parameters.group(1) + "&selectXq=" + parameters.group(2) + "&selectTime=" + parameters.group(3)
	else:
		result.state = False
		result.errorMsg = re.search(r'id="errorReason".*?value="(.*?)"', result.text).group(1).decode('utf-8')
	return result
	
def SwitchSemester(semester, url, timeout = 5, failtimes = 10):
	# url comes from the return value of method "Login"
	time.sleep(5)
	getUrl = re.sub('selectXq=.', 'selectXq='+str(semester), url)
	header = {  'Host' : 'xk.urp.seu.edu.cn',
                'Proxy-Connection' : 'keep-alive',
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',        
    }
	data = {}

	result = GetData(getUrl, header, data)
	# print result.text
	if result.state == True:
		if result.text.find("数据异常") != -1: # unvalid semester
			result.state = False
			result.errorMsg = "目前无法选择学期" + str(semester)
			result.errorMsg = result.errorMsg.decode('utf-8')
	return result

def FindRecommendations(page, selectAll = False, wantedCourse = [], timeout = 5, failtimes = 10):
	'''
		Return a list including all recommended courses if selectAll is True,
		or return a list including wanted course only if selectAll is False.
		The parameter 'wantedCourse' is a list containing the keyword of each wanted course.
	'''
	# ready to select 
	pattern = "<button.*?onclick=\"selectThis\('(.*?)','(.*?)','(.*?)'" # '<button' is used for the excluding selected courses
	recommendedCourses = []
	if selectAll == True:
		pattern = re.compile(pattern)
		pos = 0
		# find all courses available
		parameters = pattern.search(page, pos)
		while parameters:
			pos = parameters.end()
			course = [parameters.group(1), parameters.group(2), parameters.group(3), 'disabled' not in parameters.group()] # forth element indicates the availability
			recommendedCourses.append(course)
			parameters = pattern.search(page, pos)
	else:
		for keyword in wantedCourse:
			parameters = re.search(keyword + '.*?' + pattern, page, re.S)
			if parameters != None:  # in case of unvalid keyword
				course = [parameters.group(1), parameters.group(2), parameters.group(3), 'disabled' not in parameters.group()]
				recommendedCourses.append(course)
	result = Agent()
	if len(recommendedCourses) != 0:
		result.state = True
		result.courses = recommendedCourses
	else:
		result.state = False
		result.errorMsg = '没有可以服推的课程'
	return result


def SelectRecommendation(course, timeout = 5, failtimes = 10):
	'''select ONE recommended course.'''
	# ready to select 
	headers = { 'Host' : 'xk.urp.seu.edu.cn',
                        'Proxy-Connection' : 'keep-alive',
                        'Content-Length' : '2',
                        'Accept' : 'application/json, text/javascript, */*',
                        'Origin':'http://xk.urp.seu.edu.cn',
                        'X-Requested-With': 'XMLHttpRequest',
                        'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
    }
	data = {'{}':''
	}
	# is it necessary to create a class for courses?
	if course[3] == True:
		postUrl = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_jxbbh='+course[1]+'&select_xkkclx='+course[2]+'&select_jhkcdm='+course[0]
		result = PostData(postUrl, headers, data, timeout = timeout, failtimes = failtimes)
		if result.state == True:
			if result.text.find('isSuccess":"false') != -1: # actually failed
				result.state = False
				result.errorMsg = re.search(r'errorStr":"(.*?)"', result.text).group(1)
			else:
				course[3] = False
	else:
		result = Agent()
		result.state = False
		result.errorMsg = ''
	return result


typeList = {
		'renwen' : ['00034','rwskl','45'],
		'jingguan' : ['00035','jjygll','46'],
		'ziran' : ['00036','zl','47'],
		'seminar' : ['00033','sem','44']
	}

def FindOthers(courseType, selectAny = True, wantedCourses = [], timeout = 5, failtimes = 10):
	if courseType in typeList:
		type = typeList[courseType]
	else:
		result = Agent()
		result.state = False
		result.errorMsg = 'not a valid type ' + courseType
		return result
	getUrl = 'http://xk.urp.seu.edu.cn/jw_css/xk/runViewsecondSelectClassAction.action?select_jhkcdm='+type[0]+'&select_mkbh='+type[1]+'&select_xkkclx='+type[2]+'&select_dxdbz=0'
	# print getUrl
	header = {
        'Host' : 'xk.urp.seu.edu.cn',
        'Proxy-Connection' : 'keep-alive',
        'Accept' : 'application/json, text/javascript, */*',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
    }   
	data = {}
	result = GetData(getUrl, header, data, timeout = timeout, failtimes = failtimes)
	if result.state == False:
		result.errorMsg += '/n failed to open the page'
		return result
	pattern = '"8%" id="(.*?)" align'
	
	courses = []
	if selectAny == True:
		if re.search('已选(.{0,200})align=\"', result.text, re.S) != None: # already selected one
			result.state = False
			result.errorMsg = "已经选到一门课了"
		else:
			courses = re.findall(pattern, result.text)
			# print result.text
			# any better way to eliminate confliting courses???
			if len(courses) == 0:
				result.state = False
				result.errorMsg = '没有可以选择的课程'
			else:
				result.state = True
				result.courses = courses
	else:
		for keyword in wantedCourses:
			id = re.search(keyword + '.*?' + pattern, result.text, re.S)
			if id != None:
				courses.append(id.group(1)) # the second empty string is for future error message
		if len(courses) == 0:
			result.state = False
			result.errorMsg = '没找到符合要求的课程'
		else:
			result.state = True
			result.courses = courses
	return result
	

def SelectOther(courseType, course, timeout = 5, failtimes = 10):
	'''select ONE course in 'other courses' '''
	if courseType in typeList:
		type = typeList[courseType]
	else:
		result = Agent()
		result.state = False
		result.errorMsg = courseType + '不是有效的类别'
		return result	
	headers = { 
        'Host' : 'xk.urp.seu.edu.cn',
    	'Proxy-Connection' : 'keep-alive',
        'Content-Length' : '2',
        'Accept' : 'application/json, text/javascript, */*',              
		'Origin':'http://xk.urp.seu.edu.cn',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
    }
	data = {
            '{}':''
    }
	postUrl = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_jxbbh='+course+'&select_xkkclx='+type[2]+'&select_jhkcdm='+type[0]+'&select_mkbh='+type[1]
	result = PostData(postUrl, headers, data, timeout = timeout, failtimes = failtimes)
	# print result.text
	if result.state == True:
		if result.text.find('isSuccess":"false') != -1: # actually failed
			result.state = False
			result.errorMsg = re.search(r'errorStr":"(.*?)"', result.text).group(1)
		else:
			result.state = True
	return result
	