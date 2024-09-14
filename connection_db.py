import psycopg2

# Здесь код, который может вызвать ошибку декодирования

# ToDo: сделать открытие файла с with

text = open("media\\data\\csv_data.csv", "r", encoding="utf-8").read().split("\n")

conn_db = psycopg2.connect(
    dbname="diploma", user="postgres", password="12345", host="localhost"
)

# Подготовьте SQL-запрос для вставки данных в таблицу.
sql = "INSERT INTO audit (price, count, add_cost, company, product) VALUES (%s, %s, %s, %s, %s)"

# Выполните запрос с использованием подготовленных параметров.
cur = conn_db.cursor()

params = [line.split(",") for line in text[1:-1]]
cur.executemany(sql, params)

conn_db.commit()
"""После этого удаление новый загруженный файл  import sys"""
# с помощью sys можно узнать название файла
# вместо csv_data.csv будет переменная в которой будет название файла
# после удаляем файл

conn_db.close()

# ToDo: Как получилось прочитать csv-файл без pandas?

# def db_insert(new_file):
#     text = open('data\\new_file', 'r', encoding='utf-8').read().split('\n')
#
#     conn_db = psycopg2.connect(
#         dbname='diploma', user='postgres', password='12345', host='localhost'
#     )
#
#     sql = 'INSERT INTO audit (price, count, add_cost, company, product) VALUES (%s, %s, %s, %s, %s)'
#
#     cur = conn_db.cursor()
#
#     params = [line.split(',') for line in text[1:-1]]
#     cur.executemany(sql, params)
#
#     conn_db.commit()
#     conn_db.close()
