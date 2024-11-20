from fastapi import FastAPI, Request
import mysql.connector
from mysql.connector import Error

app = FastAPI()

# Database connection settings
db_config = {
    "host": "localhost",  # Replace with the actual host if not local
    "user": "samnaz",
    "password": "1234560",  # Replace with the actual password
    "database": "sakila"
}

# Establish a connection to the database
def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Successfully connected to the database")
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None
        
@app.get("/")
async def root():
    return {"message": "Worker is running!"}

@app.post("/execute")
async def execute_query(request: Request):
    try:
        # Get the query from the request
        data = await request.json()
        query = data.get("query")
        if not query:
            return {"error": "No query provided"}

        # Connect to the database
        connection = connect_to_database()
        if connection is None:
            return {"error": "Database connection failed"}

        # Execute the query
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()  # Fetch all results of the query
        cursor.close()
        connection.close()

        return {"status": "success", "type": "read", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
