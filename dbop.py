import sqlite3

# Connect to your database
conn = sqlite3.connect("dev.db")
cursor = conn.cursor()

# Update the role of user with id=1 to 'Admin'
# user_id = 1
# cursor.execute("UPDATE users SET role = ? WHERE id = ?", ("Admin", user_id))


# Empty the attendance table
cursor.execute("DELETE FROM attendance")

# Commit changes and close
conn.commit()
conn.close()
