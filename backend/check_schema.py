import sqlite3
conn = sqlite3.connect('agendame.db')
c = conn.cursor()
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='turnos'")
print("TURNOs:")
print(c.fetchone()[0])
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='clientes'")
print("\nCLIENTES:")
print(c.fetchone()[0])