import sqlite3

# Connect to your database
conn = sqlite3.connect("dev.db")
cursor = conn.cursor()

# # Update the status of user with id=2 to 'NoLongerActive'
# user_id = 2
# cursor.execute("UPDATE users SET status = ? WHERE id = ?", ("NoLongerActive", user_id))


# Empty the attendance table
cursor.execute("DELETE FROM attendance")

# empty the ratings table
cursor.execute("DELETE FROM ratings")

# empty the rating_history table
cursor.execute("DELETE FROM rating_history")

# empty the contest_data_snapshots table
cursor.execute("DELETE FROM contest_data_snapshots")

# Reset all user ratings to 1400
cursor.execute("UPDATE users SET rating = 1400")



# Commit changes and close
conn.commit()
conn.close()
