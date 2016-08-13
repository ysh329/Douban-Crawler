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
from compiler.ast import flatten


################################### PART2 CLASS && FUNCTION ###########################
class Crawler(object):
    # 通过目录页获取列表信息列表
    def getPostsBasicInfoList(self, discussionUrlOfGroup):
        basicInfoList = []

        # 发送请求接受响应并转换为soup对象后抽出结果保存
        request = urllib2.Request(discussionUrlOfGroup)
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
            logging.error("HTTPError code:{0}, URL:{1}".format(e.code, discussionUrlOfGroup))

        return basicInfoList

    # 过滤基本信息列表中的无用条目
    def filterPostsBasicInfoList(self, basicInfoList):
        pass
        return basicInfoList


    # 根据需要的小组数目计算小组信息的目录页
    def getGroupsCategoryUrlList(self, queryKeywordsList, topNGroup=10,
                                findGroupUrl="https://www.douban.com/group/search?start=0&cat=1019&q=[REPLACEBYQUERY]&sort=relevance",
                                maxGroupsNumForEachPage=20):
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

        countPlain = soup.find("span", attrs={"class": "count"}).string
        countNum = int(re.findall('[0-9]\d', countPlain)[0])
        maxPageNum = int(math.ceil(float(countNum) / maxGroupsNumForEachPage))

        pageStartGroupIdxList = map(lambda pageIdx: str(pageIdx * 10), xrange(maxPageNum))
        groupCategoryUrlList = map(lambda start: queryUrl.replace("start=0", "start=" + start),\
                                   pageStartGroupIdxList)
        if topNGroup < len(groupCategoryUrlList) * maxGroupsNumForEachPage:
            groupCategoryUrlList = groupCategoryUrlList[:topNGroup / maxGroupsNumForEachPage + 1]
        logging.info("topNGroup:{0},needPageNum:{1},countNum:{2},maxPageNum:{3},maxGroupsNumForEachPage:{4}"\
                     .format(topNGroup, len(groupCategoryUrlList), countNum, maxPageNum, maxGroupsNumForEachPage)\
                     )
        return groupCategoryUrlList


    # 取出关键标签部分
    def getGroupInfo(self, groupUrl, queryKeywordsList):
        # 发送访问请求和接收
        try:
            request = urllib2.Request(groupUrl)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            logging.error("HTTPError code:{0}, URL:{1}".format(e.code, groupUrl))
        except Exception, e:
            logging.error(e)

        # 读取响应内容并转换为soup对象
        html = response.read()
        soup = BeautifulSoup(html, "lxml")

        # 获取一个小组的所有信息
        # 小组基本信息[9项]组来源、查询、组名、组ID、成员数、组地址、介绍、创建时间、组标签
        # 小组活跃信息[3项]当天帖子总数、当天帖子历史累计回复数、平均帖子回复数
        # 组长信息[3项]管理员姓名、全站唯一性ID、个人页面地址
        # 系统信息[1项]表更新时间

        # 小组基本信息
        groupSource = re.findall(r"www\.(.*)\.com", groupUrl)[0]
        groupQuery = ",".join(queryKeywordsList)
        groupName = soup.title.string.strip()
        groupId = re.findall(r'group/(.*)/', groupUrl)[0]
        try:
            groupMemberNum = re.findall(r'members">浏览所有.* \((.*)\)', html)[0]
        except Exception, e:
            groupMemberNum = '0'
            logging.error(e)
        #groupUrl = groupUrl
        groupIntro = str(soup.findAll("div", attrs={"class": "group-intro"})[0])
        groupBoard = soup.find("div", attrs={"class": "group-board"}).p
        groupCreateDate = re.findall(r"\d{4}-\d{2}-\d{2}", str(groupBoard))[0]
        groupTagList = re.findall('<a class="tag" href=".*>(.*)</a>', html)
        groupTag = ",".join(groupTagList)

        # 小组活跃信息
        allPostInfoList = soup.find("table", attrs={"class":"olt"}).findAll("td", attrs={"class":"", "nowrap":"nowrap"})
        currentDayCommentNumStrList = re.findall(r'<td class="" nowrap="nowrap">(\d*)</td>', str(allPostInfoList))
        currentDayCommentNumIntList = map(lambda s: 0 if s == '' else int(s), currentDayCommentNumStrList)
        currentDayCommentNum = sum(currentDayCommentNumIntList)
        currentDayPostNum = len(currentDayCommentNumStrList)
        currentDayAveCommentNum = int(float(currentDayCommentNum)/currentDayPostNum)

        # 组长信息
        adminName = str(groupBoard.a.string)
        adminUrl = groupBoard.a['href']
        adminId = re.findall('people/(.*)/', adminUrl)[0]

        # 表更新时间
        tableUpdateDate = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

        # print "=============="
        # print groupSource
        # print groupQuery
        # print groupName
        # print groupId
        # print groupMemberNum
        # print groupUrl
        # print groupIntro
        # print groupCreateDate
        # print groupTag
        #
        # print currentDayCommentNum
        # print currentDayPostNum
        # print currentDayAveCommentNum
        #
        # print adminName
        # print adminUrl
        # print adminId
        #
        # print tableUpdateDate
        return (groupSource, groupQuery, groupName, groupId, groupMemberNum,\
                groupUrl, groupIntro, groupCreateDate, groupTag,\
                currentDayPostNum, currentDayCommentNum, currentDayAveCommentNum,\
                adminName, adminId, adminUrl,\
                tableUpdateDate)


    def getGroupUrl(self, groupCategoryUrl):
        # 发送访问请求和接收
        try:
            request = urllib2.Request(groupCategoryUrl)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            logging.error("HTTPError code:{0}, URL:{1}".format(e.code, groupCategoryUrl))
        except Exception, e:
            logging.error(e)

        # 读取响应内容并转换为soup对象
        html = response.read()
        soup = BeautifulSoup(html, "lxml")
        resultOfSoup = soup.find_all("div", attrs={'class': "result"})

        # 遍历抽取重要信息[组名、链接、人数、介绍]
        groupUrlList = []

        for resultIdx in xrange(len(resultOfSoup)):
            try:
                result = resultOfSoup[resultIdx]
                #groupName = "".join(list(result.find("div", attrs={'class':"title"}).strings)).strip()
                groupUrl = result.a.get("href")
                #groupId = re.findall(r'group/(.*)/', groupHref)[0]
                #print groupId
                #groupMemberPlain = result.find("div", attrs={'class':"info"}).string
                #groupMemberNum = int(re.findall('^[0-9]\d*', groupMemberPlain)[0])
                #groupIntro = result.p.string.strip().replace(" ", "").replace("", "")
                #print groupHref
                #groupInfoList.append(groupName, groupHref, groupMemberNum, groupIntro)
                groupUrlList.append(groupUrl)
            except Exception, e:
                logging.error(e)
        return groupUrlList


    # 查找指定关键词的前topNGroup个群组的信息[组名、地址、人数、介绍]
    def getGroupsInfoList(self, queryKeywordsList,
                          topNGroup=10,
                          maxGroupsNumForEachPage=20,
                          findGroupUrl="https://www.douban.com/group/search?start=0&cat=1019&q=[REPLACEBYQUERY]&sort=relevance"):
        # 目录页地址列表
        groupsCategoryUrlList = self.getGroupsCategoryUrlList(queryKeywordsList, topNGroup, findGroupUrl, maxGroupsNumForEachPage)

        # 获取group地址并取topNGroup
        groupsUrl2DList = map(lambda groupCategoryUrl: self.getGroupUrl(groupCategoryUrl), groupsCategoryUrlList)
        groupsUrlList = flatten(groupsUrl2DList)
        groupsUrlList = groupsUrlList[:topNGroup] if len(groupsUrlList) > topNGroup else groupsUrlList

        # 获取group详细信息并取topNGroup
        groupsInfoTupleList = map(lambda groupUrl: self.getGroupInfo(groupUrl, queryKeywordsList), groupsUrlList)
        logging.info("成功获取有关【{0}】 总计 {1} 个小组的详细信息.".format(",".join(queryKeywordsList), len(groupsInfoTupleList)))

        # 获取groupIntroUrl页面的小组详细信息
        return groupsInfoTupleList


################################### PART3 TEST #######################################

# 初始化参数
#discussionUrlOfGroup = "https://www.douban.com/group/HZhome/discussion?start=0"
queryKeywordsList = ["杭州", "租房"]
topNGroup = 5
maxGroupsNumForEachPage = 20
findGroupUrl = "https://www.douban.com/group/search?start=0&cat=1019&q=[REPLACEBYQUERY]&sort=relevance"

# 初始化环境
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
crawler = Crawler()

groupsInfoList = crawler.getGroupsInfoList(queryKeywordsList, topNGroup, maxGroupsNumForEachPage, findGroupUrl)



"""
# 执行爬取
postsBasicInfoList = getPostsBasicInfoList(discussionUrlOfGroup)
#filteredBasicInfoList = filterPostsBasicInfoList(postsBasicInfoList)

# 打印结果
for basicInfoIdx in xrange(len(postsBasicInfoList)):
    title = postsBasicInfoList[basicInfoIdx][0]
    href = postsBasicInfoList[basicInfoIdx][1]
    userName = postsBasicInfoList[basicInfoIdx][2]
    doubanId = postsBasicInfoList[basicInfoIdx][3]
    userLink = postsBasicInfoList[basicInfoIdx][4]
    commentNum = postsBasicInfoList[basicInfoIdx][5]
    lastTime = postsBasicInfoList[basicInfoIdx][6]

    logging.info("idx:{0}, title:{1}, href:{2}, userName:{3}, doubanId:{4}, userLink:{5}, commentNum:{6}, lastTime:{7}".format(basicInfoIdx+1, title, href, userName, doubanId, userLink, commentNum, lastTime))
"""


