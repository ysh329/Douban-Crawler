# -*- coding: utf-8 -*-
################################### PART0 DESCRIPTION #################################
# Filename: db.py
# Description:
#

# E-mail: ysh329@sina.com
# Create: 2016-08-28 23:09:25
# Last:
__author__ = 'yuens'


################################### PART1 IMPORT ######################################


import peewee

databaseName = "DouBan"
hostName = "localhost"
password = "931209"
userName = 'root'
portCode = 3306



#database = peewee.MySQLDatabase('web_db', **{'host': 'localhost', 'password': 'kkd93kd  ', 'port': 3306, 'user': 'root'})
database = peewee.MySQLDatabase(database=databaseName,**{'host': hostName, 'password': password, 'port': portCode, 'user': userName})
