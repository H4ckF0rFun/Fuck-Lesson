# -*- coding: UTF-8 -*-
import random
import requests
import json
import thread
import threading
import re
import time
import os
import hashlib
import getpass
from requests import sessions

login_success_headers = {
        'Host': 'uims.jlu.edu.cn',
        'Origin': 'https://uims.jlu.edu.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer': 'https://uims.jlu.edu.cn/ntms/index.do',
}

stuId = ""
splanId = 0
termId = 0

#登录,成功后返回一个session
#md5("UIMS" + username + password)

def login(username="",password=""):
    session = requests.Session()

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
    verification_code_res = session.get(url = verification_code,headers=headers)
    with open("./vcode.png","wb") as file:
        file.write(verification_code_res.content)
    
    os.startfile("vcode.png")
    #让用户自己输入验证码
    print "[#]please input vcode >",
    vcode = str(raw_input()) 
    #登录
    print("[*]login....")
    #表单方式提交,不是json
    payload = {
        "username":username,
        "password":password,
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
    response = session.post(data=payload,url = login_auth,headers=headers,cookies=cookies)
    print("[#]statu code %d"%response.status_code)
    #登录成功会重定向到index.do
    if response.url == "https://uims.jlu.edu.cn/ntms/index.do":
        print("[#]login success!")
        return session
    else:
        print("[x]login error!")
        session.close()
        return None

#获取个人信息
def GetMyInfo(session):
    url = "https://uims.jlu.edu.cn/ntms/service/res.do"
    payload={
        "tag":"studInfoAll@student",
        "branch":"self",
        "params":{}
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    return json.loads(response.text)
#打印全部课程(供选择的课)
def PrintAllLessons(session):
    url = "https://uims.jlu.edu.cn/ntms/service/res.do"
    payload={
        "type":"search",
        "tag":"apl@gxSelect",
        "branch":"default",
        "params":{
            #"mooc":"Y",                     #慕课在线课程
            "campus":"1401",                 #应该是校区,1401貌似是前卫南区
            "splanId":splanId,               #这里可能需要修改
            "termId":termId                  #这里可能需要修改
            },
        "orderBy":"lesson.courseInfo.courName"
    }

    response = session.post(url=url,json=payload,headers=login_success_headers)
    LessonList =  json.loads(response.text)["value"]

    print ("%-11s %-45s %-45s"%("aplId","CourseName","SchoolName"))
    for item in LessonList:
        aplId = item["aplId"]
        name = item['lesson']['courseInfo']['courName']
        school = item['lesson']['teachSchool']['schoolName']
        print ("%-11d %-45s %-45s"%(aplId,name.encode("gbk"),school.encode("gbk")))

#输出选课列表(包含未选课程)
def PrintMySelList(session):
    url = 'https://uims.jlu.edu.cn/ntms/service/res.do'
    payload = {
        "tag":"lessonSelectLog@selectStore",
        "branch":"default",
        "params":{
            "splanId":splanId
        }
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    LessonList =  json.loads(response.text)["value"]

    print ("%-11s%-45s%-45s%-45s"%("lslId","CourseName","SchoolName","Y/N"))
    for item in LessonList:
        lslId = item["lslId"]
        name = item['lesson']['courseInfo']['courName']
        school = item['lesson']['teachSchool']['schoolName']
        selected = item["selectResult"]
        print ("%-11d%-45s%-45s%-45s"%(lslId,name.encode("gbk"),school.encode("gbk"),selected.encode("gbk")))

#输出已选课程列表
def PrintMySelectedList(session):
    url = 'https://uims.jlu.edu.cn/ntms/service/res.do'
    payload = {
        "tag":"teachClassStud@schedule",
        "branch":"self",
        "params":{
            "termId":termId
        }
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    LessonList =  json.loads(response.text)["value"]
    for item in LessonList:
        name = item["teachClassMaster"]["lessonSegment"]["fullName"]
        print("%s "%name.encode("gbk"))
        for teacher in item["teachClassMaster"]["lessonTeachers"]:
            print("\t\t%s"%teacher["teacher"]["name"].encode("gbk"))

#获取选课信息
def GetSelLesInfo(session):
    url ="https://uims.jlu.edu.cn/ntms/service/res.do"
    payload = {
        "tag":"common@selectPlan",
        "branch":"byStudentSet",
        "params":{
            "studId":stuId
        }
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    return json.loads(response.text)

#输出选课日志的锁
SelectLogLock = threading.Lock()
#选课
def SelectIt(session,lsltId):
    url = 'https://uims.jlu.edu.cn/ntms/action/select/select-lesson.do'
    payload = {
        "lsltId":lsltId,
        "opType":"Y"
    }
    #加个超时,要不然卡住了
    response = session.post(url=url,json=payload,headers=login_success_headers,timeout=1)
    result = json.loads(response.text)
    #输出加个锁,要不然窜行了

    SelectLogLock.acquire()
    print("errno: %d msg:%s"%(result["errno"],result["msg"].encode("gbk")))
    SelectLogLock.release()
    return result["errno"]

#退课
def CancelIt(session,lsltId):
    url = 'https://uims.jlu.edu.cn/ntms/action/select/select-lesson.do'
    payload = {
        "lsltId":lsltId,
        "opType":"N"
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    result = json.loads(response.text)
    print("errno: %d msg:%s"%(result["errno"],result["msg"].encode("gbk")))
    return result["errno"]

#获取课程的详细信息:有哪些老师授课,
def GetLesDetailedInfo(session,lslId):
    url = 'https://uims.jlu.edu.cn/ntms/service/res.do'
    payload = {
        "tag":"lessonSelectLogTcm@selectGlobalStore",
        "branch":"self",
        "params":{
            "lslId":lslId,
            "myCampus":"Y"
        }
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    DetailedInfoList =  json.loads(response.text)["value"]

    for item in DetailedInfoList:
        print("========================================================================")
        name = item["lessonSegment"]["fullName"].encode("gbk")
        lsltId = item["lsltId"].encode("gbk")
        print("%-15s %-40s"%(lsltId,name))

        for schedule in item["teachClassMaster"]["lessonSchedules"]:
            room = schedule["classroom"]["fullName"]
            time = schedule["timeBlock"]["name"]
            print("%s %s"%(room.encode("gbk"),time.encode("gbk")))
        for teacher in item["teachClassMaster"]["lessonTeachers"]:
            teacher_name = teacher["teacher"]["name"]
            print("teacher: %s "%teacher_name.encode("gbk"))
    return
#添加到选课列表
def AddToSelList(session,aplId):
    url = 'https://uims.jlu.edu.cn/ntms/action/select/add-gx-lsl.do'
    payload = {
        #这里应该是一次可以添加好几个
        "aplIds":[
            aplId
        ],
        "splanId":splanId,
        "studId":stuId,
        "isQuick":False
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    print(response.text)
#从选课列表删除
def DelFromSelList(session,lslId):
    url = "https://uims.jlu.edu.cn/ntms/action/select/delete-other-lsl.do"
    payload={
        "lslId":lslId
    }
    response = session.post(url=url,json=payload,headers=login_success_headers)
    print(response.text)


Selecting={}
ignore_error = True
Counter = {}
#线程函数选课
def fuck(session,lsltId):
    while True:
        #获取课程状态
        statu = Selecting[lsltId]
        #正在选择
        if statu == "doing":
            result = SelectIt(session,lsltId)
            #判断结果.0:选课成功 
            # 1410:已经选过该课程了
            # 1420:该课程已经选过其他教学班
            if result == 0 or result == 1410 or result == 1420:
                if Selecting[lsltId] == 'doing':
                    Selecting[lsltId] = "ok"
                    SelectLogLock.acquire()
                    print("[#]The lesson(%s) has be selected successfully!."%lsltId)
                    SelectLogLock.release()
                break
            #1932选课已经结束,
            if result == 1932 :
                SelectLogLock.acquire()
                print("[x]Sorry. The time for selecting courses has ended!")
                SelectLogLock.release()
                break
            #1931选课还未开始,如果不忽略错误,那么退出
            if result == 1931 and ignore_error == False:
                SelectLogLock.acquire()
                print("[x]Sorry. It's not time to choose classes yet!.")
                SelectLogLock.release()
                break
            #其他错误,不处理,继续尝试
        else:
            #已经选上了
            break
    Counter["WorkingThread"]-=1
'''
大致流程是:
    获取课程列表,然后通过aplId 加入到选课列表.
    获取选课列表的内容,得到课程的lslId
    在页面上点击课程后,会出来详细的信息,也就是lsltId了,选课的时候就用这个去选.
    aplId--->lslId--->lsltId---->SelectIt.
'''

#输入用户账号和密码
#emmmm突然在Js代码里面找到了这部分 ThansferPwd = MD5("UIMS"+username+password)
print "Please input username:",
username = raw_input()
password = getpass.getpass("Please input password:")
ThansferPwd = hashlib.md5("UIMS"+username+password).hexdigest()
#登录
session = login(username=username,password=ThansferPwd)
if session is None:
    exit()

#获取stuId
print("[*]Get StuId...")
info = GetMyInfo(session)
stuId = info["value"][0]["studId"]
print("[#]stuId: %d"%stuId)

#获取选课信息
print("[*]Get Sel Lesson Info...")
SelInfo = GetSelLesInfo(session)
print("====================================================================")
print("\t\t@start time: %s"%SelInfo["value"][0]["currStartTime"].encode("gbk"))
print("\t\t@stop  time: %s"%SelInfo["value"][0]["currStopTime"].encode("gbk"))
print("\t\t@title     : %s"%SelInfo["value"][0]["title"].encode("gbk"))

splanId = SelInfo["value"][0]["splanId"]
termId = SelInfo["value"][0]["teachingTerm"]["termId"]

print("\t\t@splanId: %d\ttermId: %d"%(splanId,termId))

while True:
    print("====================================================================")
    print("\t\t1.Print all courses")
    print("\t\t2.Add to select list")
    print("\t\t3.Del from select list")
    print("\t\t4.Print select list")
    print("\t\t5.Print detailed course information")
    print("\t\t6.List of selected courses")
    print("\t\t7.Fuck it")
    print("\t\t8.Cancel it")
    print("\t\t9.exit")
    print("====================================================================")
    print "please input choice >",
    choice = input()
    id = int(choice)
    if id == 1:
        #输出课程列表
        print("====================================================================")
        print("[#]All courses:")
        PrintAllLessons(session)
    
    if id == 2:
        #添加到选课列表
        print "please input aplId >",
        aplId = int(input())
        AddToSelList(session,aplId)

    if id == 3:
        #从选课列表删除
        print "Please input lslId >",
        lslId = int(input())
        DelFromSelList(session,lslId)

    if id == 4:
        #输出选课列表
        print("====================================================================")
        print("[#]Select List")
        PrintMySelList(session)

    if id == 5:
        #打印课程详细信息
        print "Please input lslId >",
        lslId = int(input())
        GetLesDetailedInfo(session,lslId)
    if id == 6:
        #打印已选课程列表
        print("====================================================================")
        print("[#]List of selected courses:")
        PrintMySelectedList(session)
    if id == 7:
        Counter["WorkingThread"] = 0
        #选课
        print "Please input lsltIds >",
        lsltids = raw_input()
        pattern = "(\d+)"
        for lsltid in re.findall(pattern=pattern,string=lsltids):
            Selecting[lsltid] = "doing"

            print lsltid,"Selecting......\n"
            for i in range(8):
                Counter["WorkingThread"]+=1
                thread.start_new_thread(fuck,(session,lsltid))
        
        while Counter["WorkingThread"]>0:
            time.sleep(1)
    if id == 8:
        #退课
        print "Please input lsltId >",
        lsltid = input()
        CancelIt(session,lsltid)

    if id == 9:
        break
    
session.close()
