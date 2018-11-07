import psycopg2

# Connect to the postgres
conn = psycopg2.connect(dbname="referral", user='postgres', password='amazon', host= "35.225.56.214")
print("You're in boi!!")
conn.close()