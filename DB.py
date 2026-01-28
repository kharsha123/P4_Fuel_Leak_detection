
"""
===========================================================================
Author       :  Aastha
Created on   :  19-09-2024
Purpose      :  Standardise the codings
Modified on  :  
M.Purpose    :  
Version      :  1.0
===========================================================================
"""

import os
import pandas as pd
import pypyodbc as pyodbc

# drvr = os.environ.get("drvr")
drvr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.121.2.218;DATABASE=Vision_System;uid=AIML;pwd=I0TaiML123#;Pooling=True;Connection Timeout=120;'
#==============================================================================================
def mssql_read_data(sql,driver=drvr):
    try:
        # print(Config.drivers)
        conn = pyodbc.connect(driver, autocommit=True)
        pyodbc.pooling = True
        df = pd.read_sql(sql, conn)
        #print("Data read from mssql done")
        return df
    except Exception as ee:
        print( str( ee ) )
    # finally:
    #     conn.close()
#==============================================================================================
def mssql_insert_data(_sql,drivers=drvr):
    try:
        # global drivers
        sql_conn = pyodbc.connect(drivers, autocommit=False)
        pyodbc.pooling = True
        mycursor = sql_conn.cursor()
        mycursor.execute(_sql)
        mycursor.commit()
        mycursor.close()
        #sql_conn.close()
        print("Data inserted in DB")
    except Exception as ee:
        print("Data insertion error:",str(ee))
    finally:
        sql_conn.close()
# ========================================================================================
