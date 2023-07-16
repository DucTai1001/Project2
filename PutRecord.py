import mysql.connector
from mysql.connector import Error
import pandas as pd

# Kết nối đến MySQL
try:
    connection = mysql.connector.connect(
        host='127.0.0.1',
        database='project2',
        user='root',
        password='taimysql1001'
    )
    if connection.is_connected():
        print('Kết nối thành công!')

except Error as e:
    print('Lỗi kết nối:', e)
    exit()

# Đọc dữ liệu từ pandas DataFrame
dataframe = pd.read_csv('dim_company.csv')  # Thay đổi tên file CSV và các tham số đọc dữ liệu tương ứng

# Chuẩn bị câu truy vấn SQL
query = "INSERT INTO dim_company (Ticker, Company, Sector) VALUES (%s, %s, %s)"
values = [tuple(row) for row in dataframe.values]

# Thực thi truy vấn SQL và xác nhận thay đổi vào cơ sở dữ liệu
try:
    cursor = connection.cursor()
    cursor.executemany(query, values)
    connection.commit()
    print(cursor.rowcount, "dòng đã được thêm vào cơ sở dữ liệu!")

except Error as e:
    print('Lỗi thực thi truy vấn:', e)

# Đóng kết nối với MySQL
cursor.close()
connection.close()

