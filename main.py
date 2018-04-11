#!/usr/bin/env python3
# -*- coding: utf-8 -*-

' jwts@HIT '
__author__ = '惊蛰'

import requests
import threading
import getpass
import time
import re
import os


class Session(object):
    def __init__(self):
        self.s = requests.Session()
        self.semester = None

    def get_alert(self, content):
        msg = re.search("alert\('(.*?)'\);", content)
        if msg and msg.group(1) in ["用户不存在或密码错误！", "页面过期，请重新登录"]:
            print(msg.group(1))
            self.login()
        elif msg and '成功' in msg.group(1):
            print(msg.group(1))
            os._exit(0)
        elif msg:
            print(msg.group(1))

    def login(self):
        username = input('username:')
        password = getpass.getpass('password:')
        r = self.s.post('http://jwts.hit.edu.cn/loginLdap', data={
            'usercode': username,
            'password': password,
            'code': ''
        })
        if r.history:
            self.get_alert(r.text)
        else:
            print('Account：', self.get_username())

    def set_semester(self):
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
        r = self.s.post('http://jwts.hit.edu.cn/xsxk/queryXsxkList', data={
            'pageXklb': 'yy',
            'pageXnxq': '2017-20182',
        })
        if r.history:
            self.get_alert(r.text)
        else:
            token = re.search('<input type="hidden" id="token" name="token" value="(.*?)" />', r.text)
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
            course_id = re.findall('<input id="xkyq_(.*?)" type="hidden" value=""/>', r.text)
            teacher = re.findall(
                '<td><div style="width:100%; white-space: normal;word-break:break-all;">(.*?)</div></td>', r.text)
            return {'name': course_name, 'id': course_id, 'teacher': teacher}

    def select_course(self, course_id, course_type):
        if self.semester == None:
            self.set_semester()
        r = self.s.post('http://jwts.hit.edu.cn/xsxk/saveXsxk', data={
            'rwh': course_id,
            'token': self.get_token(),
            'pageXklb': course_type,
            'pageXnxq': self.semester,
        })
        self.get_alert(r.text)
        return r.text


def get_courese_id(course_list):
    course_name = input('course_name:')
    for i in range(len(course_list['name'])):
        if course_name.lower() in course_list['name'][i].lower():
            course_id = course_list['id'][i]
            print("Find the course successfully.")
            return course_id
        else:
            course_id = None
    if course_id == None:
        return False


def loop(Session, course_id, course_type, thread_num=5):
    thread_list = []
    for i in range(thread_num):
        thread_list.append(threading.Thread(target=Session.select_course, args=(course_id, course_type,)))
    for t in thread_list:
        t.start()
    for t in thread_list:
        t.join()


def main():
    s = Session()
    s.login()
    course_type = input('course_type:')
    course_list = s.get_course_list(course_type)
    course_id = get_courese_id(course_list)
    while course_id == False:
        print("Can't find the course.\nPlease input the name of the course again.")
        course_id = get_courese_id(course_list)
    input("Please input ENTER to start select!")
    while 1:
        loop(s, course_id, course_type)


if __name__ == '__main__':
    main()
