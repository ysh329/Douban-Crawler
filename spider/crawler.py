# -*- coding: utf-8 -*-
################################### PART0 DESCRIPTION #################################
# Filename: crawler.py
# Description:
#

# E-mail: ysh329@sina.com
# Create: 2016-8-7 14:22:51
# Last:
__author__ = 'yuens'


################################### PART1 IMPORT ######################################

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import logging

import urllib2
from bs4 import BeautifulSoup
import re
import time
import math


################################### PART2 CLASS && FUNCTION ###########################

# 通过目录页获取列表信息列表
def getBasicInfoList(listUrl):
    basicInfoList = []

    # 发送请求接受响应并转换为soup对象后抽出结果保存
    request = urllib2.Request(listUrl)
    try:
        # 发出请求接收响应转换为soup对象
        response = urllib2.urlopen(request)
        html = response.read()
        soup = BeautifulSoup(html, "lxml")
        soupOfAllTitles = soup.find_all("tr")

        #for i in soupOfAllTitles: logging.info(i)

        # 统计结果
        failureNum = 0
        successNum = 0
        for titleIdx in xrange(len(soupOfAllTitles)):
            titleDetailInfo = soupOfAllTitles[titleIdx]
            try:
                # 获取每条信息的[链接、标题、用户名、用户名链接、回帖人数、回帖日期]
                title = titleDetailInfo.a.get("title")
                href = titleDetailInfo.a.get("href")

                userLink = re.compile('<td nowrap="nowrap"><a class="" href="(.*)">').findall(str(titleDetailInfo))[0]
                userName = re.findall(userLink+'">(.*)</a></td>', str(titleDetailInfo))[0]
                doubanId = re.findall(r"\d+", userLink)[0]

                commentNumStr = re.findall('<td class="" nowrap="nowrap">(.*)</td>', str(titleDetailInfo))[0]
                commentNum = 0 if commentNumStr=="" else int(commentNumStr)

                lastTime = str(time.localtime(time.time())[0]) +\
                           "-" +\
                           re.findall('<td class="time" nowrap="nowrap">(.*)</td>', str(titleDetailInfo))[0]

                #print commentNum, lastTime, type(lastTime)

                basicInfoList.append( (title, href, userName, doubanId, userLink, commentNum, lastTime) )
                successNum += 1
            except Exception, e:
                logging.error("ExceptionError:{0}".format(e))
                failureNum += 1
        logging.info("title:{0},successNum:{1},failureNum:{2}".format(soup.title.string.strip(), successNum, failureNum))
    except urllib2.HTTPError, e:
        logging.error("HTTPError code:{0}, URL:{1}".format(e.code, listUrl))

    return basicInfoList

# 过滤基本信息列表中的无用条目
def filterBasicInfoList(basicInfoList):
    pass
    return basicInfoList

# 查找指定关键词的前topNGroup个群组的信息[组名、地址、人数、介绍]
def getGroupsInfoList(queryKeywordsList, topNGroup=10, findGroupUrl="https://www.douban.com/group/search?start=0&cat=1019&q=[REPLACEBYQUERY]&sort=relevance", maxGroupsNumForEachPage=20):

    # 根据需要的小组数目计算小组信息的目录页
    def getGroupCategoryUrlList(queryKeywordsList, topNGroup=10, findGroupUrl="https://www.douban.com/group/search?start=0&cat=1019&q=[REPLACEBYQUERY]&sort=relevance", maxGroupsNumForEachPage=20):
        # 获取查询结果地址
        queryString = "+".join(queryKeywordsList)
        queryUrl = findGroupUrl.replace("[REPLACEBYQUERY]", queryString)
        logging.info("queryUrl:{0}".format(queryUrl))

        # 发送访问请求和接收
        try:
            request = urllib2.Request(queryUrl)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            logging.error("HTTPError code:{0}, URL:{1}".format(e.code, queryUrl))
        except Exception, e:
            logging.error(e)

        # 读取响应内容并转换为soup对象
        html = response.read()
        soup = BeautifulSoup(html, "lxml")

        countPlain = soup.find("span", attrs={"class":"count"}).string
        countNum = int(re.findall('[0-9]\d', countPlain)[0])
        maxPageNum = int(math.ceil(float(countNum)/maxGroupsNumForEachPage))
        pageStartGroupIdxList = map(lambda pageIdx: str(pageIdx*10), xrange(maxPageNum))
        groupCategoryUrlList = map(lambda start: findGroupUrl.replace("start=0", "start="+start), pageStartGroupIdxList)
        if topNGroup < len(groupCategoryUrlList)*maxGroupsNumForEachPage:
            groupCategoryUrlList = groupCategoryUrlList[:topNGroup/maxGroupsNumForEachPage+1]
        return groupCategoryUrlList


    # 取出关键标签部分
    def getGroupInfoListForEachPage(groupCategoryUrl):
        # 发送访问请求和接收
        try:
            request = urllib2.Request(groupCategoryUrl)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            logging.error("HTTPError code:{0}, URL:{1}".format(e.code, queryUrl))
        except Exception, e:
            logging.error(e)

        # 读取响应内容并转换为soup对象
        html = response.read()
        soup = BeautifulSoup(html, "lxml")

        #print soup.find("div", id="wrapper").find("div", id="content")
        resultOfSoup = soup.find_all("div", attrs={'class':"result"})

        # 遍历抽取重要信息[组名、链接、人数、介绍]
        groupInfoList = []
        # for resultIdx in xrange(len(resultOfSoup)):
        #     try:
        #         result = resultOfSoup[resultIdx]
        #         groupName = "".join(list(result.find("div", attrs={'class':"title"}).strings)).strip()
        #         groupHref = result.a.get("href")
        #         groupMemberPlain = result.find("div", attrs={'class':"info"}).string
        #         groupMemberNum = int(re.findall('^[0-9]\d*', groupMemberPlain))
        #         groupIntro = result.p.string.strip().replace(" ", "").replace("", "")
        #         groupInfoList.append(groupName, groupHref, groupMemberNum, groupIntro)
        #     except Exception, e:
        #         logging.error(e)
        # return groupInfoList



################################### PART３ TEST #######################################

# 初始化参数
listUrl = "https://www.douban.com/group/HZhome/discussion?start=0"
queryKeywordsList = ["杭州", "租房"]

# 初始化环境
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

'''
# 执行爬取
basicInfoList = getBasicInfoList(listUrl)
filteredBasicInfoList = filterBasicInfoList(basicInfoList)

# 打印结果
for basicInfoIdx in xrange(len(filteredBasicInfoList)):
    title = basicInfoList[basicInfoIdx][0]
    href = basicInfoList[basicInfoIdx][1]
    userName = basicInfoList[basicInfoIdx][2]
    doubanId = basicInfoList[basicInfoIdx][3]
    userLink = basicInfoList[basicInfoIdx][4]
    commentNum = basicInfoList[basicInfoIdx][5]
    lastTime = basicInfoList[basicInfoIdx][6]

    logging.info("idx:{0}, title:{1}, href:{2}, userName:{3}, doubanId:{4}, userLink:{5}, commentNum:{6}, lastTime:{7}".format(basicInfoIdx+1, title, href, userName, doubanId, userLink, commentNum, lastTime))
'''

getGroupsInfoList(queryKeywordsList)
