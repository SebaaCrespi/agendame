import sqlite3
conn = sqlite3.connect('agendame.db')
c = conn.cursor()
c.execute('SELECT name FROM sqlite_master WHERE type="table"')
print("Tables:", c.fetchall())
for table in ['users', 'refresh_tokens', 'profesionales', 'clientes']:
    c.execute(f'PRAGMA table_info({table})')
    print(f"\n{table}:", c.fetchall())