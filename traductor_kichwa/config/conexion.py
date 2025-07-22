import mysql.connector

def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        port=3308,
        user="root",
        password="",
        database="traductorfinal",
        charset="utf8mb4",
        use_unicode=True
    )
