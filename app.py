from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# ---------------------------
# Route: Login Page
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



@app.post("/list_of_tables", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    primavera_url: str = Form(...)
):
    try:
        tables_url = f"{primavera_url}/pds/rest-service/dataservice/metadata/tables?configCode=ds_p6adminuser"
        print("DEBUG → Calling:", tables_url)

        r = requests.get(
            tables_url,
            auth=(username, password),
            headers={"Accept": "application/json"}
        )

        print("DEBUG → Status:", r.status_code)
        print("DEBUG → Response:", r.text[:500])

        if r.status_code != 200:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": f"Primavera error {r.status_code}: {r.text}"
            })

        # FIX: response is already a list of tables
        tables = r.json()

        return templates.TemplateResponse("tables.html", {
            "request": request,
            "tables": tables,
            "username": username,
            "password": password,
            "primavera_url": primavera_url
        })

    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Error: {str(e)}"
        })

# ---------------------------
# Route: Show Columns of Selected Tables
# ---------------------------
@app.post("/columns", response_class=HTMLResponse)
def show_columns(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    primavera_url: str = Form(...),
    tables: list[str] = Form(...)
):
    try:
        selected_columns = {}

        for table in tables:
            # Build URL for each table's columns
            columns_url = f"{primavera_url}/pds/rest-service/dataservice/metadata/columns/{table}?configCode=ds_p6adminuser"

            r = requests.get(
                columns_url,
                auth=(username, password),
                headers={"Accept": "application/json"}
            )

            if r.status_code == 200:
                selected_columns[table] = r.json().get("columns", [])
            else:
                selected_columns[table] = [f"Error {r.status_code}: {r.text}"]

        return templates.TemplateResponse("columns.html", {
            "request": request,
            "columns": selected_columns
        })

    except Exception as e:
        return templates.TemplateResponse("tables.html", {
            "request": request,
            "error": f"Error fetching columns: {str(e)}"
        })
