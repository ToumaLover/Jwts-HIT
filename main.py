#!/usr/bin/env python3
# -*- coding: utf-8 -*-

' jwts@HIT '
__author__ = '惊蛰'

import requests
import threading
import getpass
import datetime
import re
import os


class Session(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.semester = None
        self.s = requests.Session()

    def get_alert(self, content):
        msg = re.search("alert\('(.*?)'\);", content)
        if msg:
            print(datetime.datetime.now(), msg.group(1))
            self.staus(msg.group(1))

    def staus(self, content):
        if "容量已满"in content:
            # os._exit(0)  # 注释此行可以监控捡漏
            pass
        elif "已选" in content:
            os._exit(0)
        elif "成功" in content:
            os._exit(0)
        elif content == "用户不存在或密码错误！":
            self.set_basis()
            self.login()
        elif content == "页面过期，请重新登录":
            self.login()

    def set_basis(self):
        self.username = input('username:')
        self.password = getpass.getpass('password:')

    def login(self):
        r = self.s.post('http://jwts.hit.edu.cn/loginLdap', data={
            'usercode': self.username,
            'password': self.password,
            'code': ''
        })
        if r.history:
            self.get_alert(r.text)
        else:
            print('Account：', self.get_username())

    def set_semester(self):
        '''默认最近的选课学期'''
        r = self.s.get('http://jwts.hit.edu.cn/xsxk/queryXsxk?pageXklb=szxx')
        semester = re.search('<option value="(.*?)"  selected="selected"', r.text)
        if semester:
            self.semester = semester.group(1)

    def get_username(self):
        r = self.s.get('http://jwts.hit.edu.cn/login')
        if r.history:
            self.get_alert(r.text)
        elif re.search('您好！(.*?)同学', r.text):
            return re.search('您好！(.*?)同学', r.text).group(1)

    def get_token(self):
        r = self.s.post('http://jwts.hit.edu.cn/xsxk/queryXsxkList', timeout=15.00, data={
            'pageXklb': 'yy',
            'pageXnxq': '2017-20182',
        })
        if r.history:
            self.get_alert(r.text)
        else:
            token = re.search('id="token" name="token" value="(.*?)" />', r.text)
            if token:
                return token.group(1)

    def get_course_list(self, course_type):
        if self.semester == None:
            self.set_semester()
        r = self.s.post('http://jwts.hit.edu.cn/xsxk/queryXsxkList', data={
            'pageXklb': course_type,
            'pageXnxq': self.semester,
            'pageSize': 300,
        })
        if r.history:
            self.get_alert(r.text)
        else:
            course_name = re.findall('return false;">(.*?)</a></td>', r.text)
            course_id = re.findall('<input id="xkyq_(.*?)"', r.text)
            if course_name:
                course_list = []
                for x in range(len(course_name)):
                    course_list.append({'name': course_name[x], 'id': course_id[x]})
                return course_list
            else:
                print("Can't get the list of course.")
                os._exit(0)

    def select_course(self, course_id, course_type):
        if self.semester == None:
            self.set_semester()
        r = self.s.post('http://jwts.hit.edu.cn/xsxk/saveXsxk', timeout=15.00, data={
            'rwh': course_id,
            'token': self.get_token(),
            'pageXklb': course_type,
            'pageXnxq': self.semester,
        })
        self.get_alert(r.text)
        return r.text

    def cancel_course(self, course_id, course_type):
        if self.semester == None:
            self.set_semester()
        r = self.s.post('http://jwts.hit.edu.cn/xsxk/saveXstk', data={
            'rwh': course_id,
            'token': self.get_token(),
            'pageXklb': course_type,
            'pageXnxq': self.semester,
        })
        self.get_alert(r.text)
        return r.text


def get_courese_id(course_list):
    course_name = input('course_name:')
    for i in range(len(course_list)):
        if course_name.lower() in course_list[i]['name'].lower():
            course_id = course_list[i]['id']
            print("Find the course successfully.")
            return course_id
        else:
            course_id = None
    if course_id == None:
        return False


def loop(Session, course_id, course_type, thread_num=15):
    thread_list = []
    for i in range(thread_num):
        thread_list.append(threading.Thread(target=Session.select_course, args=(course_id, course_type,)))
    for t in thread_list:
        t.start()
    for t in thread_list:
        t.join()


def main():
    username = input('username:')
    password = getpass.getpass('password:')
    s = Session(username, password)
    s.login()
    course_type = input('course_type:')
    course_list = s.get_course_list(course_type)
    course_id = get_courese_id(course_list)
    while course_id == False:
        print("Can't find the course.\nPlease input the name of the course again.")
        course_id = get_courese_id(course_list)
    input("Please input ENTER to start to select the course!")
    while 1:
        loop(s, course_id, course_type)


if __name__ == '__main__':
    main()
