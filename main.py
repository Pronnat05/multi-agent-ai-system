from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import mysql.connector

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------- DATABASE CONNECTION FUNCTION --------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            unix_socket="/cloudsql/projectsub1-491808:asia-south1:assistant-db",
            user="trickyadmin",
            password="tricky123",
            database="assistant_db",
            connection_timeout=5
        )
        print("DB Connected")
        return conn
    except Exception as e:
        print("DB ERROR:", str(e))
        return None


# -------- TOOL FUNCTIONS (MCP) --------

# Task Tools
def add_task(task):
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed"

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks(task, status) VALUES(%s, %s)",
        (task, "pending")
    )
    conn.commit()

    cursor.close()
    conn.close()
    return "Task added successfully"


def get_tasks():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# Notes Tools
def add_note(note):
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed"

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes(note) VALUES(%s)",
        (note,)
    )
    conn.commit()

    cursor.close()
    conn.close()
    return "Note added successfully"


def get_notes():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# Calendar Tools
def add_event(event, date="2026-01-01"):
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed"

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events(event, date) VALUES(%s, %s)",
        (event, date)
    )
    conn.commit()

    cursor.close()
    conn.close()
    return "Event scheduled successfully"


def get_events():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# -------- SUB AGENTS --------

class TaskAgent:
    def handle(self, query):
        if "add" in query:
            return add_task(query)
        elif "show" in query:
            return get_tasks()
        return "Task command not recognized"


class NotesAgent:
    def handle(self, query):
        if "add" in query:
            return add_note(query)
        elif "show" in query:
            return get_notes()
        return "Notes command not recognized"


class CalendarAgent:
    def handle(self, query):
        if "add" in query or "schedule" in query:
            return add_event(query)
        elif "show" in query:
            return get_events()
        return "Calendar command not recognized"


# -------- PRIMARY AGENT --------

class PrimaryAgent:
    def __init__(self):
        self.task_agent = TaskAgent()
        self.notes_agent = NotesAgent()
        self.calendar_agent = CalendarAgent()

    def route(self, query):
        query = query.lower()

        if "task" in query:
            return self.task_agent.handle(query)

        elif "note" in query:
            return self.notes_agent.handle(query)

        elif "meeting" in query or "schedule" in query or "event" in query:
            return self.calendar_agent.handle(query)

        return "Sorry, I could not understand the request"


agent = PrimaryAgent()


# -------- MULTI-STEP WORKFLOW --------

def execute_workflow(query):
    steps = query.split(" and ")
    results = []

    for step in steps:
        result = agent.route(step.strip())
        results.append(result)

    return results


# -------- API ENDPOINTS --------

@app.get("/")
def home():
    return {"message": "Multi-Agent AI System Running"}


@app.post("/execute")
def execute(query: str):
    result = execute_workflow(query)
    return {"response": result}


@app.get("/execute")
def execute_get(query: str):
    try:
        result = execute_workflow(query)
        return {"response": result}
    except Exception as e:
        return {"error": str(e)}