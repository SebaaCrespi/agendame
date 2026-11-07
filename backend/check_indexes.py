import sqlite3
conn = sqlite3.connect('agendame.db')
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name IN ('profesionales', 'servicios', 'disponibilidades', 'excepciones_disponibilidad')")
for row in cursor.fetchall():
    print(row[0], ':', row[1])
conn.close()