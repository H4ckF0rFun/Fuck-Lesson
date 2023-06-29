import time
import requests
import json
from bs4 import BeautifulSoup
import random
import threading
import os
import re
import hashlib
import getpass

class Uims:
    def __init__(self,session):
        self.s = session
        self.login_success_headers = {
            'Host': 'uims.jlu.edu.cn',
            'Origin': 'https://uims.jlu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://uims.jlu.edu.cn/ntms/index.do',
        }
        self.ignore_not_start = True
        self.Selecting={}
        self.mutex = threading.Lock()
        self.stuId = ''
        self.splanId = 0
        self.termId = 0

        pass

    def login(self,username,password):
        verification_code = 'https://uims.jlu.edu.cn/ntms/open/get-captcha-image.do?s='+str(random.random())
        login_auth = "https://uims.jlu.edu.cn/ntms/j_spring_security_check"
        #下载验证码
        headers = {
            'Host': 'uims.jlu.edu.cn',
            "Referer": "https://uims.jlu.edu.cn/ntms/",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62",
            "Origin": "https://uims.jlu.edu.cn"
        }

        print("[*]downloading the verification code...")
        verification_code_res = self.s.get(url = verification_code,headers=headers)
        with open("./vcode.png","wb") as file:
            file.write(verification_code_res.content)
        
        os.startfile("vcode.png")
        #让用户自己输入验证码
        print("[#]please input vcode >",end='')
        vcode = str(input()) 
        #登录
        print("[*]login....")
        #表单方式提交,不是json

        payload = {
            "username":username,
            "password":hashlib.md5(("UIMS"+username+password).encode('utf-8')).hexdigest(),
            "mousePath":"",
            "vcode": vcode
        }
        cookies = {
            "loginPage":"userLogin.jsp",
            "alu":username,
            "pwdStrength":"3"
        }
        headers={
            'Host': 'uims.jlu.edu.cn',
            'Origin': 'https://uims.jlu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://uims.jlu.edu.cn/ntms/userLogin.jsp',
        }
        response = self.s.post(data=payload,url = login_auth,headers=headers,cookies=cookies)
        #登录成功会重定向到index.do
        if response.status_code == 200 and response.url[-9:] == "/index.do":
            print("[#]login success!")
            #获取stuid
            self.stuId = self.get_my_info()["value"][0]["studId"]
            #获取 splanId 和term id
            try:
                SelInfo = self.get_sel_lesson_info()
                print("====================================================================")
                print("\t\t@start time: %s"%SelInfo["value"][0]["currStartTime"])
                print("\t\t@stop  time: %s"%SelInfo["value"][0]["currStopTime"])
                print("\t\t@title     : %s"%SelInfo["value"][0]["title"])

                self.splanId = SelInfo["value"][0]["splanId"]
                self.termId = SelInfo["value"][0]["teachingTerm"]["termId"]
            except:
                print("当前无选课信息")
                exit(0)
                pass
            return True
        else:
            print("[x]login failed!")
            return False

    def get_my_info(self):
        url = "https://uims.jlu.edu.cn/ntms/service/res.do"
        payload={
            "tag":"studInfoAll@student",
            "branch":"self",
            "params":{}
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        return json.loads(response.text)

    #获取选课信息
    def get_sel_lesson_info(self):
        url ="https://uims.jlu.edu.cn/ntms/service/res.do"
        payload = {
            "tag":"common@selectPlan",
            "branch":"byStudentSet",
            "params":{
                "studId":self.stuId
            }
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        return json.loads(response.text)

    #打印全部课程(供选择的课)
    def PrintAllLessons(self):
        url = "https://uims.jlu.edu.cn/ntms/service/res.do"
        payload={
            "type":"search",
            "tag":"apl@gxSelect",
            "branch":"default",
            "params":{
                #"mooc":"Y",                     #慕课在线课程
                "campus":"1401",                 #应该是校区,1401貌似是前卫南区
                "splanId":self.splanId,               #这里可能需要修改
                "termId":self.termId                  #这里可能需要修改
                },
            "orderBy":"lesson.courseInfo.courName"
        }

        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        LessonList =  json.loads(response.text)["value"]

        print ("%-11s %-45s %-45s"%("aplId","CourseName","SchoolName"))
        for item in LessonList:
            aplId = item["aplId"]
            name = item['lesson']['courseInfo']['courName']
            school = item['lesson']['teachSchool']['schoolName']
            print ("%-11d %-45s %-45s"%(aplId,name,school))

    #输出选课列表(包含未选课程)
    def PrintMySelList(self):
        url = 'https://uims.jlu.edu.cn/ntms/service/res.do'
        payload = {
            "tag":"lessonSelectLog@selectStore",
            "branch":"default",
            "params":{
                "splanId":self.splanId
            }
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        LessonList =  json.loads(response.text)["value"]

        print ("%-11s%-45s%-45s%-45s"%("lslId","CourseName","SchoolName","Y/N"))
        for item in LessonList:
            lslId = item["lslId"]
            name = item['lesson']['courseInfo']['courName']
            school = item['lesson']['teachSchool']['schoolName']
            selected = item["selectResult"]
            print ("%-11d%-45s%-45s%-45s"%(lslId,name,school,selected))

    #输出已选课程列表
    def PrintMySelectedList(self):
        url = 'https://uims.jlu.edu.cn/ntms/service/res.do'
        payload = {
            "tag":"teachClassStud@schedule",
            "branch":"self",
            "params":{
                "termId":self.termId
            }
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        LessonList =  json.loads(response.text)["value"]
        for item in LessonList:
            name = item["teachClassMaster"]["lessonSegment"]["fullName"]
            print("%s "%name.encode("gbk"))
            for teacher in item["teachClassMaster"]["lessonTeachers"]:
                print("\t\t%s"%teacher["teacher"]["name"].encode("gbk"))

    #选课
    def SelectIt(self,lsltId):
        url = 'https://uims.jlu.edu.cn/ntms/action/select/select-lesson.do'
        payload = {
            "lsltId":lsltId,
            "opType":"Y"                    #同时添加到快捷选课?
        }
        #加个超时,要不然卡住了
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers,timeout=1)
        result = json.loads(response.text)

        print("errno: %d msg:%s"%(result["errno"],result["msg"]))
        return result["errno"]

    #退课
    def CancelIt(self,lsltId):
        url = 'https://uims.jlu.edu.cn/ntms/action/select/select-lesson.do'
        payload = {
            "lsltId":lsltId,
            "opType":"N"
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        result = json.loads(response.text)
        print("errno: %d msg:%s"%(result["errno"],result["msg"].encode("gbk")))
        return result["errno"]

    #获取课程的详细信息:有哪些老师授课,
    def GetLesDetailedInfo(self,lslId):
        url = 'https://uims.jlu.edu.cn/ntms/service/res.do'
        payload = {
            "tag":"lessonSelectLogTcm@selectGlobalStore",
            "branch":"self",
            "params":{
                "lslId":lslId,
                "myCampus":"Y"
            }
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        DetailedInfoList =  json.loads(response.text)["value"]

        for item in DetailedInfoList:
            print("==============================================================")
            name = item["lessonSegment"]["fullName"]
            lsltId = item["lsltId"]
            print("%-15s %-40s"%(lsltId,name))

            for schedule in item["teachClassMaster"]["lessonSchedules"]:
                room = schedule["classroom"]["fullName"]
                time = schedule["timeBlock"]["name"]
                print("%s %s"%(room,time))
            for teacher in item["teachClassMaster"]["lessonTeachers"]:
                teacher_name = teacher["teacher"]["name"]
                print("teacher: %s "%teacher_name)
        return
    #添加到选课列表
    def AddToSelList(self,aplId):
        url = 'https://uims.jlu.edu.cn/ntms/action/select/add-gx-lsl.do'
        payload = {
            #这里应该是一次可以添加好几个
            "aplIds":[
                aplId
            ],
            "splanId":self.splanId,
            "studId":self.stuId,
            "isQuick":False
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        print(response.text)
    #从选课列表删除
    def DelFromSelList(self,lslId):
        url = "https://uims.jlu.edu.cn/ntms/action/select/delete-other-lsl.do"
        payload={
            "lslId":lslId
        }
        response = self.s.post(url=url,json=payload,headers=self.login_success_headers)
        print(response.text)

    def Run(self):
        while True:
            os.system('cls')
            print("========================================================")
            print("\t\t1.Print all courses")
            print("\t\t2.Add to select list")
            print("\t\t3.Del from select list")
            print("\t\t4.Print select list")
            print("\t\t5.Print detailed course information")
            print("\t\t6.List of selected courses")
            print("\t\t7.Fuck it")          
            print("\t\t8.Cancel it")
            print("========================================================")
            print("please input choice >",end="")
            id = 0
            try:
                id = int(input())
            except:
                continue

            if id == 1:
                #输出课程列表
                print("====================================================================")
                print("[#]All courses:")
                self.PrintAllLessons()
            
            if id == 2:
                #添加到选课列表
                aplId = int(input("please input aplId >"))
                self.AddToSelList(aplId)

            if id == 3:
                #从选课列表删除
                lslId = int(input("Please input lslId >"))
                self.DelFromSelList(lslId)

            if id == 4:
                #输出选课列表
                print("====================================================================")
                print("[#]Select List")
                self.PrintMySelList()

            if id == 5:
                lslId = int(input("Please input lslId >"))
                self.GetLesDetailedInfo(lslId)
            if id == 6:
                #打印已选课程列表
                print("====================================================================")
                print("[#]List of selected courses:")
                self.PrintMySelectedList()
            
            if id == 7:
                #选课
                lsltids = input("Please input lsltIds >")
                pattern = "(\d+)"

                Works = {}
                for lsltid in re.findall(pattern=pattern,string=lsltids):
                    Works[lsltid] = {}

                    for i in range(8):          #每一个课开8个线程去强.
                        Works[lsltid][i] = threading.Thread(target = self.Fuck,args = (lsltid,))
                        Works[lsltid][i].start()

                for key in Works:
                    for i in range(8):
                        Works[key][i].join()

            if id == 8:
                lsltid = input("Please input lsltId >")
                self.CancelIt(lsltid)

    def Fuck(self,lsltId):
        while True:
            #获取课程状态
            statu = self.Selecting.get(lsltId)
            if statu == None:
                break
            #正在选择
            if statu == "doing":
                result = self.SelectIt(lsltId)
                #判断结果.0:选课成功 
                # 1410:已经选过该课程了
                # 1420:该课程已经选过其他教学班
                if result == 0 or result == 1410 or result == 1420:
                    self.mutex.acquire()
                    
                    if self.Selecting[lsltId] == 'doing':
                        self.Selecting[lsltId] = "ok"
                        print("[#]The lesson(%s) has be selected successfully!."%lsltId)
                    
                    self.mutex.release()
                    break

                #1932选课已经结束,
                if result == 1932 :
                    print("[x]Sorry. The time for selecting courses has ended!")
                    break
                #1931选课还未开始,如果不忽略错误,那么退出
                if result == 1931 and self.ignore_not_start == False:
                    print("[x]Sorry. It's not time to choose classes yet!.")
                    break
                #其他错误,不处理,继续尝试
            else:
                break
        
'''
大致流程是:
    获取课程列表,然后通过aplId 加入到选课列表. 

    获取选课列表的内容,得到课程的lslId  
    在页面上点击课程后,会出来详细的信息,也就是lsltId了,选课的时候就用这个去选.
    aplId--->lslId--->lsltId---->SelectIt.
'''

class VpnSession:

    def __init__(self):
        self.Session = requests.session()
        self.redirect_url = ''
        self.url = ''

    def login(self,username,password)->bool:
        index = 'https://webvpn.jlu.edu.cn/'
        login_url = 'https://webvpn.jlu.edu.cn/login'

        headers = {
            'Host': 'webvpn.jlu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
            
        }
        #get captcha_id
        html = BeautifulSoup(self.Session.get(url=index,headers=headers).text,'html.parser')
        captcha_id = ''
        for input in html.find_all('input'):
            name = ''
            try:
                name = input['name']
            except:
                pass
            else:
                if input['name'] == 'captcha_id':
                    captcha_id = input['value']
                    break

        #print(captcha_id) 
        #login 
        headers = {
            'Origin': 'https://webvpn.jlu.edu.cn',
            'Referer': 'https://webvpn.jlu.edu.cn/login',
            'X-Requested-With': 'XMLHttpRequest',
            'Host': 'webvpn.jlu.edu.cn',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
        }
        post_url = 'https://webvpn.jlu.edu.cn/do-login'
        data = 'auth_type=local'
        data += '&username=' + username 
        data += '&sms_code='
        data += '&password=' + password 
        data += '&captcha='
        data += '&needCaptcha=false'
        data += '&captcha_id=' + captcha_id

        success = json.loads(self.Session.post(url = post_url,data=data,headers=headers).text)['success']
        
        headers = {
            'Origin': 'https://webvpn.jlu.edu.cn',
            'Referer': 'https://webvpn.jlu.edu.cn/login',
            'Host': 'webvpn.jlu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
        }
        self.Session.get(url = index,headers = headers).url
        
        return success
    
    def redirect(self,name):
        get_url = 'https://webvpn.jlu.edu.cn/user/portal_groups?_t=' + str(time.time()).split('.')[0] + '224'
        headers = {
            'Host': 'webvpn.jlu.edu.cn',
            'Referer': 'https://webvpn.jlu.edu.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'

        }
        data = json.loads(self.Session.get(url = get_url,headers=headers).text)

        for a in data['data']:
            if a['group']['group_name'] == '学生资源':
                for b in a['resource']:
                    if b['name'] == name:
                        self.redirect_url = b['redirect']
                        if 'https' not in b['url']:
                            self.url = b['url'].replace('http','https')
                        else:
                            self.url = b['url']

                        return True
        return False

    def action(self,method,url,cookies,headers,data,json):
        new_url = 'https://webvpn.jlu.edu.cn' + url.replace(self.url + '/',self.redirect_url)
        new_headers = {
            'Host': 'webvpn.jlu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
        }
        #替换 Host
        if headers != None:
            for key in headers:
                # 重新设置下面这些header
                if key == 'Referer':
                    new_headers['Referer'] ='https://webvpn.jlu.edu.cn' + headers.get('Referer').replace(self.url + '/',self.redirect_url)
                    continue
                if key == 'Origin':
                    new_headers['Origin'] ='https://webvpn.jlu.edu.cn'
                #将没有的header 加到 new_headers 
                if new_headers.get(key) == None:
                    new_headers[key] = headers[key]
                
        if method == 'get':
            return self.Session.get(new_url,headers=new_headers,cookies=cookies,data=data)
        if method =='post':
            return  self.Session.post(url=new_url,data=data,headers=new_headers,cookies=cookies,json=json)
            
        

    def get(self,url,headers=None,cookies = None,data=None):
        return self.action('get',url,cookies,headers,data,json=None)
       
    def post(self,url,headers=None,cookies = None,data=None,json=None):
        return self.action('post',url,cookies,headers,data,json=json)

if __name__ == '__main__':
    choice = input("Enable Vpn?(Y/y) :")
    Session = None

    if choice == 'Y' or choice == 'y':
        Session = VpnSession()
        print("Vpn Login")

        username=  input("Username > ")
        password = getpass.getpass()

        if False == Session.login(username,password):
            print('login vpn failed!')
            exit(0)
        
        if False == Session.redirect('本科教务管理系统'):
            print('redirect failed!')
            exit(0)
        print('Vpn Init Success!')
    else:
        Session = requests.session()
    
    uims = Uims(Session)
    print("Uims Login")

    username = input('Username > ')
    password = getpass.getpass()
    
    if True == uims.login(username=username,password=password):
        uims.Run()
    else:
        print("Uims login Failed!")


