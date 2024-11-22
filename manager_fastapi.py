from fastapi import FastAPI, Request
import mysql.connector
from mysql.connector import Error

app = FastAPI()

# Database connection settings
db_config = {
    "host": "localhost",  # actual host if not local
    "user": "samnaz",
    "password": "1234560",  # actual password
    "database": "sakila"
}

# Establish a connection to the database
def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            connection.autocommit = True  # Enable auto-commit
            print("Successfully connected to the database")
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

        
@app.get("/")
async def root():
    return {"message": "Manager is running!"}

@app.post("/execute")
async def execute_query(request: Request):
    try:
        # Get the query from the request
        data = await request.json()
        query = data.get("query")
        if not query:
            return {"error": "No query provided"}
        if "select" in query.lower():
            query_type = "read"
        else:
            query_type = "write"

        # Connect to the database
        connection = connect_to_database()
        if connection is None:
            return {"error": "Database connection failed"}

        # Execute the query
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        #result = cursor.fetchall()  # Fetch all results of the query
        #result = cursor.fetchall() if query_type == "read" else []  # Fetch results only for read queries
        if query_type == "read":
            result = cursor.fetchall()  # Fetch results for SELECT queries
        else:
            result = {"affected_rows": cursor.rowcount}  # Get number of affected rows for write queries
        cursor.close()
        connection.close()

        

        return {"status": "success", "type": query_type, "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    except Error as db_error:
        print(f"Database error: {db_error}")
        return {"status": "error", "message": str(db_error)}
