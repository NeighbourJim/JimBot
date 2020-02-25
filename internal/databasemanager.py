import sqlite3
import logging

from internal.helpers import Helper
from internal.logs import logger
from internal.enums import WhereType, CompareType

class DB_Manager():
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.path = "./internal/data/databases/"

    def ConnectToDB(self, db_name):
        try:
            logger.LogPrint(f'Opening database {db_name}.', logging.DEBUG)
            self.connection = sqlite3.connect(f'{self.path}{db_name}.db')
            logger.LogPrint(f'Succesfully opened database {db_name}.', logging.DEBUG)
            return True
        except Exception as ex:
            logger.LogPrint(f'Failed to open database {db_name}. - {ex}', logging.ERROR)
            return ex    

    def CreateTable(self, db_name, table_name, columns_dict):
        try:            
            columns = ''
            if self.ConnectToDB(db_name):
                self.cursor = self.connection.cursor()
                for column, args in columns_dict.items():
                    columns += f'{column} {args}, '
                columns = columns[:-2]
                sql_query = f'CREATE TABLE {table_name} ({columns})'
                logger.LogPrint(f'Table Create Statement {sql_query}.', logging.DEBUG)
                self.cursor.execute(sql_query)
                self.connection.commit()
                self.connection.close()
                return True
        except Exception as ex:
            logger.LogPrint(f'Failed to create {table_name} in {db_name}. - {ex}', logging.ERROR)
            return ex

    def CheckTableExists(self, db_name, table_name):
        try:
            if self.ConnectToDB(db_name):
                self.cursor = self.connection.cursor()
                sql_query = f"SELECT count(*) FROM {db_name} WHERE type='table' AND name='{table_name}';"
                self.cursor.execute(sql_query)
                result = self.cursor.fetchone()                
                self.connection.close()
                return result
        except Exception as ex:
            logger.LogPrint(f'Failed to check if {table_name} in {db_name}. - {ex}', logging.ERROR)

    def Insert(self, db_name, table_name, data_dict):
        try:
            if self.ConnectToDB(db_name):
                columns = []
                values = []
                params = ""
                self.cursor = self.connection.cursor()
                for item in data_dict.items():
                    columns.append(item[0])
                    values.append(item[1])
                    params += "?,"
                params = params[:-1]
                sql_query = f"INSERT INTO {table_name}({','.join(columns)}) VALUES({params});"
                self.cursor.execute(sql_query,values)
                self.connection.commit()
                self.connection.close()
                logger.LogPrint(f'Inserted to database {db_name} - {table_name}.', logging.DEBUG)
                return True               
        except Exception as ex:
            logger.LogPrint(f'Failed to insert to database {db_name}. - {ex}', logging.ERROR)
            return ex

    def Update(self, db_name, table_name, data_dict, where):
        try:
            if self.ConnectToDB(db_name):
                columns = []
                values = []
                where_values = []
                where_clause = ""
                self.cursor = self.connection.cursor()
                for d in data_dict.items():
                    columns.append(d[0])
                    values.append(d[1])
                for w in where.items():
                    where_clause += f"{w[0]} = ? AND "
                    where_values.append(w[1])
                where_clause = where_clause[:-4]
                sql_query = f'UPDATE {table_name} SET {"=?, ".join(columns)}=? WHERE {where_clause}'
                self.cursor.execute(sql_query,values + where_values)
                self.connection.commit()
                self.connection.close()
                logger.LogPrint(f'Updated {db_name} - {table_name}.', logging.DEBUG)
                return True 
        except Exception as ex:
            logger.LogPrint(f'Failed to update {db_name} - {table_name}. - {ex}', logging.ERROR)
            return ex

    def Delete(self, db_name, table_name, where):
        try:
            if self.ConnectToDB(db_name):
                where_values = []
                where_clause = ""
                self.cursor = self.connection.cursor()
                for w in where.items():
                    where_clause += f"{w[0]} = ? AND "
                    where_values.append(w[1])
                where_clause = where_clause[:-4]
                sql_query = f'DELETE FROM {table_name} WHERE {where_clause}'
                affected = self.cursor.execute(sql_query,where_values).rowcount
                self.connection.commit()
                self.connection.close()
                logger.LogPrint(f'Deleted from {db_name} - {table_name}.', logging.DEBUG)
                return affected 
        except Exception as ex:
            logger.LogPrint(f'Failed to delete from {db_name} - {table_name}. - {ex}', logging.ERROR)
            return ex

    def Retrieve(self, db_name, table_name, where = None, where_type=WhereType.AND, column_data = ["*"], rows_required = 1, compare_type = CompareType.EQUALS, order_by=None):
        try:
            if self.ConnectToDB(db_name): 
                columns = []
                where_values = []
                where_clause = ""
                
                self.cursor = self.connection.cursor()
                for c in column_data:
                    columns.append(c)
                sql_query = f"SELECT {','.join(columns)} FROM {table_name}"
                if where != None:
                    for w in where:
                        if where_type == WhereType.AND:
                            if compare_type == CompareType.EQUALS:
                                where_clause += f"{w[0]} = ? AND "
                            else:
                                where_clause += f"{w[0]} LIKE ? AND "
                        else:
                            if compare_type == CompareType.EQUALS:
                                where_clause += f"{w[0]} = ? OR  "
                            else:
                                where_clause += f"{w[0]} LIKE ? OR  "
                        where_values.append(w[1])
                    where_clause = where_clause[:-4]
                    sql_query += f" WHERE {where_clause}"
                if order_by != None:
                    sql_query += f" ORDER BY {order_by[0]} {order_by[1]}"
                self.cursor.execute(sql_query, where_values)
                result = self.cursor.fetchmany(rows_required)
                logger.LogPrint(f'Retrieved from {db_name}: {result}', logging.DEBUG)
                self.connection.close()
                return result
        except Exception as ex:
            logger.LogPrint(f'Failed to retrieve from {db_name} - {table_name}. - {ex}', logging.ERROR)
            return ex

    def ExecuteRawQuery(self, db_name, query):
        '''Executes a RAW UNSANITIZED QUERY. This should ONLY be for internal use to do things such as create views. DO NOT PASS IN USER DATA.'''
        try:
            if self.ConnectToDB(db_name):
                self.cursor = self.connection.cursor()
                result = self.cursor.execute(query).fetchone()
                self.connection.commit()
                self.connection.close()
                return result
        except Exception as ex:
            logger.LogPrint(f'Failed to execute query. DB:{db_name} - Q:{query}. - {ex}', logging.ERROR)


dbm = DB_Manager()
