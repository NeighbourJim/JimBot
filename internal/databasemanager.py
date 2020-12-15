import sqlite3
import logging
import pandas as pd

from internal.logs import logger
from internal.enums import WhereType, CompareType

class DB_Manager():
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.path = "./internal/data/databases/"

    def ConnectToDB(self, db_name: str):
        """Attempt to connect to / open a given database.

        Args:
            db_name (str): Name of the database to open.

        Returns:
            bool: Returns True if connection successful.
        """
        try:
            logger.LogPrint(f'Opening database {db_name}.', logging.DEBUG)
            self.connection = sqlite3.connect(f'{self.path}{db_name}.db')
            logger.LogPrint(f'Succesfully opened database {db_name}.', logging.DEBUG)
            return True
        except Exception as ex:
            logger.LogPrint(f'Failed to open database {db_name}. - {ex}', logging.ERROR)
            return ex    

    def CreateTable(self, db_name: str, table_name: str, columns_dict: dict):
        """Create a table in a given database, with a given name, with given column schema.

        Args:
            db_name (str): Name of database to create table in.
            table_name (str): Name of table to create.
            columns_dict (dict): Dictionary containing column schema. Key should be the name of the column and value the datatype and any modifiers.
                                 For example: {"id": "integer PRIMARY KEY AUTOINCREMENT", "name": "text NOT NULL"}

        Returns:
            bool: Returns True if operation successful.
        """
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

    def CheckTableExists(self, db_name: str, table_name: str):
        """Check if a given table exists within a given database.

        Args:
            db_name (str): Database to search.
            table_name (str): Table name to find.

        Returns:
            int: Returns 1 if Table found, returns 0 if not.
        """
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
        """Insert data into given table/database.

        Args:
            db_name (str): Name of database to insert to.
            table_name (str): Name of table to insert to.
            data_dict (dict): Dict containing data to insert. Key should be column name and value should be data.
                              For example: {"id": 42, "name": 'John Foo'}

        Returns:
            bool: Returns True if operation successful.
        """
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
        """Update a given table with provided data.

        Args:
            db_name (str): Database name.
            table_name (str): Table to update.
            data_dict (dict): Dict containing data to update. Key should be column and value should be data.
                              For example: {"name": 'John Foo'} would update name column to 'John Foo'.
            where (dict): Dict containing where clause(s) to restrict by. Key should be column and value should be data.
                          For example: {"id": 42} would equate to the clause "WHERE id = 42" and thus only update records with that ID.

        Returns:
            bool: Returns True if operation successful.
        """
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
        """Delete records from a given table.

        Args:
            db_name (str): Database name.
            table_name (str): Table to delete from.
            where (dict): Dict containing where clause(s) to restrict by. Key should be column and value should be data.
                          For example: {"id": 42} would equate to the clause "WHERE id = 42", and thus delete all records with that ID.

        Returns:
            bool: Returns True if operation successful.
        """
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
        """Retrieve row(s) from a given table.

        Args:
            db_name (str): Database name to access.
            table_name (str): Table name to access.
            where (list of tuples, optional): List containing where clause(s) tuples to restrict by. First half should be column and second half should be data.
            For example: [("id", 42), ("name", "John)] would equate to the clause 'WHERE id = 42 AND/OR name = "John"'. Defaults to None.
            where_type (internal.enums.WhereType, optional): Whether to use AND clause or OR clause. Defaults to AND.
            column_data (list, optional): List of columns to retrieve. Defaults to ["*"].
            rows_required (int, optional): How many records to retrieve. Defaults to 1.
            compare_type (internal.enums.CompareType, optional): Whether to compare with EQUALS or with LIKE. Defaults to CompareType.EQUALS.
            order_by (tuple(str,str), optional): Which column to order by and whether to order ascendingly or descendingly. 
                                                 For example ("id", "desc"). Defaults to None.

        Returns:
            bool: Returns True if operation successful.
        """
        try:
            logger.LogPrint(f'Retrieving from {db_name}', logging.DEBUG)
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

    def ExecuteParamQuery(self, db_name, query, params):
        """Execute a parameterised query.

        Args:
            db_name (str): Database to run query on.
            query (str): The SQL query to run.
                         For example "SELECT * FROM table WHERE name LIKE ?1 AND surname LIKE ?2"
            params (list): Parameters for the query. Will be inserted into query above in the ? slots.

        Returns:
            list: Returns the result of the query.
        """
        try:
            if self.ConnectToDB(db_name):
                self.cursor = self.connection.cursor()
                self.cursor.execute(query, params)
                result = self.cursor.fetchall()
                self.connection.commit()
                self.connection.close()
                return result
        except Exception as ex:
            logger.LogPrint(f'Failed to execute query. DB:{db_name} - Q:{query}. - {ex}', logging.ERROR)

    def ExecuteRawQuery(self, db_name, query):
        """Executes a RAW UNSANITIZED QUERY. This should ONLY be for internal use to do things such as create views. 
           !!!!!!! DO NOT PASS IN USER DATA UNDER ANY CIRCUMSTANCES. !!!!!!!

        Args:
            db_name (str): Database to run query on.
            query (str): SQL query to run.

        Returns:
            list: Results of the query.
        """
        try:
            if self.ConnectToDB(db_name):
                self.cursor = self.connection.cursor()
                result = self.cursor.execute(query).fetchone()
                self.connection.commit()
                self.connection.close()
                return result
        except Exception as ex:
            logger.LogPrint(f'Failed to execute query. DB:{db_name} - Q:{query}. - {ex}', logging.ERROR)

    def ConvertTableToCSV(self, db_name, table_name):
        try:
            if self.ConnectToDB(db_name):
                df = pd.read_sql(f'SELECT * FROM {table_name}', self.connection)
                df.to_csv(f'{self.path}ss-{db_name}.csv')
                return True            
        except Exception as ex:
            logger.LogPrint(f'Failed to write spreadsheet. DB:{db_name} - Q:{query}. - {ex}', logging.ERROR)

dbm = DB_Manager()
