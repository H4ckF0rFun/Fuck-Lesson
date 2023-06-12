from copy import copy, deepcopy
from Cryptodome.Cipher import AES

import time
import ddddocr
import threading
from urllib import response
import requests
import base64
import json
import os
import sys
import urllib3

from urllib3.exceptions import InsecureRequestWarning



if len(sys.argv) < 4:
    print('Usage: %s username password batchId <loop>' % sys.argv[0])
    exit(-1)

DEBUG_REQUEST_COUNT = 0
urllib3.disable_warnings(InsecureRequestWarning)

WorkThreadCount = 8
ocr = ddddocr.DdddOcr()

def pkcs7padding(data, block_size=16):
    if type(data) != bytearray and type(data) != bytes:
        raise TypeError("仅支持 bytearray/bytes 类型!")
    pl = block_size - (len(data) % block_size)
    return data + bytearray([pl for i in range(pl)])

class iCourses:
    mutex = threading.Lock()

    def __init__(self):
        self.aeskey = ''
        self.loginname=''
        self.password = ''
        self.captcha = ''
        self.uuid = ''
        self.token = ''
        self.batchId = ''
        self.s = requests.session()
        
        self.is_login = False
        self.favorite = None
        self.select = None
        self.batchlist = None

        self.current = None
        self.error_code = 0
        self.try_if_capacity_full = True

    def login(self,username,password):
        index  ='https://icourses.jlu.edu.cn/'

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Host': 'icourses.jlu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }
        #get aes key
        html = self.s.get(url=index,headers=headers,verify=False).text
        start = html.find('"',html.find('loginVue.loginForm.aesKey')) + 1
        end = html.find('"',start)

        self.aeskey = html[start:end].encode('utf-8')
        self.loginname = username
        self.password = base64.b64encode(AES.new(self.aeskey,AES.MODE_ECB).encrypt(pkcs7padding(password.encode('utf-8'))))
        #
        get_url = 'https://icourses.jlu.edu.cn/xsxk/auth/captcha'

        headers={
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/profile/index.html',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }
        try:
            data = json.loads(self.s.post(url=get_url,headers=headers).text)
        except:
            print("get captcha failed!")
            exit(0)
        #
        self.uuid = data['data']['uuid']
        captcha = data['data']['captcha']
        self.captcha = ocr.classification(base64.b64decode(captcha[captcha.find(',') + 1:]))
        login_url = 'https://icourses.jlu.edu.cn/xsxk/auth/login'

        payload = {
            'loginname' :  self.loginname,
            'password' : self.password.decode('utf-8'),
            'captcha' : self.captcha,
            'uuid' : self.uuid
        }
        
        response = json.loads(self.s.post(url=login_url,headers=headers,data = payload).text)
        if response['code'] == 200 and response['msg'] == '登录成功':
            self.token  = response['data']['token']
            s = ''
            s += 'login success!\n'
            s += '=' * 0x40 + '\n'
            s += '\t\t@XH:   %s'%response['data']['student']['XH']+ '\n'
            s += '\t\t@XM:   %s'%response['data']['student']['XM']+ '\n'
            s += '\t\t@ZYMC: %s'%response['data']['student']['ZYMC']+ '\n'
            s += '=' * 0x40+ '\n'
            for c in response['data']['student']['electiveBatchList']:
                s += '\t\t@name:      %s'%c['name']+ '\n'
                s += '\t\t@BeginTime: %s'%c['beginTime']+ '\n'
                s += '\t\t@EndTime:   %s'%c['endTime']+ '\n'
                s += '=' * 0x40+ '\n'
            print(s)
            self.batchlist = response['data']['student']['electiveBatchList']
            self.is_login = True
            return True
        else:
            print('login failed! ')
            print('reason: %s'%response['msg'])
            return False
        
       # self.s sda
    def setbatchId(self,idx):
        url = 'https://icourses.jlu.edu.cn/xsxk/elective/user'

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/profile/index.html',
            'Authorization':self.token , 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }
        
        try:
            self.batchId = self.batchlist[idx]['code']
        except:
            print('No such batch Id')
            return
        
        payload = {
            'batchId':self.batchId
        }
        d = json.loads(self.s.post(url=url,headers=headers,data=payload).text)
        if 200 != d['code']:
            print("set batchid failed")
            return 
        c = self.batchlist[idx]     
        print('Selected BatchId:')
        s = ''    
        s += '=' * 0x40+ '\n'
        s += '\t\t@name:      %s'%c['name']+ '\n'
        s += '\t\t@BeginTime: %s'%c['beginTime']+ '\n'
        s += '\t\t@EndTime:   %s'%c['endTime']+ '\n'
        s += '=' * 0x40 + '\n'
        print(s)

        url = 'https://icourses.jlu.edu.cn/xsxk/elective/grablessons?batchId=' + self.batchId

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/profile/index.html',
            'Authorization':self.token , 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }
        #为什么这里必须要请求一次连接
        self.s.get(url=url,headers=headers)

    def del_lesson(self,ClassType,ClassId,SecretVal):
        post_url = 'https://icourses.jlu.edu.cn/xsxk/elective/clazz/del'

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/elective/grablessons?batchId=' + self.batchid,
            'Authorization':self.token , 
            'batchId': self.batchId,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }

        payload = {
            'clazzType':ClassType,
            'clazzId' : ClassId,
            'secretVal' : SecretVal,
            'source':'yxkcyx'
        }
        response = json.loads(self.s.post(url=post_url,headers=headers,data=payload).text)
        
        if response['code'] == 200:
            print('del success!')
        else:
            print('del failed: %s'%response['msg'])
    
    #已选课程
    def get_select(self):
        post_url =  'https://icourses.jlu.edu.cn/xsxk/elective/select'

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/elective/grablessons?batchId=' + self.batchId,
            'Authorization':self.token , 
            'batchId': self.batchId,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }

        response = json.loads(self.s.post(url=post_url,headers=headers).text)
        if response['code'] == 200:
            self.select = response['data']
        else:
            print('get_select failed :%s'%response['msg'])
        pass

    #获取收藏课程列表.
    def get_favorite(self):
        post_url = 'https://icourses.jlu.edu.cn/xsxk/sc/clazz/list'

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/elective/grablessons?batchId=' + self.batchId,
            'Authorization':self.token , 
            'batchId': self.batchId,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }
        cookies = {
            'Authorization':self.token
        }
        t = self.s.post(url = post_url,headers=headers,cookies=cookies)
        response = json.loads(t.text)
        if response['code'] == 200:
            self.favorite = response['data']
        else:
            print('get_favorite failed :%s'%response['msg'])


    # 选择一个课的接口...
    def select_favorite(self,ClassType,ClassId,SecretVal):
        #在收藏页面添加的接口和在主修课程页面添加的接口不一样。
        post_url = 'https://icourses.jlu.edu.cn/xsxk/sc/clazz/addxk'

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/elective/grablessons?batchId=' + self.batchId,
            'Authorization':self.token , 
            'batchId': self.batchId,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }

        payload = {
            'clazzType':ClassType,
            'clazzId':ClassId,
            'secretVal' : SecretVal
        }

        response = json.loads(self.s.post(url=post_url,headers=headers,data=payload,verify=False).text)

        return response

    def find(self,key):
        post_url = 'https://icourses.jlu.edu.cn/xsxk/elective/clazz/list'

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/elective/grablessons?batchId=' + self.batchId,
            'Authorization':self.token , 
            'batchId': self.batchId,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }

        payload = {
            "campus": "01",                     # 校区.
            "teachingClassType":"TJKC",        # FANKC 或者是 TJKC
            "pageNumber":1,
            "pageSize":999999,                  #列出所有.
            "orderBy":"",
            'KEY':key
        }

        response = json.loads(self.s.post(url=post_url,headers=headers,json=payload).text)

        '''
            课程信息:
                每一个老师的教学班 
        '''
        
        if response['code'] == 200:
            for item in response['data']['rows']:
                print("%-20s %-10s %-10s %-20s"%(
                    item['KCM'],item['KCLB'],item['KCXZ'],item['KKDW']
                ))
                
                for tech in item["tcList"]:
                    print(' ' * 8 + '%-20s %-10s %-20d %-20s '%(
                       tech['JXBID'],tech['SKJS'],tech['classCapacity'],tech['TJBJ']
                    ))
                    
                print('')
        else:
            print('get all lesson failed: %s'%response['msg'])


    #添加到收藏课程列表.clazzID如何确定
    def add_to_favorite(self,clazzType,clazzId,SecretVal):
        post_url = 'https://icourses.jlu.edu.cn/xsxk/sc/clazz/add'

        headers = {
            'Host': 'icourses.jlu.edu.cn',
            'Origin': 'https://icourses.jlu.edu.cn',
            'Referer': 'https://icourses.jlu.edu.cn/xsxk/elective/grablessons?batchId=' + self.batchid,
            'Authorization':self.token , 
            'batchId': self.batchId,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
        }

        payload = {
            "clazzType":clazzType,          #貌似只能从主修课程里面选择?,查看全校课程里面没有选课按钮....
            "clazzId":clazzId,              # 
            "secretVal":SecretVal,
        }

        return json.loads(self.s.post(url=post_url,headers=headers,data=payload).text)

    def PrintSelect(self):
        print("="*20 + 'My Select' + '='*20)
        if self.select != None:
            for item in self.select:
                print('Teacther: %-10sName: %-20s Id: %-30s'%(item['SKJS'],item['KCM'],item['JXBID']))
        
    def PrintFavorite(self):
        print("="*20 + 'Favorite' + '='*20)
        if self.favorite != None:
            for item in self.favorite:
                print('Teacther: %-10sName: %-20s Id: %-30sclazzType: %-10s'%(item['SKJS'],item['KCM'],item['JXBID'],item['teachingClassType']))

        print('=' * 48)


    #普通的选课(对收藏中的所有课都选择,)
    def SelectMyFavorite(self):
        if self.favorite != None:
            for item in self.favorite:
                self.select_favorite(item['teachingClassType'],item['JXBID'],item['secretVal'])


    def workThread(self,clazzType,clazzId,SecretVal,Name):
        tmp = deepcopy(self)

        global DEBUG_REQUEST_COUNT
        
        while True:
            try:
                response = tmp.select_favorite(clazzType,clazzId,SecretVal)
            except :
                break
            
            code = response['code']
            msg = response['msg']

            self.mutex.acquire()

            DEBUG_REQUEST_COUNT += 1

            if self.current.get(clazzId) != None:
                #正在抢课。
                if self.current[clazzId] == 'doing':
                    if code == 200:
                        print('select [%s] success'%Name)
                        self.current[clazzId] = 'done'
                        self.mutex.release()
                        break       # 
                    
                    elif code == 500 :
                        if msg == '该课程已在选课结果中':
                            print('[%s] %s'%(Name,msg))
                            self.current[clazzId] = 'done'
                            self.mutex.release()
                            break

                        #时间未开始继续尝试.
                        if msg == '本轮次选课暂未开始':
                            print('本轮次选课暂未开始')
                            self.mutex.release()
                            continue
                        #
                        if msg == '课容量已满':
                            print(Name + "课容量已满")
                            self.mutex.release()
                            if self.try_if_capacity_full:
                                continue
                            else:
                                break
                                 
                        print('[%s] %s'%(Name,msg))         #错误信息,继续尝试...
                        self.mutex.release()
                        break
                    elif code == 401:                       #被顶下去了,重新登录
                        print(msg)
                        self.error_code = 401
                        self.mutex.release()
                        break
                    else:
                        print('[%d]: failed,try again'%code)
                        self.mutex.release()
                        continue
                else:
                    self.mutex.release()
                    break
            else:
                self.mutex.release()
                break


    def FuckMyFavorite(self):
        self.get_favorite()

        thread = {}
        if None != self.favorite:
            self.current = {}

            for item in self.favorite:
                key = item['JXBID']
                thread[key] = []
                
                self.mutex.acquire()
                self.current[key] = 'doing'
                self.mutex.release()

                args = (item['teachingClassType'],item['JXBID'],item['secretVal'],item['KCM'])

                for i in range(WorkThreadCount):    
                    thread[key].append(threading.Thread(target=self.workThread,args=args))
                    thread[key][-1].start()

            #wait all thread exit
            
            for key in thread:
                for t in thread[key]:
                    t.join()

            print('end...')
        pass
    '''
    TJKC  推介课程
    FANKC 主修课程
    '''
if __name__ == '__main__':
    while True:
        failed_count = 999999999999
        a = iCourses()
        
        #尝试登录...
        for i in range(failed_count):
            if a.login(sys.argv[1],sys.argv[2]):
                break
            time.sleep(0.02)
          
        if a.is_login == False:
            print('登录失败')
            exit(0)
        
        a.setbatchId(int(sys.argv[3]))        
        a.get_favorite()
        #
        a.PrintFavorite()
        a.FuckMyFavorite()
        
        if a.error_code != 0:
            print('error: ' + str(a.error_code))
            continue
        
        #获取已选的课
        a.get_select()
        a.PrintSelect()
        print('DEBUG_REQUEST_COUNT:%d \n' % DEBUG_REQUEST_COUNT)
        
        if len(sys.argv) == 4:
            break
        time.sleep(0.02)
        
