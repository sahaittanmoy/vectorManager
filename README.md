# 🗄️ Weaviate Manager

A lightweight Flask web application for managing a remote [Weaviate](https://weaviate.io/) vector database — no CLI required.

---

## Features

| Feature | Details |
|---------|---------|
| **Connect** | Enter an HTTP URL + optional API key to connect to any remote Weaviate instance |
| **Collections** | List, create, and delete collections; view metadata and multi-tenancy status |
| **Collection Properties** | View, edit descriptions, add new schema properties, and delete properties across documents |
| **Tenants** | View, create, delete, and **toggle status between Active (HOT) and Inactive (COLD)** |
| **Tenant Description** | View and update dedicated tenant-level descriptions (e.g. table/view summary) |
| **Property Values** | View all properties and their values across objects inside each tenant |
| **Document Property Editor** | **Edit or delete individual document properties**, add new fields, or edit full JSON |
| **Documents** | Browse documents, upload new ones (JSON), delete by UUID |
| **Search** | Filter documents and properties inline in real-time |

---

## Prerequisites

- Python **3.9+**
- A running Weaviate instance accessible over HTTP (local or remote)

---

## Setup

### 1. Clone / navigate to the project

```bash
cd /path/to/VectorManager
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

```bash
# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
# Make sure the venv is active, then:
python app.py
```

The server starts on **http://localhost:5000** (also reachable on the local network via your machine's IP).

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

Open **http://localhost:5000** in your browser.

---

## Usage

### Connect to Weaviate

1. Enter your Weaviate instance URL, e.g. `http://localhost:8086`
2. Enter your API key (leave blank if not required)
3. Click **Connect to Database**

### Collections & Collection Properties

- The landing page after connect lists all collections
- Click **+ New Collection** to create one (with optional multi-tenancy)
- **Double-click** a card to drill into the collection
- Click **Delete** on a card to delete the entire collection
- **Manage Collection Properties**:
  - View all schema properties, data types, and descriptions
  - Click **Edit** on any property to update its description
  - Click **Delete** on any property to remove that property and its data from all documents across all tenants
  - Click **+ Add Property** to define a new property (with data types like `text`, `int`, `number`, `boolean`, `date`, `text[]`, etc.)

### Tenants & Active / Inactive Status Switching

- Shown when you drill into a multi-tenant collection
- Click **+ New Tenant** to add a tenant (with optional tenant-level description)
- **Toggle Tenant Status**:
  - Switch any tenant between **Active (HOT)** and **Inactive (COLD)** with one click (**Activate** / **Deactivate** buttons)
  - Status is displayed with badges (`Active` in green, `Inactive` in red/gray)
- Click **Property Values** on any tenant card to view all properties and their values across objects in that tenant
- Click **Documents** or **double-click** a tenant card to view its documents
- Click **Delete** to remove a tenant

### Document Property Editor & Documents

- In the Tenant view (or single-tenant collection view):
- Click **Edit Properties** on any document row to open the Document Property Editor:
  - **Property Table View**: View each individual key-value pair of the document. Edit any value and click **Save**, or click **Delete** to remove that specific property from the document.
  - **+ Add Property**: Quickly set/add a new property key and value to that specific document.
  - **Raw JSON Editor**: Switch to raw JSON mode to inspect and edit the entire document properties structure at once.
- Click **+ Upload Document** and paste a JSON object of properties
- Optionally specify a UUID (auto-generated otherwise)
- Click **Delete** next to any row to remove a document
- Use the filter box to search by UUID or property text in real-time

---

## Project Structure

```
VectorManager/
├── app.py            # Flask application (routes + HTML/JS template)
├── requirements.txt  # Python dependencies
├── README.md         # This file
└── venv/             # Virtual environment (not committed)
```

---

## Dependencies (`requirements.txt`)

| Package | Purpose |
|---------|---------|
| `Flask` | Web framework |
| `weaviate-client >= 4.x` | Official Weaviate Python client (v4 API) |
| `python-dotenv` | Load environment variables from `.env` |
| `gunicorn` | Production WSGI server (optional) |

---

## Running in Production (optional)

For a production deployment, use **Gunicorn** instead of the built-in Flask server:

```bash
gunicorn -w 1 -b 0.0.0.0:5000 app:app
```

> [!WARNING]
> The app stores the Weaviate connection in a **module-level global variable**.  
> Use exactly **1 worker** (`-w 1`) with Gunicorn, otherwise each worker will have its own disconnected state.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `weaviate-manager-secret-key` | Flask session secret — change in production |
| `OPENAI_API_KEY` | *(not set)* | Forwarded to Weaviate if your collections use OpenAI vectorizers |

You can place these in a `.env` file in the project root:

```env
SECRET_KEY=my-super-secret-key
OPENAI_API_KEY=sk-...
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Connection failed` on connect | Check the URL format (`http://host:port`) and that Weaviate is reachable |
| `Not connected` on API calls | The session expired or the server restarted — reconnect from the home page |
| Tenant operations fail | Ensure the collection was created with **multi-tenancy enabled** |
| `grpc` connection errors | The app tries gRPC on port 50051; if your Weaviate instance doesn't expose gRPC, this is expected — HTTP REST calls will still work |

## Screenshots

<img width="1194" height="375" alt="image" src="https://github.com/user-attachments/assets/78902319-6f02-4700-b2ad-08979828cce5" />
<img width="1188" height="561" alt="image" src="https://github.com/user-attachments/assets/cb07f76a-67fd-428a-a014-4e51268740fe" />
<img width="1213" height="954" alt="image" src="https://github.com/user-attachments/assets/b5c98408-8b54-4b1d-9084-26ec45593639" />


