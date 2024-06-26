from enum import Enum
import pymysql
#from mysql.connector import Error
from pymysql import Error
import json

class CRUD(Enum):
    CREATE = 1,
    READ = 2,
    UPDATE = 3,
    DELETE = 4, 
    ALTER = 5


class DBResponse:
    def __init__(self, status, row = None, rows = None):
        self.status = status
        if row is not None:
            self.row = row
        else:
            self.row = None
        if rows is not None:
            self.rows = rows
        else:
            self.rows = []
    def __str__(self):
        return json.dumps(self.__dict__)

class DB:
    db = None
    def __runQuery(op, isMany, queryString, args = None):
        response = None
        #print(f"query {queryString} args {args}")
        try:
            db = DB.getDB()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            status = False
            if not isMany or op == CRUD.READ:
                if args is not None and len(args) > 0:
                    if type(args[0]) is dict:
                        args = {k: v for d in args for k, v in d.items()}
                    status = cursor.execute(queryString, args)
                else:
                    
                    status = cursor.execute(queryString)
            else:
                if args is not None and len(args) > 0:
                    status = cursor.executemany(queryString, args)
                else:
                    status = cursor.executemany(queryString)
            if op == CRUD.READ:
                if not isMany:
                    result = cursor.fetchone()
                    # response = {"status": True if status is None else False, "row": result}
                    
                    status = True if status >= 0 else False
                    response = DBResponse(status, result)
                else:
                    result = cursor.fetchall()
                    print(f"db.py status {status}")
                    status = True if status >= 0 else False
                    response = DBResponse(status, None, result)
            else:
                if op != CRUD.ALTER:
                    db.commit()
                status = True if status >= 0 else False
                response = DBResponse(status)
            try:
                cursor.close()
            except Exception as ce:
                print("cursor close error", ce)
        
        except Error as e:
            #if e.errno == -1:
            if e.args[0] == -1:
                DB.close()
            # converting to a plain exception so other modules don't need to import mysql.connector.Error
            # this will let you more easily swap out DB connectors without needing to refactor your code, just this class
            raise Exception(e)
        return response 

    @staticmethod
    def delete(queryString, *args):
        return DB.__runQuery(CRUD.DELETE, False, queryString, args)
        
    @staticmethod
    def update(queryString, *args):
        return DB.__runQuery(CRUD.UPDATE, False, queryString, args)

    @staticmethod
    def query(queryString):
        if "CREATE TABLE" in queryString.upper():
            return DB.__runQuery(CRUD.CREATE, False, queryString)
        elif queryString.upper().startswith("ALTER"):
            return DB.__runQuery(CRUD.ALTER, False, queryString)
        else:
            return DB.__runQuery(CRUD.ALTER, False, queryString)
            #raise Exception("Please use one of the abstracted methods for this query")

    @staticmethod
    def insertMany(queryString, data):
        return DB.__runQuery(CRUD.CREATE, True, queryString, data)

    @staticmethod
    def insertOne(queryString, *args):
        return DB.__runQuery(CRUD.CREATE, False, queryString, args)


    @staticmethod
    def selectAll(queryString, *args):
        return DB.__runQuery(CRUD.READ, True, queryString, args)


    @staticmethod
    def selectOne(queryString, *args):
        return DB.__runQuery(CRUD.READ, False, queryString, args)
    
    @staticmethod
    def close():
        try:
            DB.db.close()
        except:
            pass
        DB.db = None

    @staticmethod
    def getDB():
        if DB.db is None or DB.db.open == False:
            #import mysql.connector
            #import pymysql
            import os
            import re
            from dotenv import load_dotenv
            load_dotenv()
            db_url  = os.environ.get("DB_URL")
            from urllib.parse import urlparse
            url = urlparse(db_url)
            if url:
                user = url.username
                password = url.password
                host = url.hostname
                port = url.port
                database = url.path.strip("/")
                try:
                    DB.db =  pymysql.connect(host=host, user=user, password=password, database=database, port=int(port))
                except Error as e:
                    print("Error while connecting to MySQL", e)
                    raise e
            else: # old logic as fallback
                data = re.findall("mysql:\/\/(\w+):(\w+)@([\w\.]+):([\d]+)\/([\w]+)", db_url)
                if len(data) > 0:
                    data = data[0]
                    if len(data) >= 5:
                        try:
                            user,password,host,port,database = data
                            #DB.db = mysql.connector.connect(host=host, user=user, password=password, database=database, port=port,
                            DB.db = pymysql.connect(host=host, user=user, password=password, database=database, port=int(port))
                        except Error as e:
                            print("Error while connecting to MySQL", e)
                            raise e
                    else:
                        raise Exception("Missing connection details")
                else:
                    raise Exception("Invalid connection string")
        return DB.db

if __name__ == "__main__":
    # verifies connection works
    print(DB.selectOne("SELECT 'test' from dual"))