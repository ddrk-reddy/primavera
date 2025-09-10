from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from typing import List, Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# ---------------------------
# Route: Login Page
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ---------------------------
# Route: Fetch Tables
# ---------------------------
@app.post("/list_of_tables", response_class=HTMLResponse)
def list_of_tables(
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

        tables = r.json()
        tables = sorted(tables, key=lambda x: x.get("displayTableName", ""))

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
    tables: List[str] = Form(...)
):
    try:
        selected_columns = {}

        for table in tables:
            columns_url = f"{primavera_url}/pds/rest-service/dataservice/metadata/columns/{table}?configCode=ds_p6adminuser"
            print("DEBUG → Fetching columns for:", table)

            r = requests.get(
                columns_url,
                auth=(username, password),
                headers={"Accept": "application/json"}
            )

            print("DEBUG → Status:", r.status_code)
            print("DEBUG → Response:", r.text[:500])

            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    selected_columns[table] = data
                else:
                    selected_columns[table] = data.get("columns", [])
            else:
                selected_columns[table] = [{"error": f"Error {r.status_code}: {r.text}"}]

        return templates.TemplateResponse("columns.html", {
            "request": request,
            "columns": selected_columns,
            "username": username,
            "password": password,
            "primavera_url": primavera_url
        })

    except Exception as e:
        return templates.TemplateResponse("tables.html", {
            "request": request,
            "error": f"Error fetching columns: {str(e)}"
        })


# ---------------------------
# Route: Display Data
# ---------------------------
@app.post("/data", response_class=HTMLResponse)
def display_data(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    primavera_url: str = Form(...),
    selected_columns: Optional[List[str]] = Form(None)
):
    if not selected_columns:
        return templates.TemplateResponse("columns.html", {
            "request": request,
            "error": "⚠️ You must select at least one column.",
            "columns": {},  # you could re-fetch if you want
            "username": username,
            "password": password,
            "primavera_url": primavera_url
        })

    # ✅ Build table-to-columns mapping
    tables_dict = {}
    for col in selected_columns:
        table, column = col.split(":")
        tables_dict.setdefault(table, []).append(column)

    payload = {
        "name": "MyQuery",
        "sinceDate": None,
        "tables": [{"tableName": t, "columns": cols} for t, cols in tables_dict.items()]
    }

    print("DEBUG → Payload:", payload)

    try:
        r = requests.post(
            f"{primavera_url}/pds/rest-service/dataservice/runquery?configCode=ds_p6adminuser",
            json=payload,
            auth=(username, password),
            headers={"Accept": "application/json"}
        )

        print("DEBUG → Status:", r.status_code)
        print("DEBUG → Response:", r.text[:500])

        if r.status_code != 200:
            return templates.TemplateResponse("data.html", {
                "request": request,
                "error": f"Error {r.status_code}: {r.text}",
                "data": None,
                "username": username,
                "password": password,
                "primavera_url": primavera_url,
                "tables": list(tables_dict.keys())  # ✅ send tables back
            })

        data = r.json()

        return templates.TemplateResponse("data.html", {
            "request": request,
            "data": data,
            "username": username,
            "password": password,
            "primavera_url": primavera_url,
            "tables": list(tables_dict.keys())  # ✅ send tables back
        })

    except Exception as e:
        return templates.TemplateResponse("data.html", {
            "request": request,
            "error": f"Exception: {str(e)}",
            "data": None,
            "username": username,
            "password": password,
            "primavera_url": primavera_url,
            "tables": list(tables_dict.keys())  # ✅ send tables back
        })