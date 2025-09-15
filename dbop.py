import sqlite3

# Connect to your database
conn = sqlite3.connect("dev.db")
cursor = conn.cursor()

# Delete a specific row
user_id = 1
cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

# Commit changes and close
conn.commit()
conn.close()
