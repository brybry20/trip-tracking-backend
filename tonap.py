import sqlite3
from werkzeug.security import generate_password_hash

# Connect to database
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

# Reset admin password to 'admin123'
new_password = generate_password_hash('admin123')
cursor.execute('''
    UPDATE users 
    SET password_hash = ? 
    WHERE username = 'admin'
''', (new_password,))

conn.commit()
conn.close()

print("✅ Admin password has been reset to 'admin123'")