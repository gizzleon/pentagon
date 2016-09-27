# -*- coding: utf-8 -*-

import wx
import csv
from pentagon import *
from wx.lib.wordwrap import wordwrap
import threading
import sys
import time
reload(sys)
#sys.setdefaultencoding( "utf-8" )

class PentagonThread(threading.Thread):
	def __init__(self, window):
		threading.Thread.__init__(self)
		self.window = window
		result = Initiate()
		if result.state == False:
			wx.CallAfter(self.window.ShowMessage, "-----\n初始化失败\n" + result.errorMsg)
		else:
			wx.CallAfter(self.window.ShowMessage, "-----\n初始化成功!可以开始选课了")
			wx.CallAfter(self.window.UpdateCaptcha)
		self.state = result.state
		self.errorMsg = result.errorMsg
		
	def start(self, ID, password, captcha, semester, interval, keywordsInType):
		self.ID = ID
		self.password = password
		self.captcha = captcha
		self.semester = semester
		self.interval = interval
		self.keywordsInType = keywordsInType
		threading.Thread.start(self)
	def run(self):
		wx.CallAfter(self.window.ShowMessage, "启动!")
		
		result = Login(self.ID, self.password, self.captcha)
		self.handleResult(result, "登陆成功")
		if result.state == False:		
			wx.CallAfter(self.window.ShowMessage, "选课结束\n\n\n")
			self.window.thread = PentagonThread(self.window)
			self.window.buttonLogin.Enable()
			return
		
		result = SwitchSemester(self.semester, result.url)
		self.handleResult(result, "已成功切换到学期" + str(self.semester))
		if result.state == False:
			wx.CallAfter(self.window.ShowMessage, "选课结束\n\n\n")
			self.window.thread = PentagonThread(self.window)
			self.window.buttonLogin.Enable()
			return

		
		# find recommendations
		recommendations = []
		if self.keywordsInType.has_key('tuijian') == True:
			if '*' in self.keywordsInType['tuijian']:
				selectAll = True
			else:
				selectAll = False
			result = FindRecommendations(result.text, selectAll, self.keywordsInType['tuijian'])
			if result.state == True:
				recommendations = result.courses
			else:
				wx.CallAfter(self.window.ShowMessage, result.errorMsg)
		
		for course in recommendations:
			if course[3] == False:
				recommendations.remove(course)
		
		for i in range(10000):
			wx.CallAfter(self.window.ShowMessage, "第"+str(i+1)+"回合选课:")
			time.sleep(self.interval)
			for key in self.keywordsInType:
				if key == 'tuijian':
					if len(recommendations) != 0:
						wx.CallAfter(self.window.ShowMessage, "可服推"+str(len(recommendations))+"门")
					selectedCourse = []
					for course in recommendations:
						result = SelectRecommendation(course)
						self.handleResult(result, '成功选择', course[1])
						if result.state == True:
							selectedCourse.append(course)
					for course in selectedCourse:
						recommendations.remove(course)
				else:
					if '#' in self.keywordsInType[key]:
						continue
					elif '*' in self.keywordsInType[key]:
						selectAny = True
					else:
						selectAny = False
					result = FindOthers(key, selectAny, self.keywordsInType[key])
					self.handleResult(result, key + ':找到' + str(len(result.courses)) + '门可选课程')
					if result.state == False:
						continue
					courses = result.courses
					for course in courses:
						result = SelectOther(key, course)
						self.handleResult(result, '成功选择', course)
						if result.state == True:
							self.keywordsInType[key].append('#')
							break
		
		wx.CallAfter(self.window.ShowMessage, "选课结束\n\n\n")
		self.window.thread = PentagonThread(self.window)
		self.window.buttonLogin.Enable()
				
		
	def handleResult(self, result, successMsg, course = ''):
		if result.state == False:
			wx.CallAfter(self.window.ShowMessage, course + result.errorMsg)
		else:
			wx.CallAfter(self.window.ShowMessage, course + successMsg)

		
		


class PentagonFrame(wx.Frame):
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, title = title)
		
		mainPanel = wx.Panel(self, wx.ID_ANY)
		
		# ---- LEFT SIZER ---
		self.panelLeft = wx.Panel(mainPanel, wx.ID_ANY)

		# Student ID
		sizerID = wx.BoxSizer(wx.HORIZONTAL)
		sizerID.Add(wx.StaticText(self.panelLeft, label = "Student ID:", size = (70, -1)), 2, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
		self.textID = wx.TextCtrl(self.panelLeft)
		sizerID.AddSpacer((5,0))
		sizerID.Add(self.textID, 5, wx.EXPAND | wx.ALL, 2)
		
		# Password
		sizerPassword = wx.BoxSizer(wx.HORIZONTAL)
		sizerPassword.Add(wx.StaticText(self.panelLeft, label = "Password:", size = (70,-1)), 2, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
		self.textPassword = wx.TextCtrl(self.panelLeft, style = wx.TE_PASSWORD)
		sizerPassword.AddSpacer((5,0))
		sizerPassword.Add(self.textPassword, 5, wx.EXPAND | wx.ALL, 2)
		
		# Captcha
		sizerCaptcha = wx.BoxSizer(wx.HORIZONTAL)
		captchaBmp = wx.Image('code.jpg', wx.BITMAP_TYPE_JPEG).Scale(63, 30).ConvertToBitmap()
		self.bitmapCaptcha = wx.StaticBitmap(self.panelLeft, bitmap = captchaBmp)
		self.textCaptcha = wx.TextCtrl(self.panelLeft, size = (70, -1))
#		self.checkAutoRecognize = wx.CheckBox(self.panelLeft, label = "auto recg")
		sizerCaptcha.Add(self.bitmapCaptcha, 0, wx.ALIGN_CENTER | wx.ALL, 2)
		sizerCaptcha.AddSpacer((5, 0))
		sizerCaptcha.Add(self.textCaptcha, 1, wx.ALIGN_CENTER | wx.ALL, 2)	
#		sizerCaptcha.AddSpacer((5, 0))
#		sizerCaptcha.Add(self.checkAutoRecognize, 0, wx.ALIGN_CENTER | wx.ALL, 2)
		
	
		# Setting - semester and interval
		sizerSetting = wx.BoxSizer(wx.HORIZONTAL)
		# Semester
		sizerSetting.Add(wx.StaticText(self.panelLeft, label = "Semester:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)	
		semesterList = ['1', '2', '3']
		self.choiceSemester = wx.Choice(self.panelLeft, wx.ID_ANY, choices = semesterList)
		self.choiceSemester.SetMinClientSize((40, -1))		
		sizerSetting.AddSpacer((5, 0))	
		sizerSetting.Add(self.choiceSemester, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 2)		
		sizerSetting.AddSpacer((15, 0))
		# Interval
		sizerSetting.Add(wx.StaticText(self.panelLeft, label = "Interval(0.1~10):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
		sizerSetting.AddSpacer((5, 0))		
		self.textInterval = wx.TextCtrl(self.panelLeft)
		self.textInterval.SetMinClientSize((50, -1))
		sizerSetting.Add(self.textInterval, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 2)

		
		#Buttons
		self.buttonLogin = wx.Button(self.panelLeft, label = "Login", size = (80,-1))
		self.buttonExit = wx.Button(self.panelLeft, label = "Exit", size = (80,-1))
		sizerButton = wx.BoxSizer(wx.HORIZONTAL)
		sizerButton.Add(self.buttonLogin, 1, wx.FIXED_MINSIZE)
		sizerButton.AddSpacer((15,0))
		sizerButton.Add(self.buttonExit, 1, wx.FIXED_MINSIZE)
		
		# Status Box
		self.textStatus = wx.TextCtrl(self.panelLeft, style = wx.TE_MULTILINE)
		self.textStatus.SetEditable(False)
		
		# Button - setting panel control
		self.buttonSettingSwitcher = wx.Button(self.panelLeft, label = "Collapse<<<", size = (100, -1))		
		
		#sizer
		sizerLeft = wx.BoxSizer(wx.VERTICAL)
		sizerLeft.Add(sizerID,0,wx.ALIGN_CENTER | wx.ALL, 2)
		sizerLeft.Add(sizerPassword,0,wx.ALIGN_CENTER | wx.ALL, 2)
		sizerLeft.Add(sizerCaptcha, 0, wx.ALIGN_CENTER | wx.ALL, 2)
		sizerLeft.Add(sizerSetting, 0, wx.ALIGN_CENTER | wx.ALL, 2)
		sizerLeft.Add(sizerButton,0,wx.ALIGN_CENTER | wx.ALL, 5)
		sizerLeft.Add(self.textStatus, 100, wx.ALL | wx.EXPAND, 5)
		sizerLeft.Add(self.buttonSettingSwitcher, 1, wx.ALIGN_RIGHT | wx.ALL, 5)
		sizerLeft.AddSpacer((0, 3))
		
		#binding events
		self.Bind(wx.EVT_BUTTON, self.Login, self.buttonLogin)
		self.Bind(wx.EVT_BUTTON, self.Exit, self.buttonExit)
		self.Bind(wx.EVT_BUTTON, self.SwitchSettingPanel, self.buttonSettingSwitcher)
#		self.Bind(wx.EVT_CHECKBOX, self.SwitchManualCaptcha, self.checkAutoRecognize)
		
		
		self.panelLeft.SetSizer(sizerLeft)


		# ---- RIGHT SIZER ---
		self.panelRight = wx.Panel(mainPanel, wx.ID_ANY)

		# Buttons - Operation
		sizerButtons = wx.BoxSizer(wx.HORIZONTAL)
		self.buttonImport = wx.Button(self.panelRight, label = "Import", size = (70, -1))
		self.buttonExport = wx.Button(self.panelRight, label = "Export", size = (70, -1))
#		self.buttonApply = wx.Button(self.panelRight, label = "apply", size = (70, -1))
		self.buttonClear = wx.Button(self.panelRight, label = "Clear", size = (70, -1))
		self.buttonAbout = wx.Button(self.panelRight, label = "About", size = (70, -1))
		sizerButtons.Add(self.buttonImport, 1, wx.FIXED_MINSIZE | wx.ALL, 2)
		sizerButtons.AddSpacer((5,0))
		sizerButtons.Add(self.buttonExport, 1, wx.FIXED_MINSIZE | wx.ALL, 2)
#		sizerButtons.Add(self.buttonApply, 1, wx.FIXED_MINSIZE | wx.ALL, 2)
		sizerButtons.AddSpacer((5,0))
		sizerButtons.Add(self.buttonClear, 1, wx.FIXED_MINSIZE | wx.ALL, 2)		
		sizerButtons.AddSpacer((5,0))
		sizerButtons.Add(self.buttonAbout, 1, wx.FIXED_MINSIZE | wx.ALL, 2)		
		

		# Course List
		self.index = 0
		self.listCtrl = wx.ListCtrl(self.panelRight, style = wx.LC_REPORT|wx.BORDER_SUNKEN)
#		self.listCtrl.InsertColumn(0, "semester")
		self.listCtrl.InsertColumn(0, "Type")
		self.listCtrl.InsertColumn(1, "Keyword")
#		self.listCtrl.InsertColumn(3, "course code")
#		self.listCtrl.SetColumnWidth(0, 70)
		self.listCtrl.SetColumnWidth(0, 120)
		self.listCtrl.SetColumnWidth(1, 200)
#		self.listCtrl.SetColumnWidth(3, 160)
		
		# Semester
#		sizerSemester = wx.BoxSizer(wx.VERTICAL)
#		sizerSemester.Add(wx.StaticText(self.panelRight, label = "Semester"))	
#		semesterList = ['1', '2', '3']
#		self.choiceSemester = wx.Choice(self.panelRight, wx.ID_ANY, choices = semesterList)
#		self.choiceSemester.SetMinClientSize((60, -1))		
#		sizerSemester.Add(self.choiceSemester, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 2)
		
		# Course Type		
		sizerType = wx.BoxSizer(wx.VERTICAL)
		sizerType.Add(wx.StaticText(self.panelRight, label = "Type"))
		typeList = ['tuijian', 'renwen', 'jingguan', 'ziran', 'seminar']
		self.choiceType = wx.Choice(self.panelRight, wx.ID_ANY, choices = typeList)
		self.choiceType.SetMinClientSize((80, -1))
		sizerType.Add(self.choiceType, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 2)
		
		# Course Code
#		sizerCode = wx.BoxSizer(wx.VERTICAL)
#		sizerCode.Add(wx.StaticText(self.panelRight, label = "Code"))
#		self.textCode = wx.TextCtrl(self.panelRight,)
#		sizerCode.Add(self.textCode, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 2)		
		
		# Course Name
		sizerName = wx.BoxSizer(wx.VERTICAL)
#		sizerName.SetMinSize((200, -1))
		sizerName.Add(wx.StaticText(self.panelRight, label = "Keyword"))
		self.textName = wx.TextCtrl(self.panelRight)
		self.textName.SetMinClientSize((150, -1))
		sizerName.Add(self.textName, 1, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
		
		# buttons in editbar
		self.buttonAdd = wx.Button(self.panelRight, id = wx.ID_ADD, label = "Add", size = (70, -1))
		self.buttonDelete = wx.Button(self.panelRight, id = wx.ID_DELETE, label = "Delete", size = (70, -1))
		self.buttonDelete.Disable()
		
		# Edit Bar
		sizerEdit = wx.BoxSizer(wx.HORIZONTAL)
		sizerEdit.Add(sizerType, 0, wx.ALIGN_BOTTOM | wx.ALL, 2)
		sizerEdit.Add(sizerName, 0, wx.ALIGN_BOTTOM | wx.ALL, 2)
		sizerEdit.Add(self.buttonAdd, 0, wx.ALIGN_BOTTOM | wx.ALL, 2)
		sizerEdit.Add(self.buttonDelete, 0, wx.ALIGN_BOTTOM | wx.ALL, 2)
		
		# sizer
		sizerRight = wx.BoxSizer(wx.VERTICAL)		
		sizerRight.Add(sizerButtons, 1, wx.ALL | wx.ALIGN_CENTER | wx.FIXED_MINSIZE, 5)
		sizerRight.Add(self.listCtrl, 50, wx.ALL|wx.EXPAND, 5)  # 50 - ensure the listctrl would expand	
		sizerRight.Add(sizerEdit, 0, wx.ALL | wx.ALIGN_CENTER , 5)
		
		# Events Binding
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.SelectEntry, self.listCtrl)
		self.Bind(wx.EVT_BUTTON, self.ImportFromFile, self.buttonImport)
		self.Bind(wx.EVT_BUTTON, self.ExportToFile, self.buttonExport)
		self.Bind(wx.EVT_BUTTON, self.ClearList, self.buttonClear)
		self.Bind(wx.EVT_BUTTON, self.ShowAbout, self.buttonAbout)
		self.Bind(wx.EVT_BUTTON, self.AddEntry, self.buttonAdd)
		self.Bind(wx.EVT_BUTTON, self.DeleteEntry, self.buttonDelete)
		
		self.panelRight.SetSizer(sizerRight)

		# ---- MAIN PANEL SETTING ----
	
		mainSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainPanel.SetSizer(mainSizer)	
		mainSizer.Add(self.panelLeft, 1, wx.ALL | wx.ALIGN_CENTER, 2)
		mainSizer.Add(self.panelRight, 0, wx.ALL | wx.ALIGN_CENTER, 2)
		self.SetSize((900, 500))
		self.SetMinSize((800, 350))
		self.Show()
		# ---- Start Thread ----
		# initiating the thread here may froze the program for seconds
		# any better solution???
		self.thread = PentagonThread(self)
		
	def UpdateCaptcha(self, captchaPath = 'code.jpg'):
		captchaBmp = wx.Image(captchaPath, wx.BITMAP_TYPE_JPEG).Scale(63, 30).ConvertToBitmap()
		self.bitmapCaptcha.SetBitmap(captchaBmp)
	def ShowMessage(self, message):
		print message
		self.textStatus.AppendText(message.decode('utf-8') + '\n')
		
	def CheckEntry(self):
		if self.choiceType.GetStringSelection() == "":
			return (False, "Please select Type!")
		if self.textName.GetValue() == "":
			return (False, "Please enter the keyword")
		return (True, "Success")	
		
	def GetCourseList(self):
		courseList = []
		for i in range(self.index):
			courseInfo = []
			for j in range(2):
				courseInfo.append(self.listCtrl.GetItem(i, j).GetText())  #solve the encoding problem
			courseList.append(courseInfo)
		return courseList
	
	def ParseCourseList(self):
		courseList = []
		for i in range(self.index):
			course = []
			for j in range(2):  # get column?
				course.append(self.listCtrl.GetItem(i, j).GetText().encode('utf-8'))
				if course[j] == '': # an empty string
					break
			else:
				courseList.append(course)
		coursesInType = {}
		for course in courseList:
			if coursesInType.has_key(course[0]) == False:
				coursesInType[course[0]] = []
			coursesInType[course[0]].append(course[1])
		for key in coursesInType:
			courses = coursesInType[key]
			courses = list(set(courses)) # eliminate repeated courses
			coursesInType[key] = courses
			
		return coursesInType
		
	def CheckLoginInfo(self):
		ID = self.textID.GetValue()
		if ID == '':
			return (False, u'请输入一卡通号')
		password = self.textPassword.GetValue()
		if password == '':
			return (False, u'请输入密码')
		captcha = self.textCaptcha.GetValue()
		if captcha == '':
			return (False, u'请输入验证码')
		semester = self.choiceSemester.GetStringSelection()
		if semester == '':
			return (False, u'请选择学期')
		interval = self.GetInterval()
		if interval == -1:
			return (False, u'请输入合法的数字')
		if interval == '':
			return (False, u'请输入间隔时间')
		return (True, '')
		
	def GetInterval(self):
		interval = self.textInterval.GetValue()
		try:
			interval = float(interval)
		except:
			return -1
		if interval > 10:
			return 10
		if interval < 0.1:
			return 0.1
		return interval
		
	# ---- event handlers	 ----
	def Login(self, event):
		state = self.CheckLoginInfo()
		if state[0] == False:
			wx.MessageBox(state[1],"Input Error")
			return
		ID = self.textID.GetValue()
		password = self.textPassword.GetValue()
		captcha = self.textCaptcha.GetValue()
		semester = self.choiceSemester.GetStringSelection()
		interval = self.GetInterval()
		coursesInType = self.ParseCourseList()
		self.buttonLogin.Disable()
		self.thread.start(ID, password, captcha, semester, interval, coursesInType)
#		self.thread = PentagonThread(self) # abandon the former thread and create a new one

	def Exit(self, event):
		self.Close(False)

	def SwitchManualCaptcha(self, event):
		status = self.checkAutoRecognize.IsChecked()
		if status == True:
			self.textCaptcha.Disable()
		else:
			self.textCaptcha.Enable()

	def SwitchSettingPanel(self, event):
		space = self.panelRight.GetSize()[0] + 4
		if self.panelRight.IsShown() == False:
			size = (self.GetSize()[0] + space, self.GetSize()[1])
			self.panelRight.Show()
			self.buttonSettingSwitcher.SetLabel('Collapse<<<')
			self.SetSize(size)
			self.SetMinSize((800, 350))
		else:
			size = (self.GetSize()[0] - space, self.GetSize()[1])
			self.panelRight.Hide()
			self.buttonSettingSwitcher.SetLabel('Expand>>>')
			self.SetMinSize((800 - space, 350))
			self.SetSize(size)		

	def SelectEntry(self, event):	
		self.buttonDelete.Enable()
		
	def AddEntry(self, event):
		status = self.CheckEntry()
		if status == False:
			wx.MessageBox(u"请输入完整信息","Input Error")
			return
		self.listCtrl.InsertStringItem(self.index, self.choiceType.GetStringSelection())
		self.listCtrl.SetStringItem(self.index, 1, self.textName.GetValue())
		self.index += 1
		
	def DeleteEntry(self, event):
		selected = self.listCtrl.GetNextSelected(-1)
		while selected != -1:
			self.listCtrl.DeleteItem(selected)
			selected = self.listCtrl.GetNextSelected(-1)
			self.index -= 1
		self.buttonDelete.Disable()
	
	def ImportFromFile(self, event):
		openDlg = wx.FileDialog(None, style = wx.FD_OPEN, wildcard = "CSV Files (*.csv)|*.csv")
		openDlg.ShowModal()
		filePath = openDlg.GetPath()
		openDlg.Destroy()
		
		try:
			print "loading the file"
			csvfile = file(filePath, 'rb')
		except Exception, e:
			if e.errno == 22:
				self.ShowMessage('无效地址')
			else:
				print e
				self.ShowMessage(str(e))
			return
		
		try:
			print "ready to write"
			self.listCtrl.DeleteAllItems()
			self.index = 0
			reader = csv.reader(csvfile)
			for row in reader:
				self.listCtrl.InsertStringItem(self.index, row[0])
				self.listCtrl.SetStringItem(self.index, 1, row[1].decode('utf-8'))
				self.index += 1
		except Exception, e:
			print e
		finally:
			csvfile.close()
	
	def ExportToFile(self, event):
		# File Dialog
		saveDlg = wx.FileDialog(None, style = wx.FD_SAVE, wildcard = "CSV Files (*.csv)|*.csv")		
		saveDlg.ShowModal()
		filePath = saveDlg.GetPath()
		print "file path get"
		saveDlg.Destroy()
		
		try:
			print "loading the file..."
			csvfile = file(filePath, 'wb')
		except Exception, e:
			if e.errno == 22:
				self.ShowMessage("无效地址")
			else:
				print e
				self.ShowMessage(str(e))
			return
		try:
			print "ready to write the file"
			writer = csv.writer(csvfile)
			
			for i in range(self.index):
				courseInfo = []
				for j in range(2):
					courseInfo.append(self.listCtrl.GetItem(i, j).GetText().encode('utf-8'))  #solve the encoding problem
#				print courseInfo
				writer.writerow(courseInfo)
		except:
			self.ShowMessage('写入失败')
		finally:
			csvfile.close()
	def ClearList(self, event):
		self.listCtrl.DeleteAllItems()
		self.index = 0
		
	def ShowAbout(self, event):
		info = wx.AboutDialogInfo()
		info.Name = 'Pentagon'
		info.Version = '0.9'
		info.Description = wordwrap('Please refer to the link below for more information and instructions about this program.', 300, wx.ClientDC(self))
		info.WebSite = ('http://www.baidu.com', 'Github')
		wx.AboutBox(info)
	
if __name__ == "__main__":
	app = wx.App(False)
	frame = PentagonFrame(None, "Pentagon")
	app.MainLoop()
	app.Destroy()