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
    def getGroupInfoDict(self, groupUrl, queryKeywordsList):
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
        groupInfoDict = {}

        # 小组基本信息
        groupInfoDict['groupSource'] = re.findall(r"www\.(.*)\.com", groupUrl)[0]
        groupInfoDict['groupQuery'] = ",".join(queryKeywordsList)
        groupInfoDict['groupName'] = soup.title.string.strip()
        groupInfoDict['groupId'] = re.findall(r'group/(.*)/', groupUrl)[0]
        try:
            groupInfoDict['groupMemberNum'] = int(re.findall(r'members">浏览所有.* \((.*)\)', html)[0])
        except Exception, e:
            groupInfoDict['groupMemberNum'] = 0
            logging.error(e)
        groupInfoDict['groupUrl'] = groupUrl
        groupInfoDict['groupIntro'] = str(soup.findAll("div", attrs={"class": "group-intro"})[0])
        groupBoard = soup.find("div", attrs={"class": "group-board"}).p
        groupInfoDict['groupCreateDate'] = re.findall(r"\d{4}-\d{2}-\d{2}", str(groupBoard))[0]
        groupTagList = re.findall('<a class="tag" href=".*>(.*)</a>', html)
        groupInfoDict['groupTag'] = ",".join(groupTagList)

        # 小组活跃信息
        allPostInfoList = soup.find("table", attrs={"class":"olt"}).findAll("td", attrs={"class":"", "nowrap":"nowrap"})
        currentDayCommentNumStrList = re.findall(r'<td class="" nowrap="nowrap">(\d*)</td>', str(allPostInfoList))
        currentDayCommentNumIntList = map(lambda s: 0 if s == '' else int(s), currentDayCommentNumStrList)
        groupInfoDict['currentDayCommentNum'] = sum(currentDayCommentNumIntList)
        groupInfoDict['currentDayPostNum'] = len(currentDayCommentNumStrList)
        groupInfoDict['currentDayAveCommentNum'] = int(float(groupInfoDict['currentDayCommentNum']/groupInfoDict['currentDayPostNum']))

        # 组长信息
        groupInfoDict['adminName'] = str(groupBoard.a.string)
        groupInfoDict['adminUrl'] = groupBoard.a['href']
        groupInfoDict['adminId'] = re.findall('people/(.*)/', groupInfoDict['adminUrl'])[0]

        # 表更新时间
        groupInfoDict['tableUpdateDate'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

        return groupInfoDict

    # 根据小组查询结果页面Url获取小组groupUrl
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

        # 依次获取groupUrl
        groupUrlList = []
        for resultIdx in xrange(len(resultOfSoup)):
            try:
                result = resultOfSoup[resultIdx]
                groupUrl = result.a.get("href")
                groupUrlList.append(groupUrl)
            except Exception, e:
                logging.error(e)
        return groupUrlList


    # 查找指定关键词的前topNGroup个群组的信息[组名、地址、人数、介绍]
    def getGroupsInfoDictList(self, queryKeywordsList,
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
        groupsInfoDictList = map(lambda groupUrl: self.getGroupInfoDict(groupUrl, queryKeywordsList), groupsUrlList)
        logging.info("成功获取有关【{0}】 总计 {1} 个小组的详细信息.".format(",".join(queryKeywordsList), len(groupsInfoDictList)))
        return groupsInfoDictList


    # 获取小组当天所有帖子链接
    def getTodayPostUrlListOfGroup(self, groupUrl):
        # 发送访问请求和接收
        logging.info("groupUrl:{0}".format(groupUrl))
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

        # 解析soup对象获取所有帖子链接
        postTitlesOfSoup = soup.find_all("td", attrs={"class": "title"})
        postUrlList = map(lambda tag: tag.a['href'], postTitlesOfSoup)
        logging.info("成功获得 {0} 个帖子链接.".format(len(postUrlList)))
        return postUrlList


    def getPostDetailInfoDict(self, postUrl):
        logging.info("postUrl:{0}".format(postUrl))
        # 发送访问请求和接收
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",\
                       'Referer': postUrl,\
                       'Accept':'*/*',\
                       #'Accept-Encoding':'gzip, deflate, sdch',\
                       'Accept-Encoding':'utf8',\
                       'Accept-Language':'zh-CN,zh;q=0.8',\
                       'Connection':'keep-alive',\
                       'Cookie':'bid=7xWCDDoU6pk; gr_user_id=78b1ca83-183c-49ee-b79c-c7db9f211ad4; viewed="26308725_25753386"; ps=y; ll="118172"; ct=y; ap=1; as="https://www.douban.com/group/topic/85508155/"; _vwo_uuid_v2=4967D4925ED4A7F3DAB6ACBF56139020|ea6d135f73d347c2b2bd567e10a10b4b; __utmt=1; _ga=GA1.2.1582242860.1470147765; _gat=1; __utma=30149280.1582242860.1470147765.1471179208.1471182104.19; __utmb=30149280.18.5.1471182180158; __utmc=30149280; __utmz=30149280.1470802677.13.8.utmcsr=121.42.47.99|utmccn=(referral)|utmcmd=referral|utmcct=/yuenshome/wordpress/',\
                       #XX 'Host':'erebor.douban.com',
                        }
            request = urllib2.Request(postUrl, headers=headers,origin_req_host='erebor.douban.com')
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            logging.error("HTTPError code:{0}, URL:{1}".format(e.code, postUrl))
        except Exception, e:
            logging.error(e)

        # 读取响应内容并转换为soup对象
        html = response.read()
        soup = BeautifulSoup(html, "lxml")
        postContent = soup.find("div", attrs={"class":"topic-content clearfix"})
        postComment = soup.find("ul", attrs={"id":"comments", "class":"topic-reply"})

        # [4项]小组地址、来源、组全站唯一性ID、小组名称
        # [7项]帖子链接、标题、ID、创建时间、最后回复时间、回复个数、喜欢人数
        # [3项]作者姓名、ID、签名、个人地址
        # [5项]内容、图片张数、图片地址列表字符串、作者评论、作者评论个数
        # [4项]QQ、微信号、电话号、包含地名
        postDetailInfoDict = {}

        # 小组来源、组全站唯一性ID、小组名称
        try:
            postDetailInfoDict['groupUrl'] = re.findall('<a href="(.*)\?ref=sidebar">', html)[0].encode("utf8")
        except:
            postDetailInfoDict['groupUrl'] = re.findall('<a href="(.*)#topics', str(soup))[0].encode("utf8")
        postDetailInfoDict['groupSource'] = re.findall('www\.(.*)\.com', postDetailInfoDict['groupUrl'])[0].encode("utf8")
        postDetailInfoDict['groupId'] = re.findall('group/(.*)/', postDetailInfoDict['groupUrl'])[0].encode("utf8")
        postDetailInfoDict['groupName'] = re.findall('/\?ref=sidebar">(.*)</a>', html)[1].encode("utf8")

        logging.info("postDetailInfoDict['groupUrl']:{0}".format(postDetailInfoDict['groupUrl']))
        logging.info("postDetailInfoDict['groupSource']:{0}".format(postDetailInfoDict['groupSource']))
        logging.info("postDetailInfoDict['groupId']:{0}".format(postDetailInfoDict['groupId']))
        logging.info("postDetailInfoDict['groupName']:{0}".format(postDetailInfoDict['groupName']))

        # 帖子链接、标题、ID、创建时间、最后回复时间、回复个数、喜欢人数
        postDetailInfoDict['postUrl'] = postUrl
        # postTitle
        try: # 查找是否存在长标题的标签并匹配
            postDetailInfoDict['postTitle'] = re.findall('<strong>标题：</strong>(.*)</td><td class="tablerc"></td></tr>', str(postContent))[0].encode("utf8")
        except:
            postDetailInfoDict['postTitle'] = soup.title.text.strip().encode('utf8')
        postDetailInfoDict['postCreateDate'] = str(postContent.find("span", attrs={"class":"color-green"}).string).strip().encode("utf8")
        postDetailInfoDict['postCommentNum'] = (len(postComment)-1)/2
        # postLastCommentDate
        if postDetailInfoDict['postCommentNum'] > 0:
            postDetailInfoDict['postLastCommentDate'] = re.findall('<span class="pubtime">(.*)</span>', html)[-1].encode("utf8") if html.count('paginator') == 0 else self.getPostLastCommentDate(soup).encode("utf8")
        else:
            postDetailInfoDict['postLastCommentDate'] = postDetailInfoDict['postCreateDate'].encode("utf8")

        try:
            postDetailInfoDict["postLikeNum"] = int(re.findall(u'type=like#sep">(\d*).*</a>', str(postContent))[0])
        except:
            postDetailInfoDict["postLikeNum"] = 0

        logging.info("postDetailInfoDict['postUrl']:{0}".format(postDetailInfoDict['postUrl']))
        logging.info("postDetailInfoDict['postTitle']:{0}".format(postDetailInfoDict['postTitle']))
        logging.info("postDetailInfoDict['postCreateDate']:{0}".format(postDetailInfoDict['postCreateDate']))
        logging.info("postDetailInfoDict['postCommentNum']):{0}".format(postDetailInfoDict['postCommentNum']))
        logging.info("postDetailInfoDict['postLastCommentDate']:{0}".format(postDetailInfoDict['postLastCommentDate']))
        logging.info("postDetailInfoDict['postLikeNum']:{0}".format(postDetailInfoDict['postLikeNum']))

        # 作者姓名、ID、签名、个人地址
        postDetailInfoDict['postAuthorName'] = re.findall('alt="(.*)" class="pil"', str(postContent))[0].encode("utf8")
        postDetailInfoDict['postAuthorUrl'] = re.findall('(https://www\.douban\.com/people/.*/)"><img', str(postContent))[0].encode("utf8")
        postDetailInfoDict['postAuthorId'] = re.findall('https://www\.douban\.com/people/(.*)/"><img', str(postContent))[0].encode("utf8")
        try:
            postDetailInfoDict['postAuthorSignature'] = re.findall('</a>\((.*)\)</span>', str(postContent))[0].encode("utf8")
        except:
            postDetailInfoDict['postAuthorSignature'] = "".encode("utf8")

        logging.info("postDetailInfoDict['postAuthorName']:{0}".format(postDetailInfoDict['postAuthorName']))
        logging.info("postDetailInfoDict['postAuthorUrl']:{0}".format(postDetailInfoDict['postAuthorUrl']))
        logging.info("postDetailInfoDict['postAuthorId']:{0}".format(postDetailInfoDict['postAuthorId']))
        logging.info("postDetailInfoDict['postAuthorSignature']:{0}".format(postDetailInfoDict['postAuthorSignature']))

        # 内容、图片张数、图片地址列表字符串、作者评论、作者评论个数
        postDetailInfoDict['postContent'] = postContent.find("div", attrs={"class":"topic-content"}).text.replace("\r", "").replace("\n", "").replace(" ", "").encode("utf8")
        postImgTags = postContent.find_all("img", attrs={"class":""})
        postDetailInfoDict['postImgNum'] = len(postImgTags)
        if postDetailInfoDict['postImgNum'] > 0:
            postImgUrlList = map(lambda tag: tag['src'].encode("utf8"), postImgTags)
            postDetailInfoDict['postImgUrlList'] = u'\t'.join(postImgUrlList).encode("utf8")
        else:
            postDetailInfoDict['postImgUrlList'] = u''.encode("utf8")

        if postDetailInfoDict['postCommentNum'] >= 1:
            #commentUserNameList = re.findall(r'<a href="https://www\.douban\.com/people/135813880/" class="">(.*)</a>', str(postComment))
            commentUserNameTagList = postComment.find_all('a', attrs={"href":postDetailInfoDict['postAuthorUrl'], 'class':''})
            print len(commentUserNameTagList)
            commentUserNameList = commentUserNameTagList#map(lambda tag: tag.a, commentUserNameTagList)
            commentContentList = re.findall('<p class="">(.*)</p>', str(postContent))
            userNameAndCommentContentList = map(lambda name, comment: (name, comment), commentUserNameList, commentContentList)

            authorCommentList = filter(lambda name: postDetailInfoDict['postAuthorName'] in name, userNameAndCommentContentList)
            postDetailInfoDict['postAuthorCommentNum'] = len(authorCommentList)
            postDetailInfoDict['postAuthorComment'] = "".join(map(lambda (name, comment): comment, authorCommentList)).encode("utf8")


        logging.info("postDetailInfoDict['postContent']:{0}".format(postDetailInfoDict['postContent']))
        #logging.info("len(postDetailInfoDict['postContent']):{0}".format(len(postDetailInfoDict['postContent'])))

        logging.info("postDetailInfoDict['postImgNum']:{0}".format(postDetailInfoDict['postImgNum']))
        logging.info("postImgUrlList:{0}".format(postImgUrlList))
        logging.info("postDetailInfoDict['postImgUrlList']:{0}".format(postDetailInfoDict['postImgUrlList']))

        #logging.info("str(postContent):{0}".format(str(postComment)))
        logging.info("commentUserNameList:{0}".format(commentUserNameList))
        logging.info("len(commentUserNameList):{0}".format(len(commentUserNameList)))
        logging.info("commentContentList:{0}".format(commentContentList))
        logging.info("len(commentContentList):{0}".format(len(commentContentList)))

        logging.info("postDetailInfoDict['postAuthorComment']:{0}".format(postDetailInfoDict['postAuthorComment']))
        logging.info("postDetailInfoDict['postAuthorCommentNum']:{0}".format(postDetailInfoDict['postAuthorCommentNum']))




        logging.info("================================================================")




    # 获取最后一条评论的日期
    def getPostLastCommentDate(self, soup):
        pageContent = soup.find_all('div', attrs={'class': "paginator"})
        pageUrlList = re.findall('<a href="(.*)">\d*', str(pageContent))
        logging.info("len(pageUrlList):{0}".format(len(pageUrlList)))
        for idx in xrange(len(pageUrlList)): logging.info("{0}:{1}".format(idx+1, pageUrlList[idx]))




################################### PART3 TEST #######################################

# 初始化参数
queryKeywordsList = ["杭州", "租房"]
topNGroup = 1
maxGroupsNumForEachPage = 20
findGroupUrl = "https://www.douban.com/group/search?start=0&cat=1019&q=[REPLACEBYQUERY]&sort=relevance"

# 初始化环境
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
crawler = Crawler()

#crawler.getPostDetailInfoDict("https://www.douban.com/group/topic/83083253/")
crawler.getPostDetailInfoDict("https://www.douban.com/group/topic/88272843/")

# # 获取指定关键词下的小组详细信息
# groupsInfoDictList = crawler.getGroupsInfoDictList(queryKeywordsList,\
#                                                    topNGroup,\
#                                                    maxGroupsNumForEachPage,\
#                                                    findGroupUrl)
#
# # 获取指定小组(链接)的所有今日帖子地址
# postUrl2DList = map(lambda groupInfoDict:\
#                         crawler.getTodayPostUrlListOfGroup(groupInfoDict['groupUrl']),\
#                     groupsInfoDictList)
# postUrlList = flatten(postUrl2DList)
#
# # 根据帖子地址获取帖子详细信息
# postsDetailInfoDictList = map(lambda postUrl:\
#                                   crawler.getPostDetailInfoDict(postUrl),\
#                               postUrlList)
#
