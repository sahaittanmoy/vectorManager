#!/usr/bin/env python3
"""
Weaviate Vector Database Manager
A Flask-based web application to manage remote Weaviate vector databases.
"""

import json
import os
import urllib.parse
import weaviate
import weaviate.classes as wvc
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'weaviate-manager-secret-key-2024')

# ---------------------------------------------------------------------------
# HTML / CSS / JS template helpers
# ---------------------------------------------------------------------------

_CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           background-color: #f5f7fa; color: #333; min-height: 100vh; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
        padding: 20px; border-radius: 10px; margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
    }
    header h1 { font-size: 1.5rem; }
    .logout-btn { background: rgba(255,255,255,0.2); border: none; color: white;
                  padding: 8px 16px; border-radius: 4px; cursor: pointer; transition: background 0.2s; }
    .logout-btn:hover { background: rgba(255,255,255,0.35); }
    .connection-section { background: white; padding: 25px; border-radius: 10px;
                          box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .connection-section h2 { color: #667eea; margin-bottom: 15px; font-size: 1.3rem; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
    .form-control { width: 100%; padding: 12px; border: 1px solid #ddd;
                    border-radius: 6px; font-size: 1rem; }
    .btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;
           font-size: 0.9rem; font-weight: 500; transition: all 0.2s; display: inline-flex;
           align-items: center; gap: 6px; text-decoration: none; justify-content: center; }
    .btn:hover { opacity: 0.9; transform: translateY(-1px); }
    .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
    .btn-danger  { background: #e74c3c; color: white; }
    .btn-success { background: #27ae60; color: white; }
    .btn-secondary { background: #6c757d; color: white; }
    .btn-info    { background: #17a2b8; color: white; }
    .btn-warning { background: #f59e0b; color: white; }
    .btn-warning:hover { background: #d97706; }
    .btn-outline { background: white; border: 1px solid #16a34a; color: #16a34a; }
    .btn-outline:hover { background: #16a34a; color: white; }
    .btn-outline-danger { background: white; border: 1px solid #ef4444; color: #ef4444; }
    .btn-outline-danger:hover { background: #ef4444; color: white; }
    .btn-outline-primary { background: white; border: 1px solid #6366f1; color: #6366f1; }
    .btn-outline-primary:hover { background: #6366f1; color: white; }
    .btn-sm { padding: 5px 10px; font-size: 0.8rem; }
    .collections-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
    .collection-card { background: white; border-radius: 10px; padding: 20px;
                       box-shadow: 0 2px 10px rgba(0,0,0,0.08); cursor: pointer;
                       border: 2px solid transparent; transition: all 0.2s; }
    .collection-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.12);
                              border-color: #667eea; }
    .collection-card h3 { color: #667eea; margin-bottom: 6px; font-size: 1.25rem; word-break: break-all; }
    .collection-meta { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 15px; }
    .meta-item { background: #f8f9fa; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; }
    .meta-label { color: #666; font-weight: 500; display: block; font-size: 0.78rem; text-transform: uppercase; }
    .meta-val { color: #222; font-weight: 600; font-size: 0.95rem; }
    .status-badge { display: inline-block; padding: 4px 8px; border-radius: 4px;
                    font-size: 0.75rem; font-weight: 600; }
    .status-active { background: #d4edda; color: #155724; }
    .status-inactive { background: #fee2e2; color: #991b1b; }
    .status-mt     { background: #e2e3e5; color: #383d41; }
    .status-cold   { background: #e2e8f0; color: #334155; }
    .breadcrumbs { background: white; padding: 15px 20px; border-radius: 10px;
                   margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); font-size: 0.95rem; }
    .breadcrumb { color: #667eea; text-decoration: none; cursor: pointer; font-weight: 500; }
    .breadcrumb:hover { text-decoration: underline; }
    .content-area { background: white; border-radius: 10px; padding: 25px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 20px; }
    .documents-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    .documents-table th, .documents-table td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #eee; }
    .documents-table th { background: #f8f9fa; font-weight: 600; color: #555; }
    .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                     background: rgba(0,0,0,0.5); display: none;
                     justify-content: center; align-items: center; z-index: 1000; }
    .modal { background: white; border-radius: 10px; width: 92%; max-width: 620px;
             padding: 25px; box-shadow: 0 4px 25px rgba(0,0,0,0.25); max-height: 90vh; overflow-y: auto; }
    .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .modal-title { font-size: 1.3rem; color: #667eea; }
    .close-modal { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
    .action-bar { display: flex; justify-content: space-between; align-items: center;
                  margin-bottom: 20px; gap: 15px; flex-wrap: wrap; }
    .action-bar-left { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .search-box { flex-grow: 1; max-width: 320px; }
    .tenants-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                    gap: 15px; margin-top: 15px; }
    .tenant-card { background: #f8f9fa; border-radius: 8px; padding: 16px;
                   cursor: pointer; border: 2px solid transparent; transition: all 0.2s; display: flex; flex-direction: column; justify-content: space-between; }
    .tenant-card:hover { border-color: #764ba2; background: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .tenant-name { font-weight: 600; color: #764ba2; font-size: 1.05rem; word-break: break-all; }
    .toast-container { position: fixed; top: 20px; right: 20px; z-index: 1001; }
    .toast { background: white; padding: 14px 18px; border-radius: 8px;
             margin-bottom: 10px; box-shadow: 0 4px 14px rgba(0,0,0,0.15); min-width: 300px;
             border-left: 5px solid #667eea; }
    .toast.success { border-left-color: #27ae60; }
    .toast.error   { border-left-color: #e74c3c; }
    .loading { display: none; text-align: center; padding: 40px; }
    .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #667eea;
               border-radius: 50%; width: 40px; height: 40px;
               animation: spin 1s linear infinite; margin: 0 auto; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .card-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding-top: 12px; border-top: 1px solid #eee; }
    
    .tenant-prop-card {
        background: #f8f9fa; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px;
        transition: all 0.15s;
    }
    .tenant-prop-card:hover { background: #fff; border-color: #cbd5e1; box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
    .prop-val-pill {
        background: #fff; border: 1px solid #cbd5e1; padding: 4px 10px; border-radius: 6px;
        font-size: 0.85rem; color: #1e293b; max-width: 500px; overflow: hidden;
        text-overflow: ellipsis; white-space: nowrap; display: inline-block; word-break: break-all;
    }
    .prop-val-pill:hover { border-color: #667eea; background: #fdfdfd; }
    
    .tab-btn {
        padding: 8px 18px; border: none; background: #e5e7eb; border-radius: 6px 6px 0 0;
        cursor: pointer; font-weight: 500; font-size: 0.9rem; color: #4b5563; transition: all 0.15s;
    }
    .tab-btn:hover { background: #d1d5db; }
    .tab-btn.active {
        background: white; border-top: 3px solid #667eea; color: #667eea; font-weight: 600;
        border-left: 1px solid #ddd; border-right: 1px solid #ddd;
    }
"""

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weaviate Manager</title>
    <style>{{ css }}</style>
</head>
<body>
<div class="container">
    <header>
        <h1>Weaviate Vector Manager</h1>
        {% if connected %}
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-size:0.85rem; opacity:0.9; background:rgba(0,0,0,0.15); padding:4px 10px; border-radius:4px;">{{ weaviate_url }}</span>
            <button class="logout-btn" onclick="app.disconnect()">Disconnect</button>
        </div>
        {% endif %}
    </header>

    {% if error %}
    <div style="background:#f8d7da; color:#721c24; padding:12px 18px; border-radius:8px; margin-bottom:20px; border-left:5px solid #e74c3c;">
        <strong>Error:</strong> {{ error }}
    </div>
    {% endif %}

    <!-- Connection Section -->
    {% if not connected %}
    <div class="connection-section">
        <h2>Connect to Weaviate</h2>
        <div class="form-group">
            <label for="weaviateUrl">Weaviate HTTP URL *</label>
            <input type="text" id="weaviateUrl" class="form-control"
                   placeholder="http://localhost:8080 or https://xxx.weaviate.cloud"
                   value="{{ default_url or 'http://localhost:8080' }}">
            <small style="color:#777; display:block; margin-top:4px;">For local: http://localhost:8080 or http://10.x.x.x:8086. For WCD: https://your-cluster-id.weaviate.cloud</small>
        </div>
        <div class="form-group">
            <label for="apiKey">API Key (optional)</label>
            <input type="password" id="apiKey" class="form-control" placeholder="Leave blank if authentication is disabled">
        </div>
        <button class="btn btn-primary" onclick="app.connect()">Connect to Database</button>
    </div>
    {% endif %}

    <!-- Collections List View -->
    {% if view == 'collections' %}
    <div class="action-bar">
        <h2 style="color:#333; font-size:1.4rem;">Collections ({{ collections|length }})</h2>
        <div class="action-bar-left">
            <button class="btn btn-success" onclick="app.showModal('modal-create-collection')">+ New Collection</button>
            <button class="btn btn-secondary btn-sm" onclick="app.viewCollections()">Refresh</button>
        </div>
    </div>
    <div class="collections-grid">
        {% for col in collections %}
        <div class="collection-card" ondblclick="app.viewCollection('{{ col.name }}')">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <h3>{{ col.name }}</h3>
                <span class="status-badge status-active">Active</span>
            </div>
            {% if col.description %}
            <p style="color:#666; font-size:0.9rem; margin-top:6px; line-height:1.4;">{{ col.description }}</p>
            {% else %}
            <p style="color:#aaa; font-size:0.85rem; margin-top:6px; font-style:italic;">No description</p>
            {% endif %}
            <div class="collection-meta">
                <div class="meta-item">
                    <span class="meta-label">Properties</span>
                    <span class="meta-val">{{ col.property_count }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Architecture</span>
                    <span class="meta-val" style="font-size:0.85rem; color:#764ba2;">
                        {{ 'Multi-Tenant' if col.multi_tenancy else 'Single-Tenant' }}
                    </span>
                </div>
            </div>
            <div class="card-actions">
                <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); app.viewCollection('{{ col.name }}')">
                    Drill Down
                </button>
                <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); app.deleteCollection('{{ col.name }}')">
                    Delete
                </button>
            </div>
        </div>
        {% else %}
        <div class="content-area" style="grid-column: 1 / -1; text-align:center; padding:40px;">
            <p style="color:#666; margin-bottom:15px; font-size:1.05rem;">No collections found in this Weaviate instance.</p>
            <button class="btn btn-success" onclick="app.showModal('modal-create-collection')">+ Create Your First Collection</button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Collection detail -->
    {% if view == 'collection' %}
    <nav class="breadcrumbs">
        <a class="breadcrumb" onclick="app.viewCollections()">&larr; Collections</a> &gt;
        <span style="font-weight:600; color:#333;">{{ current_collection }}</span>
    </nav>
    <div class="action-bar">
        <div class="action-bar-left">
            {% if is_multi_tenant %}
            <button class="btn btn-success" onclick="app.showModal('modal-create-tenant')">+ New Tenant</button>
            {% else %}
            <button class="btn btn-success" onclick="app.showModal('modal-upload-doc')">+ Upload Document</button>
            {% endif %}
            <button class="btn btn-danger" onclick="app.deleteCollection('{{ current_collection }}')">Delete Collection</button>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="app.viewCollections()">Back to Collections</button>
    </div>

    <!-- Metadata & Schema Properties Card -->
    <div class="content-area">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <div>
                <h2 style="color:#667eea;">{{ current_collection }}</h2>
                {% if description %}
                <p style="color:#666; margin-top:4px;">{{ description }}</p>
                {% endif %}
            </div>
            <div>
                <span class="status-badge status-active">Active</span>
                <span class="status-badge status-mt" style="margin-left:6px;">{{ 'Multi-Tenant' if is_multi_tenant else 'Standard (Single-Tenant)' }}</span>
            </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px; margin-bottom:10px;">
            <h3 style="font-size:1.15rem; color:#444; margin:0;">Schema Properties ({{ properties|length }})</h3>
            <button class="btn btn-success btn-sm" onclick="app.showAddPropertyModal('{{ current_collection }}')">+ Add Property</button>
        </div>
        {% if properties %}
        <table class="documents-table" style="margin-top:0;">
            <thead>
                <tr>
                    <th style="width:25%;">Property Name</th>
                    <th style="width:18%;">Data Type</th>
                    <th>Description</th>
                    <th style="width:160px; text-align:right;">Actions</th>
                </tr>
            </thead>
            <tbody>
            {% for prop in properties %}
            <tr id="col-prop-row-{{ prop.name }}">
                <td style="font-weight:600; color:#333;">{{ prop.name }}</td>
                <td><code style="background:#eef2ff; color:#4f46e5; padding:2px 8px; border-radius:4px; font-size:0.85rem;">{{ prop.data_type }}</code></td>
                <td style="color:#666;" id="col-prop-desc-{{ prop.name }}">{{ prop.description or '-' }}</td>
                <td style="text-align:right;">
                    <div style="display:inline-flex; gap:6px;">
                        <button class="btn btn-secondary btn-sm" onclick='app.showEditPropertyModal("{{ current_collection }}", "{{ prop.name }}", {{ (prop.description or "")|tojson }})'>Edit</button>
                        <button class="btn btn-danger btn-sm" onclick='app.deleteCollectionProperty("{{ current_collection }}", "{{ prop.name }}")'>Delete</button>
                    </div>
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p style="color:#888; font-size:0.9rem;">No custom properties defined yet. Click <strong>+ Add Property</strong> above to add one.</p>
        {% endif %}
    </div>

    <!-- Multi-Tenant View: Show Tenants -->
    {% if is_multi_tenant %}
    <div class="content-area">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <div>
                <h3 style="font-size:1.2rem; color:#444;">Tenants ({{ tenants|length }})</h3>
                <p style="color:#666; font-size:0.85rem; margin-top:2px;">Switch active/inactive status, view tenant descriptions, or inspect document properties.</p>
            </div>
            <button class="btn btn-success btn-sm" onclick="app.showModal('modal-create-tenant')">+ Add Tenant</button>
        </div>
        {% if tenants %}
        <div class="tenants-grid">
            {% for t in tenants %}
            {% set is_t_active = (t.activity_status|upper in ['ACTIVE', 'HOT', 'TRUE', '1']) %}
            <div class="tenant-card" ondblclick="app.viewTenant('{{ current_collection }}', '{{ t.name }}')">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
                        <div class="tenant-name">{{ t.name }}</div>
                        <span class="status-badge {{ 'status-active' if is_t_active else 'status-inactive' }}" style="font-size:0.72rem;">
                            {{ 'Active' if is_t_active else 'Inactive (' ~ (t.activity_status or 'Cold') ~ ')' }}
                        </span>
                    </div>
                    {% if t.description %}
                    <p style="color:#374151; font-size:0.84rem; margin-top:8px; line-height:1.4; max-height:48px; overflow:hidden; text-overflow:ellipsis;" title="{{ t.description }}">
                        <strong>Description:</strong> {{ t.description }}
                    </p>
                    {% else %}
                    <p style="font-size:0.8rem; color:#888; margin-top:8px;">Double-click to view documents</p>
                    {% endif %}
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:14px; padding-top:10px; border-top:1px solid #eee; gap:6px; flex-wrap:wrap; align-items:center;">
                    <div style="display:flex; gap:5px; flex-wrap:wrap;">
                        <button class="btn btn-primary btn-sm" title="Inspect tenant description and property values" onclick="event.stopPropagation(); app.showTenantPropertyValues('{{ current_collection }}', '{{ t.name }}')">
                            Properties
                        </button>
                        <button class="btn btn-info btn-sm" onclick="event.stopPropagation(); app.viewTenant('{{ current_collection }}', '{{ t.name }}')">
                            Documents
                        </button>
                    </div>
                    <div style="display:flex; gap:5px; flex-wrap:wrap;">
                        {% if is_t_active %}
                        <button class="btn btn-warning btn-sm" title="Switch tenant to Inactive" onclick="event.stopPropagation(); app.setTenantStatus('{{ current_collection }}', '{{ t.name }}', 'INACTIVE')">
                            Deactivate
                        </button>
                        {% else %}
                        <button class="btn btn-success btn-sm" title="Switch tenant to Active" onclick="event.stopPropagation(); app.setTenantStatus('{{ current_collection }}', '{{ t.name }}', 'ACTIVE')">
                            Activate
                        </button>
                        {% endif %}
                        <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); app.deleteTenant('{{ current_collection }}', '{{ t.name }}')">
                            Delete
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p style="color:#666;">No tenants exist yet. Click <strong>+ Add Tenant</strong> above to create one.</p>
        {% endif %}
    </div>
    {% endif %}

    <!-- Single-Tenant / Standard View: Show Documents Directly -->
    {% if not is_multi_tenant %}
    <div class="content-area">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <h3 style="font-size:1.2rem; color:#444; margin:0;">Documents ({{ documents|length }})</h3>
                <input type="text" id="docSearchBox" class="form-control doc-search-input" style="width:260px; padding:6px 10px; font-size:0.85rem;" placeholder="Filter by UUID or property (e.g. _)..." oninput="app.filterDocuments(this.value)">
                <span id="docFilterCount" class="status-badge status-mt" style="display:none; font-size:0.8rem;"></span>
            </div>
            <button class="btn btn-success btn-sm" onclick="app.showModal('modal-upload-doc')">+ Upload Document</button>
        </div>
        <table class="documents-table" id="docsTable">
            <thead>
                <tr><th>UUID</th><th>Properties Preview</th><th style="width:210px;">Actions</th></tr>
            </thead>
            <tbody>
            {% for doc in documents %}
            <tr data-uuid="{{ doc.uuid }}" data-search="{{ doc.uuid }} {{ doc.properties_json }}">
                <td><code style="background:#f8f9fa; padding:3px 6px; border-radius:3px; font-size:0.8rem;">{{ doc.uuid }}</code></td>
                <td style="max-width:520px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#444; font-size:0.88rem;" class="doc-preview-cell">
                    {{ doc.properties_preview }}
                </td>
                <td style="display:flex; gap:6px;">
                    <button class="btn btn-primary btn-sm" onclick='app.openDocumentPropertyEditor("{{ current_collection }}", null, "{{ doc.uuid }}", {{ doc.properties|tojson }})'>Edit Properties</button>
                    <button class="btn btn-danger btn-sm" onclick="app.deleteDocument('{{ current_collection }}', null, '{{ doc.uuid }}')">Delete</button>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align:center; padding:25px; color:#888;">
                No documents in this collection. Click "+ Upload Document" to add one.
            </td></tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}
    {% endif %}

    <!-- Tenant detail (tenant description + documents list + property values summary) -->
    {% if view == 'tenant' %}
    <nav class="breadcrumbs">
        <a class="breadcrumb" onclick="app.viewCollections()">Collections</a> &gt;
        <a class="breadcrumb" onclick="app.viewCollection('{{ current_collection }}')">{{ current_collection }}</a> &gt;
        <span style="font-weight:600; color:#333;">Tenant: {{ current_tenant }}</span>
        <span class="status-badge {{ 'status-active' if is_tenant_active else 'status-inactive' }}" style="margin-left:8px; font-size:0.75rem;">
            {{ 'Active' if is_tenant_active else 'Inactive (' ~ (tenant_status or 'Cold') ~ ')' }}
        </span>
    </nav>
    <div class="action-bar">
        <div class="action-bar-left">
            <button class="btn btn-primary" onclick="app.showTenantPropertyValues('{{ current_collection }}', '{{ current_tenant }}')">
                View Property Values
            </button>
            <button class="btn btn-success" onclick="app.showModal('modal-upload-doc')">+ Upload Document</button>
            {% if is_tenant_active %}
            <button class="btn btn-warning" onclick="app.setTenantStatus('{{ current_collection }}', '{{ current_tenant }}', 'INACTIVE')">
                Deactivate Tenant
            </button>
            {% else %}
            <button class="btn btn-success" onclick="app.setTenantStatus('{{ current_collection }}', '{{ current_tenant }}', 'ACTIVE')">
                Activate Tenant
            </button>
            {% endif %}
            <button class="btn btn-danger" onclick="app.deleteTenant('{{ current_collection }}', '{{ current_tenant }}')">Delete Tenant</button>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="app.viewCollection('{{ current_collection }}')">Back to {{ current_collection }}</button>
    </div>

    <!-- Tenant's Own Description Card -->
    <div class="content-area" style="background:#f0fdf4; border: 1px solid #bbf7d0; border-left: 5px solid #16a34a; margin-bottom: 20px; padding:18px 22px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
            <div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <span style="font-size:1.15rem;">📌</span>
                    <h3 style="color:#166534; font-size:1.1rem; margin:0;">Tenant Description</h3>
                </div>
                <p id="tenantPageDescText" style="color:#15803d; font-size:0.95rem; margin:0; line-height:1.5; font-weight:500;">
                    {{ tenant_description or 'No specific tenant-level description specified.' }}
                </p>
            </div>
            <button class="btn btn-outline btn-sm" onclick="app.showEditTenantDescModal('{{ current_collection }}', '{{ current_tenant }}')">Edit Description</button>
        </div>
    </div>

    <!-- Tenant Property Values Summary Section -->
    <div class="content-area" style="background:#fff; border-left: 4px solid #667eea; margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="app.togglePropSummary()">
            <div>
                <h3 style="color:#667eea; font-size:1.15rem; display:flex; align-items:center; gap:8px;">
                    <span>Document Elements Inside Tenant</span>
                    <span class="status-badge status-mt" style="font-size:0.75rem;">{{ tenant_properties|length }} properties</span>
                </h3>
                <p style="color:#666; font-size:0.85rem; margin-top:2px;">Summary of property values across document elements (columns / chunks) in this tenant.</p>
            </div>
            <button class="btn btn-secondary btn-sm" id="propSummaryToggleBtn">Collapse</button>
        </div>
        <div id="tenantPropSummaryContent" style="margin-top:15px; display:flex; flex-direction:column; gap:12px;">
            {% for prop in tenant_properties %}
            <div class="tenant-prop-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; flex-wrap:wrap; gap:6px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <strong style="color:#333; font-size:0.95rem;">{{ prop.name }}</strong>
                        <code style="background:#eef2ff; color:#4f46e5; padding:1px 6px; border-radius:3px; font-size:0.78rem;">{{ prop.data_type }}</code>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:0.8rem; color:#666;">
                            {{ prop.val_list|length }} unique value{{ 's' if prop.val_list|length != 1 else '' }} ({{ prop.total_count }} total entries)
                        </span>
                        <button class="btn btn-secondary btn-sm" style="padding:2px 7px; font-size:0.75rem;" onclick='app.showEditPropertyModal("{{ current_collection }}", "{{ prop.name }}", "")'>Edit Schema</button>
                        <button class="btn btn-outline-danger btn-sm" style="padding:2px 7px; font-size:0.75rem;" onclick='app.deleteTenantProperty("{{ current_collection }}", "{{ current_tenant }}", "{{ prop.name }}")'>Delete from Tenant</button>
                    </div>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; max-height:160px; overflow-y:auto;">
                    {% for val in prop.val_list %}
                    <span class="prop-val-pill" title="{{ val }}">
                        {{ val if val is string else val|tojson }}
                    </span>
                    {% else %}
                    <span style="color:#999; font-size:0.85rem; font-style:italic;">No values recorded for this property</span>
                    {% endfor %}
                </div>
            </div>
            {% else %}
            <p style="color:#888; font-size:0.9rem;">No properties found for this tenant.</p>
            {% endfor %}
        </div>
    </div>

    <!-- Documents in Tenant Table -->
    <div class="content-area">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <h2 style="color:#333; font-size:1.25rem; margin:0;">Documents ({{ documents|length }})</h2>
                <input type="text" id="docSearchBox" class="form-control doc-search-input" style="width:260px; padding:6px 10px; font-size:0.85rem;" placeholder="Filter by UUID or property (e.g. _)..." oninput="app.filterDocuments(this.value)">
                <span id="docFilterCount" class="status-badge status-mt" style="display:none; font-size:0.8rem;"></span>
            </div>
            <button class="btn btn-success btn-sm" onclick="app.showModal('modal-upload-doc')">+ Upload Document</button>
        </div>
        <table class="documents-table" id="docsTable">
            <thead>
                <tr><th>UUID</th><th>Properties Preview</th><th style="width:210px;">Actions</th></tr>
            </thead>
            <tbody>
            {% for doc in documents %}
            <tr data-uuid="{{ doc.uuid }}" data-search="{{ doc.uuid }} {{ doc.properties_json }}">
                <td><code style="background:#f8f9fa; padding:3px 6px; border-radius:3px; font-size:0.8rem;">{{ doc.uuid }}</code></td>
                <td style="max-width:520px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#444; font-size:0.88rem;" class="doc-preview-cell">
                    {{ doc.properties_preview }}
                </td>
                <td style="display:flex; gap:6px;">
                    <button class="btn btn-primary btn-sm" onclick='app.openDocumentPropertyEditor("{{ current_collection }}", "{{ current_tenant }}", "{{ doc.uuid }}", {{ doc.properties|tojson }})'>Edit Properties</button>
                    <button class="btn btn-danger btn-sm" onclick="app.deleteDocument('{{ current_collection }}', '{{ current_tenant }}', '{{ doc.uuid }}')">Delete</button>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align:center; padding:25px; color:#888;">
                No documents found for this tenant. Click "+ Upload Document" to get started.
            </td></tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    <!-- Loading spinner -->
    <div id="loading" class="loading">
        <div class="spinner"></div>
        <p style="margin-top:15px; color:#666;">Loading...</p>
    </div>
</div>

<!-- Modals -->

<!-- Tenant Property Values Modal -->
<div id="modal-tenant-properties" class="modal-overlay">
    <div class="modal" style="max-width: 680px;">
        <div class="modal-header">
            <div>
                <h3 class="modal-title" id="tenantPropModalTitle">Tenant Property Values</h3>
                <p id="tenantPropModalSubtitle" style="color: #666; font-size: 0.85rem; margin-top: 3px;"></p>
            </div>
            <button class="close-modal" onclick="app.closeModal('modal-tenant-properties')">&times;</button>
        </div>

        <!-- Dedicated Tenant Description Banner -->
        <div id="tenantDescSection" style="background:#f0fdf4; border:1px solid #bbf7d0; border-left:4px solid #16a34a; border-radius:6px; padding:12px 16px; margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="font-size:1.05rem;">📌</span>
                    <strong style="color:#166534; font-size:0.95rem;">Tenant Description</strong>
                </div>
                <button class="btn btn-outline btn-sm" style="font-size:0.75rem; padding:2px 7px;" onclick="app.editCurrentTenantDesc()">Edit</button>
            </div>
            <div id="tenantDescriptionText" style="color:#15803d; font-size:0.92rem; line-height:1.45; font-weight:500;">
                (Loading tenant description...)
            </div>
        </div>

        <div style="margin-bottom: 8px; display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#444; font-size:0.95rem;">Document Elements Inside Tenant</strong>
            <span style="font-size:0.78rem; color:#666;">Properties across documents</span>
        </div>

        <div style="margin-bottom: 15px;">
            <input type="text" id="tenantPropSearch" class="form-control" placeholder="Search property name..." oninput="app.filterTenantProperties(this.value)">
        </div>
        <div id="tenantPropertiesContainer" style="max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;">
            <p style="color:#888; text-align:center;">Loading property values...</p>
        </div>
        <div style="display:flex; justify-content:flex-end; margin-top: 20px;">
            <button class="btn btn-secondary" onclick="app.closeModal('modal-tenant-properties')">Close</button>
        </div>
    </div>
</div>

<!-- Edit Tenant Description Modal -->
<div id="modal-edit-tenant-desc" class="modal-overlay">
    <div class="modal" style="max-width: 520px;">
        <div class="modal-header">
            <h3 class="modal-title">Edit Tenant Description</h3>
            <button class="close-modal" onclick="app.closeModal('modal-edit-tenant-desc')">&times;</button>
        </div>
        <form id="editTenantDescForm">
            <input type="hidden" id="editTenantDescCol">
            <input type="hidden" id="editTenantDescTenant">
            <div class="form-group">
                <label>Tenant Description *</label>
                <textarea id="editTenantDescText" class="form-control" rows="5"
                          placeholder="Enter a description for this tenant..." required></textarea>
            </div>
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:15px;">
                <button type="button" class="btn btn-secondary" onclick="app.closeModal('modal-edit-tenant-desc')">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Description</button>
            </div>
        </form>
    </div>
</div>

<!-- Document Property Editor Modal (Edit/Delete each property of document) -->
<div id="modal-edit-doc-properties" class="modal-overlay">
    <div class="modal" style="max-width: 780px;">
        <div class="modal-header">
            <div>
                <h3 class="modal-title">Edit Document Properties</h3>
                <p id="docEditorMeta" style="font-size:0.83rem; color:#666; margin-top:3px; word-break:break-all;"></p>
            </div>
            <button class="close-modal" onclick="app.closeModal('modal-edit-doc-properties')">&times;</button>
        </div>

        <!-- Mode Toggle Tabs -->
        <div style="display:flex; border-bottom:1px solid #ddd; margin-bottom:15px; gap:4px;">
            <button type="button" class="tab-btn active" id="tabBtnDocProps" onclick="app.switchDocEditorTab('table')">Property Table</button>
            <button type="button" class="tab-btn" id="tabBtnDocJson" onclick="app.switchDocEditorTab('json')">Raw JSON</button>
        </div>

        <!-- Tab 1: Table of individual properties -->
        <div id="docEditorTablePane">
            <div style="max-height: 380px; overflow-y: auto; margin-bottom: 15px;">
                <table class="documents-table" style="margin-top:0;">
                    <thead>
                        <tr>
                            <th style="width:28%;">Property Name</th>
                            <th>Value</th>
                            <th style="width:145px; text-align:right;">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="docPropsTableBody">
                    </tbody>
                </table>
            </div>

            <!-- Add new property to document -->
            <div style="background:#f8f9fa; border:1px solid #e5e7eb; border-radius:8px; padding:12px 14px; margin-top:10px;">
                <strong style="font-size:0.88rem; color:#444; display:block; margin-bottom:8px;">+ Add / Set Property on this Document</strong>
                <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                    <input type="text" id="newDocPropKey" class="form-control" style="width:180px; padding:7px 10px; font-size:0.85rem;" placeholder="Property name...">
                    <input type="text" id="newDocPropVal" class="form-control" style="flex-grow:1; min-width:180px; padding:7px 10px; font-size:0.85rem;" placeholder="Value (string, number, or JSON)...">
                    <button type="button" class="btn btn-success btn-sm" onclick="app.addSingleDocProperty()">Add Property</button>
                </div>
            </div>
        </div>

        <!-- Tab 2: Raw JSON editor -->
        <div id="docEditorJsonPane" style="display:none;">
            <div class="form-group">
                <textarea id="docEditorJsonText" class="form-control" rows="14" style="font-family: monospace; font-size: 0.88rem;"></textarea>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                <button type="button" class="btn btn-secondary btn-sm" onclick="app.formatDocEditorJson()">Format JSON</button>
                <button type="button" class="btn btn-primary btn-sm" onclick="app.saveDocFullJson()">Save All Properties</button>
            </div>
        </div>

        <div style="display:flex; justify-content:flex-end; margin-top: 20px;">
            <button class="btn btn-secondary" onclick="app.closeModal('modal-edit-doc-properties')">Close</button>
        </div>
    </div>
</div>

<!-- Edit Collection Property Modal -->
<div id="modal-edit-collection-prop" class="modal-overlay">
    <div class="modal" style="max-width: 520px;">
        <div class="modal-header">
            <h3 class="modal-title">Edit Collection Property</h3>
            <button class="close-modal" onclick="app.closeModal('modal-edit-collection-prop')">&times;</button>
        </div>
        <form id="editCollectionPropForm">
            <input type="hidden" id="editPropColName">
            <div class="form-group">
                <label>Property Name</label>
                <input type="text" id="editPropName" class="form-control" readonly style="background:#f3f4f6; color:#555;">
            </div>
            <div class="form-group">
                <label>Description</label>
                <textarea id="editPropDescription" class="form-control" rows="4" placeholder="Description of this property..."></textarea>
            </div>
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn btn-secondary" onclick="app.closeModal('modal-edit-collection-prop')">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Property</button>
            </div>
        </form>
    </div>
</div>

<!-- Add Collection Property Modal -->
<div id="modal-add-collection-prop" class="modal-overlay">
    <div class="modal" style="max-width: 520px;">
        <div class="modal-header">
            <h3 class="modal-title">Add Property to Collection</h3>
            <button class="close-modal" onclick="app.closeModal('modal-add-collection-prop')">&times;</button>
        </div>
        <form id="addCollectionPropForm">
            <input type="hidden" id="addPropColName">
            <div class="form-group">
                <label>Property Name *</label>
                <input type="text" id="addPropName" class="form-control" placeholder="e.g., author, category, price" required>
            </div>
            <div class="form-group">
                <label>Data Type *</label>
                <select id="addPropDataType" class="form-control">
                    <option value="text">text (string / text)</option>
                    <option value="int">int (integer)</option>
                    <option value="number">number (float / decimal)</option>
                    <option value="boolean">boolean (true / false)</option>
                    <option value="date">date (RFC3339 date-time)</option>
                    <option value="text[]">text[] (array of strings)</option>
                    <option value="int[]">int[] (array of integers)</option>
                    <option value="number[]">number[] (array of numbers)</option>
                    <option value="boolean[]">boolean[] (array of booleans)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Description <span style="color:#999;font-weight:400;">(optional)</span></label>
                <textarea id="addPropDescription" class="form-control" rows="3" placeholder="Description for this property..."></textarea>
            </div>
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn btn-secondary" onclick="app.closeModal('modal-add-collection-prop')">Cancel</button>
                <button type="submit" class="btn btn-primary">Add Property</button>
            </div>
        </form>
    </div>
</div>

<!-- Create Collection Modal -->
<div id="modal-create-collection" class="modal-overlay">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Create New Collection</h3>
            <button class="close-modal" onclick="app.closeModal('modal-create-collection')">&times;</button>
        </div>
        <form id="createCollectionForm">
            <div class="form-group">
                <label>Class Name *</label>
                <input type="text" id="newClassName" class="form-control"
                       placeholder="e.g., Article, Document, Product" required>
            </div>
            <div class="form-group">
                <label>Description <span style="color:#999;font-weight:400;">(optional)</span></label>
                <input type="text" id="newClassDescription" class="form-control" placeholder="Description of the collection">
            </div>
            <div class="form-group">
                <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                    <input type="checkbox" id="enableMultiTenancy">
                    <span>Enable Multi-Tenancy (support multiple isolated tenants)</span>
                </label>
            </div>
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn btn-secondary" onclick="app.closeModal('modal-create-collection')">Cancel</button>
                <button type="submit" class="btn btn-primary">Create Collection</button>
            </div>
        </form>
    </div>
</div>

<!-- Create Tenant Modal -->
<div id="modal-create-tenant" class="modal-overlay">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Create New Tenant</h3>
            <button class="close-modal" onclick="app.closeModal('modal-create-tenant')">&times;</button>
        </div>
        <form id="createTenantForm">
            <input type="hidden" id="tenantCollectionName">
            <div class="form-group">
                <label>Tenant Name *</label>
                <input type="text" id="newTenantName" class="form-control"
                       placeholder="e.g., tenant-1, tenant-alpha" required>
            </div>
            <div class="form-group">
                <label>Tenant Description <span style="color:#999;font-weight:400;">(optional)</span></label>
                <input type="text" id="newTenantDescription" class="form-control"
                       placeholder="e.g. Master contracts view dataset">
            </div>
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn btn-secondary" onclick="app.closeModal('modal-create-tenant')">Cancel</button>
                <button type="submit" class="btn btn-primary">Create Tenant</button>
            </div>
        </form>
    </div>
</div>

<!-- Upload Document Modal -->
<div id="modal-upload-doc" class="modal-overlay">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Upload Document</h3>
            <button class="close-modal" onclick="app.closeModal('modal-upload-doc')">&times;</button>
        </div>
        <form id="uploadDocForm">
            <input type="hidden" id="docCollectionName">
            <input type="hidden" id="docTenantName">
            <div id="uploadTargetBadge" style="margin-bottom:12px; font-size:0.85rem; color:#667eea; font-weight:600;"></div>
            <div class="form-group">
                <label>Document JSON Properties *</label>
                <textarea id="documentJson" class="form-control" rows="8"
                          placeholder='{"title": "My Article", "content": "Sample text here"}'
                          required></textarea>
                <small style="color:#777; display:block; margin-top:4px;">Must be a valid JSON object mapping property names to values.</small>
            </div>
            <div class="form-group">
                <label>Custom UUID <span style="color:#999;font-weight:400;">(optional, auto-generated if left blank)</span></label>
                <input type="text" id="documentUuid" class="form-control"
                       placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000">
            </div>
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn btn-secondary" onclick="app.closeModal('modal-upload-doc')">Cancel</button>
                <button type="submit" class="btn btn-primary">Upload Document</button>
            </div>
        </form>
    </div>
</div>

<div id="toastContainer" class="toast-container"></div>

<script>
const app = {
    _collection: '{{ current_collection or "" }}',
    _tenant: '{{ current_tenant or "" }}',
    _currentModalCol: '',
    _currentModalTenant: '',
    _currentModalDesc: '',

    // Document Property Editor State
    _docEditorCol: '',
    _docEditorTenant: '',
    _docEditorUuid: '',
    _docEditorProps: {},

    async connect() {
        const url    = document.getElementById('weaviateUrl').value.trim();
        const apiKey = document.getElementById('apiKey').value.trim();
        if (!url) { app.showToast('Please enter a Weaviate URL', 'error'); return; }
        const btn = event.target;
        btn.disabled = true; btn.textContent = 'Connecting...'; btn.style.opacity = '0.7';
        try {
            const res = await fetch('/api/connect', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url, apiKey})
            });
            const body = await res.json();
            if (res.ok) {
                app.showToast('Connected successfully!', 'success');
                setTimeout(() => { window.location.href = '/collections'; }, 600);
            } else {
                app.showToast(body.error || 'Failed to connect', 'error');
                btn.disabled = false; btn.textContent = 'Connect to Database'; btn.style.opacity = '1';
            }
        } catch (err) {
            app.showToast('Connection failed: ' + err.message, 'error');
            btn.disabled = false; btn.textContent = 'Connect to Database'; btn.style.opacity = '1';
        }
    },

    async disconnect() {
        await fetch('/api/disconnect', {method: 'POST'});
        window.location.href = '/';
    },

    viewCollections() { window.location.href = '/collections'; },
    viewCollection(name) { window.location.href = '/collection/' + encodeURIComponent(name); },
    viewTenant(col, tenant) { window.location.href = '/tenant/' + encodeURIComponent(col) + '/' + encodeURIComponent(tenant); },

    // -----------------------------------------------------------------------
    // Tenant Status (Active <-> Inactive)
    // -----------------------------------------------------------------------
    async setTenantStatus(col, tenant, newStatus) {
        const actionLabel = newStatus.toUpperCase() === 'ACTIVE' ? 'activate' : 'deactivate';
        if (!confirm(`Are you sure you want to ${actionLabel} tenant "${tenant}"?`)) return;

        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(col) + '/tenant/' + encodeURIComponent(tenant) + '/status', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status: newStatus})
            });
            const body = await res.json();
            if (res.ok) {
                app.showToast(`Tenant "${tenant}" is now ${body.status}`, 'success');
                setTimeout(() => window.location.reload(), 600);
            } else {
                app.showToast(body.error || 'Failed to update tenant status', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    // -----------------------------------------------------------------------
    // Collection Property Management (Edit, Delete, Add)
    // -----------------------------------------------------------------------
    showEditPropertyModal(col, propName, currentDesc) {
        document.getElementById('editPropColName').value = col;
        document.getElementById('editPropName').value    = propName;
        document.getElementById('editPropDescription').value = currentDesc || '';
        app.showModal('modal-edit-collection-prop');
    },

    async saveCollectionPropertyDescription() {
        const col  = document.getElementById('editPropColName').value;
        const name = document.getElementById('editPropName').value;
        const desc = document.getElementById('editPropDescription').value.trim();

        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(col) + '/property/' + encodeURIComponent(name), {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({description: desc})
            });
            const body = await res.json();
            if (res.ok) {
                app.closeModal('modal-edit-collection-prop');
                app.showToast(`Property "${name}" updated`, 'success');
                const descCell = document.getElementById('col-prop-desc-' + name);
                if (descCell) descCell.textContent = desc || '-';
            } else {
                app.showToast(body.error || 'Failed to update property', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    showAddPropertyModal(col) {
        document.getElementById('addPropColName').value = col;
        document.getElementById('addPropName').value = '';
        document.getElementById('addPropDataType').value = 'text';
        document.getElementById('addPropDescription').value = '';
        app.showModal('modal-add-collection-prop');
    },

    async addCollectionProperty() {
        const col  = document.getElementById('addPropColName').value;
        const name = document.getElementById('addPropName').value.trim();
        const dt   = document.getElementById('addPropDataType').value;
        const desc = document.getElementById('addPropDescription').value.trim();

        if (!name) { app.showToast('Property name is required', 'error'); return; }

        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(col) + '/property', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, dataType: dt, description: desc})
            });
            const body = await res.json();
            if (res.ok) {
                app.closeModal('modal-add-collection-prop');
                app.showToast(`Property "${name}" added to collection!`, 'success');
                setTimeout(() => window.location.reload(), 600);
            } else {
                app.showToast(body.error || 'Failed to add property', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async deleteCollectionProperty(col, propName) {
        if (!confirm(`Are you sure you want to delete property "${propName}" from collection "${col}"?\n\nThis will remove "${propName}" and its data from all documents across all tenants in this collection.`)) return;

        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(col) + '/property/' + encodeURIComponent(propName), {
                method: 'DELETE'
            });
            const body = await res.json();
            if (res.ok) {
                app.showToast(body.message || `Property "${propName}" removed from documents`, 'success');
                setTimeout(() => window.location.reload(), 700);
            } else {
                app.showToast(body.error || 'Failed to delete property', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async deleteTenantProperty(col, tenant, propName) {
        if (!confirm(`Are you sure you want to remove property "${propName}" from all documents in tenant "${tenant}"?`)) return;

        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(col) + '/tenant/' + encodeURIComponent(tenant) + '/property/' + encodeURIComponent(propName), {
                method: 'DELETE'
            });
            const body = await res.json();
            if (res.ok) {
                app.showToast(body.message || `Property "${propName}" removed from tenant documents`, 'success');
                setTimeout(() => window.location.reload(), 700);
            } else {
                app.showToast(body.error || 'Failed to delete property from tenant', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    // -----------------------------------------------------------------------
    // Document Property Editor (Edit / Delete each property of document)
    // -----------------------------------------------------------------------
    openDocumentPropertyEditor(col, tenant, uuid, props) {
        app._docEditorCol = col;
        app._docEditorTenant = tenant || '';
        app._docEditorUuid = uuid;

        // Safely unwrap if passed as string (or multiple-encoded JSON string)
        while (typeof props === 'string') {
            try {
                const parsed = JSON.parse(props);
                if (typeof parsed === 'string' || (typeof parsed === 'object' && parsed !== null)) {
                    props = parsed;
                    if (typeof parsed === 'object') break;
                } else {
                    break;
                }
            } catch(e) {
                break;
            }
        }

        if (!props || typeof props !== 'object' || Array.isArray(props)) {
            props = {};
        }

        app._docEditorProps = JSON.parse(JSON.stringify(props));

        let metaText = 'UUID: ' + uuid;
        if (tenant) metaText += ' | Tenant: ' + tenant;
        metaText += ' | Collection: ' + col;
        document.getElementById('docEditorMeta').textContent = metaText;

        document.getElementById('newDocPropKey').value = '';
        document.getElementById('newDocPropVal').value = '';

        app.switchDocEditorTab('table');
        app.renderDocPropsTable();
        app.showModal('modal-edit-doc-properties');
    },

    switchDocEditorTab(tab) {
        const tablePane = document.getElementById('docEditorTablePane');
        const jsonPane  = document.getElementById('docEditorJsonPane');
        const btnTable  = document.getElementById('tabBtnDocProps');
        const btnJson   = document.getElementById('tabBtnDocJson');

        if (tab === 'table') {
            tablePane.style.display = 'block';
            jsonPane.style.display  = 'none';
            btnTable.classList.add('active');
            btnJson.classList.remove('active');
            app.renderDocPropsTable();
        } else {
            tablePane.style.display = 'none';
            jsonPane.style.display  = 'block';
            btnTable.classList.remove('active');
            btnJson.classList.add('active');
            document.getElementById('docEditorJsonText').value = JSON.stringify(app._docEditorProps, null, 2);
        }
    },

    renderDocPropsTable() {
        const tbody = document.getElementById('docPropsTableBody');
        tbody.innerHTML = '';
        const keys = Object.keys(app._docEditorProps || {}).sort();

        if (keys.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:18px; color:#888;">No properties on this document. Add one below!</td></tr>';
            return;
        }

        keys.forEach(k => {
            const v = app._docEditorProps[k];
            const isObj = (typeof v === 'object' && v !== null);
            const valStr = isObj ? JSON.stringify(v, null, 2) : (v === null ? '' : String(v));

            const tr = document.createElement('tr');
            tr.id = 'docPropRow_' + encodeURIComponent(k);

            const tdName = document.createElement('td');
            tdName.style.fontWeight = '600';
            tdName.style.color = '#333';
            tdName.style.verticalAlign = 'top';
            tdName.textContent = k;

            const tdVal = document.createElement('td');
            tdVal.style.verticalAlign = 'top';
            if (isObj || valStr.length > 50 || valStr.includes('\\n')) {
                const textarea = document.createElement('textarea');
                textarea.className = 'form-control';
                textarea.rows = Math.min(6, Math.max(2, valStr.split('\\n').length));
                textarea.style.fontFamily = 'monospace';
                textarea.style.fontSize = '0.85rem';
                textarea.id = 'docPropInput_' + encodeURIComponent(k);
                textarea.value = valStr;
                tdVal.appendChild(textarea);
            } else {
                const input = document.createElement('input');
                input.className = 'form-control';
                input.style.padding = '6px 10px';
                input.style.fontSize = '0.9rem';
                input.id = 'docPropInput_' + encodeURIComponent(k);
                input.value = valStr;
                tdVal.appendChild(input);
            }

            const tdActions = document.createElement('td');
            tdActions.style.textAlign = 'right';
            tdActions.style.verticalAlign = 'top';

            const btnSave = document.createElement('button');
            btnSave.className = 'btn btn-primary btn-sm';
            btnSave.style.marginRight = '5px';
            btnSave.textContent = 'Save';
            btnSave.onclick = () => app.saveSingleDocProperty(k);

            const btnDel = document.createElement('button');
            btnDel.className = 'btn btn-outline-danger btn-sm';
            btnDel.textContent = 'Delete';
            btnDel.onclick = () => app.deleteSingleDocProperty(k);

            tdActions.appendChild(btnSave);
            tdActions.appendChild(btnDel);

            tr.appendChild(tdName);
            tr.appendChild(tdVal);
            tr.appendChild(tdActions);
            tbody.appendChild(tr);
        });
    },

    _parseInputValue(raw) {
        const trimmed = raw.trim();
        if (trimmed === 'true') return true;
        if (trimmed === 'false') return false;
        if (trimmed === 'null') return null;
        if (/^-?\\d+$/.test(trimmed)) return parseInt(trimmed, 10);
        if (/^-?\\d+\\.\\d+$/.test(trimmed)) return parseFloat(trimmed);
        if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
            try { return JSON.parse(trimmed); } catch(e) {}
        }
        return raw;
    },

    async saveSingleDocProperty(propName) {
        const input = document.getElementById('docPropInput_' + encodeURIComponent(propName));
        if (!input) return;
        const parsedVal = app._parseInputValue(input.value);

        const col    = app._docEditorCol;
        const tenant = app._docEditorTenant;
        const uuid   = app._docEditorUuid;

        try {
            const res = await fetch('/api/document/' + encodeURIComponent(col) + '/' + encodeURIComponent(uuid) + '/property', {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    propertyName: propName,
                    propertyValue: parsedVal,
                    tenant: tenant || null
                })
            });
            const body = await res.json();
            if (res.ok) {
                app._docEditorProps[propName] = parsedVal;
                app.showToast(`Property "${propName}" saved!`, 'success');
                app.updateDocumentRowPreview(uuid, app._docEditorProps);
            } else {
                app.showToast(body.error || 'Failed to save property', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async deleteSingleDocProperty(propName) {
        if (!confirm(`Are you sure you want to delete property "${propName}" from this document?`)) return;

        const col    = app._docEditorCol;
        const tenant = app._docEditorTenant;
        const uuid   = app._docEditorUuid;

        try {
            const url = '/api/document/' + encodeURIComponent(col) + '/' + encodeURIComponent(uuid) + '/property/' + encodeURIComponent(propName)
                      + (tenant ? '?tenant=' + encodeURIComponent(tenant) : '');
            const res = await fetch(url, {method: 'DELETE'});
            const body = await res.json();
            if (res.ok) {
                delete app._docEditorProps[propName];
                app.showToast(`Property "${propName}" deleted from document`, 'success');
                app.renderDocPropsTable();
                app.updateDocumentRowPreview(uuid, app._docEditorProps);
            } else {
                app.showToast(body.error || 'Failed to delete property', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async addSingleDocProperty() {
        const keyInput = document.getElementById('newDocPropKey');
        const valInput = document.getElementById('newDocPropVal');
        const propName = keyInput.value.trim();
        if (!propName) { app.showToast('Property name is required', 'error'); return; }

        const parsedVal = app._parseInputValue(valInput.value);
        const col    = app._docEditorCol;
        const tenant = app._docEditorTenant;
        const uuid   = app._docEditorUuid;

        try {
            const res = await fetch('/api/document/' + encodeURIComponent(col) + '/' + encodeURIComponent(uuid) + '/property', {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    propertyName: propName,
                    propertyValue: parsedVal,
                    tenant: tenant || null
                })
            });
            const body = await res.json();
            if (res.ok) {
                app._docEditorProps[propName] = parsedVal;
                keyInput.value = '';
                valInput.value = '';
                app.showToast(`Property "${propName}" added!`, 'success');
                app.renderDocPropsTable();
                app.updateDocumentRowPreview(uuid, app._docEditorProps);
            } else {
                app.showToast(body.error || 'Failed to add property', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    formatDocEditorJson() {
        const textarea = document.getElementById('docEditorJsonText');
        try {
            const parsed = JSON.parse(textarea.value);
            textarea.value = JSON.stringify(parsed, null, 2);
        } catch(e) {
            app.showToast('Invalid JSON: ' + e.message, 'error');
        }
    },

    async saveDocFullJson() {
        const textarea = document.getElementById('docEditorJsonText');
        let parsed;
        try {
            parsed = JSON.parse(textarea.value);
        } catch(e) {
            app.showToast('Invalid JSON: ' + e.message, 'error');
            return;
        }

        const col    = app._docEditorCol;
        const tenant = app._docEditorTenant;
        const uuid   = app._docEditorUuid;

        try {
            const res = await fetch('/api/document/' + encodeURIComponent(col) + '/' + encodeURIComponent(uuid), {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    properties: parsed,
                    tenant: tenant || null
                })
            });
            const body = await res.json();
            if (res.ok) {
                app._docEditorProps = parsed;
                app.showToast('Document properties updated successfully!', 'success');
                app.updateDocumentRowPreview(uuid, parsed);
                app.closeModal('modal-edit-doc-properties');
            } else {
                app.showToast(body.error || 'Failed to update document', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    updateDocumentRowPreview(uuid, props) {
        const row = document.querySelector(`tr[data-uuid="${uuid}"]`);
        if (!row) return;
        const fullJson = JSON.stringify(props || {});
        row.setAttribute('data-search', uuid + ' ' + fullJson);
        const previewCell = row.querySelector('.doc-preview-cell');
        if (previewCell) {
            let preview = fullJson;
            if (preview.length > 120) preview = preview.substring(0, 120) + '...';
            previewCell.textContent = preview;
        }
        // Update onclick button with updated object
        const editBtn = row.querySelector('button.btn-primary');
        if (editBtn) {
            const col = app._docEditorCol;
            const tenant = app._docEditorTenant;
            editBtn.onclick = () => app.openDocumentPropertyEditor(col, tenant, uuid, props);
        }
    },

    filterDocuments(query) {
        const rawQ = (query || '').toLowerCase();
        const q = rawQ.trim();
        const rows = document.querySelectorAll('#docsTable tbody tr[data-uuid]');
        let matchCount = 0;

        rows.forEach(row => {
            if (!q) {
                row.style.display = '';
                matchCount++;
                return;
            }

            const searchData = (row.getAttribute('data-search') || '').toLowerCase();
            const rowText    = (row.textContent || '').toLowerCase();

            // Match full document properties JSON, UUID, or row text
            // Fully supports underscores, numbers, and exact substrings
            const matches = searchData.includes(q) || rowText.includes(q) || searchData.includes(rawQ);

            if (matches) {
                row.style.display = '';
                matchCount++;
            } else {
                row.style.display = 'none';
            }
        });

        document.querySelectorAll('#docFilterCount').forEach(countEl => {
            if (q) {
                countEl.textContent = `${matchCount} / ${rows.length}`;
                countEl.style.display = 'inline-block';
            } else {
                countEl.style.display = 'none';
            }
        });
    },

    // -----------------------------------------------------------------------
    // Tenant Property Values Modal & Summary
    // -----------------------------------------------------------------------
    async showTenantPropertyValues(col, tenant) {
        app._currentModalCol = col;
        app._currentModalTenant = tenant;
        document.getElementById('tenantPropModalTitle').textContent = 'Tenant: ' + tenant;
        document.getElementById('tenantPropModalSubtitle').textContent = 'Collection: ' + col;
        document.getElementById('tenantPropSearch').value = '';
        document.getElementById('tenantDescriptionText').innerHTML = '<span style="color:#888;">Fetching description...</span>';
        
        const container = document.getElementById('tenantPropertiesContainer');
        container.innerHTML = '<div style="text-align:center; padding:30px;"><div class="spinner"></div><p style="color:#666; margin-top:10px;">Fetching tenant property values...</p></div>';
        app.showModal('modal-tenant-properties');

        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(col) + '/tenant/' + encodeURIComponent(tenant) + '/property-values');
            const data = await res.json();
            if (!data.success) {
                container.innerHTML = '<div style="color:#e74c3c; padding:15px;">Failed to load properties: ' + (data.error || 'Unknown error') + '</div>';
                document.getElementById('tenantDescriptionText').innerHTML = '<span style="color:#888; font-style:italic;">No description available</span>';
                return;
            }

            // Display Tenant's Own Description
            app._currentModalDesc = data.tenant_description || '';
            const descEl = document.getElementById('tenantDescriptionText');
            if (data.tenant_description) {
                descEl.textContent = data.tenant_description;
            } else {
                descEl.innerHTML = '<span style="color:#888; font-style:italic;">No tenant-level description specified. Click Edit to add one.</span>';
            }

            // Display Document Elements Properties
            if (!data.properties || data.properties.length === 0) {
                container.innerHTML = '<div style="color:#666; padding:15px; text-align:center;">No document element properties found in this tenant.</div>';
                return;
            }

            let html = '';
            data.properties.forEach(p => {
                const count = p.val_list ? p.val_list.length : (p.values ? p.values.length : 0);
                const values = p.val_list || p.values || [];
                html += '<div class="tenant-prop-card modal-prop-item" data-name="' + p.name.toLowerCase() + '">';
                html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; flex-wrap:wrap; gap:6px;">';
                html += '<div style="display:flex; align-items:center; gap:8px;">';
                html += '<strong style="color:#333; font-size:1rem;">' + p.name + '</strong>';
                html += '<code style="background:#eef2ff; color:#4f46e5; padding:2px 6px; border-radius:3px; font-size:0.8rem;">' + p.data_type + '</code>';
                html += '</div>';
                html += '<div style="display:flex; align-items:center; gap:6px;">';
                html += '<span style="font-size:0.82rem; color:#666; background:#e5e7eb; padding:2px 8px; border-radius:10px;">' + count + ' unique (' + p.total_count + ' total)</span>';
                html += '</div>';
                html += '</div>';

                html += '<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; max-height:160px; overflow-y:auto;">';
                if (values.length > 0) {
                    values.forEach(v => {
                        const strVal = typeof v === 'object' ? JSON.stringify(v) : String(v);
                        const safeVal = strVal.replace(/"/g, '&quot;');
                        html += '<div class="prop-val-pill" title="' + safeVal + '">' + strVal + '</div>';
                    });
                } else {
                    html += '<span style="color:#999; font-size:0.85rem; font-style:italic;">No values recorded for this property</span>';
                }
                html += '</div>';
                html += '</div>';
            });
            container.innerHTML = html;
        } catch(e) {
            container.innerHTML = '<div style="color:#e74c3c; padding:15px;">Error: ' + e.message + '</div>';
        }
    },

    filterTenantProperties(query) {
        const q = (query || '').toLowerCase().trim();
        document.querySelectorAll('.modal-prop-item').forEach(el => {
            if (!q) {
                el.style.display = 'block';
                return;
            }
            const name = (el.getAttribute('data-name') || '').toLowerCase();
            const text = (el.textContent || '').toLowerCase();
            el.style.display = (name.includes(q) || text.includes(q)) ? 'block' : 'none';
        });
    },

    editCurrentTenantDesc() {
        app.showEditTenantDescModal(app._currentModalCol, app._currentModalTenant, app._currentModalDesc);
    },

    showEditTenantDescModal(col, tenant, currentDesc) {
        document.getElementById('editTenantDescCol').value    = col;
        document.getElementById('editTenantDescTenant').value = tenant;
        document.getElementById('editTenantDescText').value   = currentDesc || (document.getElementById('tenantPageDescText')?.textContent?.trim()) || '';
        app.showModal('modal-edit-tenant-desc');
    },

    async saveTenantDescription() {
        const col  = document.getElementById('editTenantDescCol').value;
        const t    = document.getElementById('editTenantDescTenant').value;
        const desc = document.getElementById('editTenantDescText').value.trim();

        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(col) + '/tenant/' + encodeURIComponent(t) + '/description', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({description: desc})
            });
            const data = await res.json();
            if (res.ok) {
                app.closeModal('modal-edit-tenant-desc');
                app.showToast('Tenant description saved successfully!', 'success');
                app._currentModalDesc = desc;
                const modalDescText = document.getElementById('tenantDescriptionText');
                if (modalDescText) modalDescText.textContent = desc;
                const pageDescText = document.getElementById('tenantPageDescText');
                if (pageDescText) pageDescText.textContent = desc;
            } else {
                app.showToast(data.error || 'Failed to save description', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    togglePropSummary() {
        const c = document.getElementById('tenantPropSummaryContent');
        const b = document.getElementById('propSummaryToggleBtn');
        if (!c) return;
        if (c.style.display === 'none') {
            c.style.display = 'flex';
            if (b) b.textContent = 'Collapse';
        } else {
            c.style.display = 'none';
            if (b) b.textContent = 'Expand';
        }
    },

    // -----------------------------------------------------------------------
    // Collection & Tenant CRUD
    // -----------------------------------------------------------------------
    async deleteCollection(name) {
        if (!confirm('Are you sure you want to delete collection "' + name + '"? All data inside it will be permanently deleted.')) return;
        try {
            const res = await fetch('/api/collection/' + encodeURIComponent(name), {method: 'DELETE'});
            const body = await res.json();
            if (res.ok) {
                app.showToast('Collection deleted successfully', 'success');
                setTimeout(() => app.viewCollections(), 600);
            } else {
                app.showToast(body.error || 'Failed to delete collection', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async createCollection() {
        const className    = document.getElementById('newClassName').value.trim();
        const description  = document.getElementById('newClassDescription').value.trim() || null;
        const multiTenancy = document.getElementById('enableMultiTenancy').checked;
        if (!className) { app.showToast('Collection name is required', 'error'); return; }
        try {
            const res  = await fetch('/api/collection', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({className, description, multiTenancy})
            });
            const body = await res.json();
            if (res.ok) {
                app.closeModal('modal-create-collection');
                app.showToast('Collection created successfully!', 'success');
                setTimeout(() => app.viewCollections(), 600);
            } else {
                app.showToast(body.error || 'Failed to create collection', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async deleteTenant(col, tenant) {
        if (!confirm('Are you sure you want to delete tenant "' + tenant + '"? All data inside will be permanently deleted.')) return;
        try {
            const res  = await fetch('/api/collection/' + encodeURIComponent(col) + '/tenant/' + encodeURIComponent(tenant), {method: 'DELETE'});
            const body = await res.json();
            if (res.ok) {
                app.showToast('Tenant deleted successfully', 'success');
                setTimeout(() => app.viewCollection(col), 600);
            } else {
                app.showToast(body.error || 'Failed to delete tenant', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async createTenant() {
        const col    = document.getElementById('tenantCollectionName').value || app._collection;
        const tenant = document.getElementById('newTenantName').value.trim();
        const desc   = document.getElementById('newTenantDescription').value.trim() || '';
        if (!tenant) { app.showToast('Tenant name is required', 'error'); return; }
        try {
            const res  = await fetch('/api/collection/' + encodeURIComponent(col) + '/tenant', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({tenantName: tenant, description: desc})
            });
            const body = await res.json();
            if (res.ok) {
                app.closeModal('modal-create-tenant');
                app.showToast('Tenant created successfully!', 'success');
                setTimeout(() => app.viewCollection(col), 600);
            } else {
                app.showToast(body.error || 'Failed to create tenant', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async deleteDocument(col, tenant, uuid) {
        if (!confirm('Are you sure you want to delete document ' + uuid + '?')) return;
        try {
            const url = '/api/document/' + encodeURIComponent(col) + '/' + encodeURIComponent(uuid)
                      + (tenant ? '?tenant=' + encodeURIComponent(tenant) : '');
            const res  = await fetch(url, {method: 'DELETE'});
            const body = await res.json();
            if (res.ok) {
                app.showToast('Document deleted', 'success');
                document.querySelector('tr[data-uuid="' + uuid + '"]')?.remove();
            } else {
                app.showToast(body.error || 'Failed to delete document', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    async uploadDocument() {
        const col    = document.getElementById('docCollectionName').value || app._collection;
        const tenant = document.getElementById('docTenantName').value || null;
        const uuid   = document.getElementById('documentUuid').value.trim() || null;
        let props;
        try {
            props = JSON.parse(document.getElementById('documentJson').value);
        } catch(e) {
            app.showToast('Invalid JSON: ' + e.message, 'error');
            return;
        }
        try {
            const res  = await fetch('/api/document/' + encodeURIComponent(col), {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({properties: props, uuid, tenant})
            });
            const body = await res.json();
            if (res.ok) {
                app.closeModal('modal-upload-doc');
                app.showToast('Document uploaded successfully (UUID: ' + body.uuid + ')', 'success');
                setTimeout(() => {
                    if (tenant) app.viewTenant(col, tenant);
                    else app.viewCollection(col);
                }, 800);
            } else {
                app.showToast(body.error || 'Failed to upload document', 'error');
            }
        } catch(e) {
            app.showToast('Error: ' + e.message, 'error');
        }
    },

    showModal(id) {
        if (id === 'modal-create-collection') {
            document.getElementById('newClassName').value = '';
            document.getElementById('newClassDescription').value = '';
            document.getElementById('enableMultiTenancy').checked = false;
        } else if (id === 'modal-create-tenant') {
            document.getElementById('tenantCollectionName').value = app._collection || '';
            document.getElementById('newTenantName').value = '';
            document.getElementById('newTenantDescription').value = '';
        } else if (id === 'modal-upload-doc') {
            const col = app._collection || '';
            const t = app._tenant || '';
            document.getElementById('docCollectionName').value = col;
            document.getElementById('docTenantName').value     = t;
            const badge = document.getElementById('uploadTargetBadge');
            if (badge) {
                badge.textContent = t ? ('Target: Collection "' + col + '" > Tenant "' + t + '"') : ('Target: Collection "' + col + '"');
            }
            document.getElementById('documentJson').value      = '{\\n  "title": "Example",\\n  "content": "Hello Weaviate"\\n}';
            document.getElementById('documentUuid').value      = '';
        }
        document.getElementById(id).style.display = 'flex';
    },

    closeModal(id) { document.getElementById(id).style.display = 'none'; },

    showToast(msg, type) {
        const c   = document.getElementById('toastContainer');
        const t   = document.createElement('div');
        const col = type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#667eea';
        t.className = 'toast ' + (type || 'info');
        t.innerHTML = '<strong style="color:' + col + '; display:block; margin-bottom:4px;">'
                    + (type === 'error' ? 'Error' : type === 'success' ? 'Success' : 'Info')
                    + ':</strong>' + msg;
        c.appendChild(t);
        setTimeout(() => t.remove(), 6000);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('createCollectionForm')?.addEventListener('submit', e => { e.preventDefault(); app.createCollection(); });
    document.getElementById('createTenantForm')?.addEventListener('submit',     e => { e.preventDefault(); app.createTenant(); });
    document.getElementById('uploadDocForm')?.addEventListener('submit',        e => { e.preventDefault(); app.uploadDocument(); });
    document.getElementById('editTenantDescForm')?.addEventListener('submit',   e => { e.preventDefault(); app.saveTenantDescription(); });
    document.getElementById('editCollectionPropForm')?.addEventListener('submit', e => { e.preventDefault(); app.saveCollectionPropertyDescription(); });
    document.getElementById('addCollectionPropForm')?.addEventListener('submit', e => { e.preventDefault(); app.addCollectionProperty(); });

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => { if (e.target === overlay) overlay.style.display = 'none'; });
    });

    document.querySelectorAll('.doc-search-input, #docSearchBox').forEach(box => {
        box.addEventListener('input', e => app.filterDocuments(e.target.value));
        box.addEventListener('keyup', e => app.filterDocuments(e.target.value));
    });
});
</script>
</body>
</html>"""


def _render(view=None, **kwargs):
    """Render the single-page template with the given view active."""
    ctx = {
        'css': _CSS,
        'view': view,
        'connected': (weaviate_client is not None),
        'weaviate_url': weaviate_url,
        'default_url': weaviate_url,
        'collections': [],
        'current_collection': None,
        'current_tenant': None,
        'tenant_status': 'Active',
        'is_tenant_active': True,
        'properties': [],
        'tenants': [],
        'documents': [],
        'tenant_properties': [],
        'tenant_description': '',
        'is_multi_tenant': False,
        'description': '',
        'error': None,
    }
    ctx.update(kwargs)
    return render_template_string(_HTML_TEMPLATE, **ctx)


# ---------------------------------------------------------------------------
# Global state  (single-process Flask dev server)
# ---------------------------------------------------------------------------
weaviate_client = None
weaviate_url = ""


def _require_client():
    if weaviate_client is None:
        return jsonify({"success": False, "error": "Not connected to Weaviate. Please connect first."}), 401
    return None


def _get_collections_list(client):
    """Robust collection fetcher: tries v4 client API first, with fallback to direct /schema REST."""
    cols = []
    # 1. Try high-level client collections.list_all(simple=False)
    try:
        raw = client.collections.list_all(simple=False)
        for name, cfg in raw.items():
            mt = False
            try:
                mt = getattr(cfg, 'multi_tenancy_config', None)
                mt = mt.enabled if mt else False
            except Exception:
                mt = False
            props = getattr(cfg, 'properties', []) or []
            cols.append({
                'name': name,
                'property_count': len(props),
                'multi_tenancy': mt,
                'description': getattr(cfg, 'description', '') or '',
            })
        if cols:
            cols.sort(key=lambda c: c['name'])
            return cols
    except Exception as e:
        print("[Warn] collections.list_all(simple=False) failed, trying REST /schema:", e)

    # 2. Fallback to direct REST endpoint /schema (works on any Weaviate version)
    try:
        res = client._connection.get('/schema')
        data = res.json() if hasattr(res, 'json') else res
        classes = data.get('classes', []) if isinstance(data, dict) else []
        for cls in classes:
            name = cls.get('class')
            props = cls.get('properties', []) or []
            mt = bool(cls.get('multiTenancyConfig', {}).get('enabled', False))
            cols.append({
                'name': name,
                'property_count': len(props),
                'multi_tenancy': mt,
                'description': cls.get('description', '') or '',
            })
        cols.sort(key=lambda c: c['name'])
        return cols
    except Exception as e:
        print("[Error] REST /schema failed:", e)
        raise e


def _extract_tenant_description(objects, tenant_name):
    """
    Finds the tenant's own description (e.g. view/table/tenant-level description)
    distinguished from individual document element descriptions (columns/chunks/rows).
    """
    if not objects:
        return ""

    # Priority 1: Check for explicit tenant/table/view description property on any object
    for obj in objects:
        props = getattr(obj, 'properties', None) or {}
        for key in ['tenant_description', 'table_description', 'view_description', 
                    'dataset_description', 'collection_description', 'entity_description']:
            val = props.get(key)
            if val and isinstance(val, str) and val.strip():
                return val.strip()

    # Priority 2: Look for an object representing the tenant/table/view itself
    for obj in objects:
        props = getattr(obj, 'properties', None) or {}
        el_type = str(props.get('element_type') or props.get('type') or props.get('kind') or props.get('role') or '').lower()
        if el_type in ['table', 'view', 'tenant', 'dataset', 'summary', 'metadata', 'tenant_metadata']:
            desc = props.get('description') or props.get('summary') or props.get('content') or props.get('text')
            if desc and isinstance(desc, str) and desc.strip():
                return desc.strip()
        
        if props.get('is_table') is True or props.get('is_view') is True or props.get('is_tenant') is True:
            desc = props.get('description') or props.get('summary') or props.get('content')
            if desc and isinstance(desc, str) and desc.strip():
                return desc.strip()

        # Name or title matches tenant_name and column_name is empty
        name_val = str(props.get('name') or props.get('title') or props.get('view_name') or props.get('table_name') or '').lower()
        col_val = props.get('column_name') or props.get('field_name') or props.get('element_name')
        if name_val == tenant_name.lower() and not col_val:
            desc = props.get('description') or props.get('summary') or props.get('content')
            if desc and isinstance(desc, str) and desc.strip():
                return desc.strip()

    # Priority 3: Look for object with column_name is None while other objects have column_name
    has_column_fields = any((getattr(obj, 'properties', None) or {}).get('column_name') or (getattr(obj, 'properties', None) or {}).get('field_name') for obj in objects)
    if has_column_fields:
        for obj in objects:
            props = getattr(obj, 'properties', None) or {}
            if not props.get('column_name') and not props.get('field_name'):
                desc = props.get('description') or props.get('summary')
                if desc and isinstance(desc, str) and desc.strip():
                    return desc.strip()

    # Priority 4: Look for object where name or title matches tenant_name
    for obj in objects:
        props = getattr(obj, 'properties', None) or {}
        for k in ['name', 'title', 'view_name', 'table_name']:
            if str(props.get(k) or '').lower() == tenant_name.lower():
                desc = props.get('description') or props.get('summary') or props.get('content')
                if desc and isinstance(desc, str) and desc.strip():
                    return desc.strip()

    # Priority 5: If all objects share the exact same description string
    all_descriptions = set()
    for obj in objects:
        props = getattr(obj, 'properties', None) or {}
        for k, v in props.items():
            if k.lower() == 'description' and v and isinstance(v, str) and v.strip():
                all_descriptions.add(v.strip())
    if len(all_descriptions) == 1:
        return list(all_descriptions)[0]

    return ""


def _get_tenant_property_values(client, collection_name, tenant_name, limit=100):
    """Extracts all properties, document elements, and the tenant's own description."""
    coll = client.collections.get(collection_name)
    try:
        tenant_coll = coll.with_tenant(tenant_name)
    except Exception:
        tenant_coll = coll

    # 1. Get collection schema properties
    props_meta = {}
    try:
        res = client._connection.get(f'/schema/{collection_name}')
        data = res.json() if hasattr(res, 'json') else res
        for p in data.get('properties', []):
            dt = p.get('dataType', [])
            props_meta[p.get('name')] = dt[0] if isinstance(dt, list) and len(dt) > 0 else str(dt)
    except Exception:
        try:
            cfg = coll.config.get()
            for p in cfg.properties:
                props_meta[p.name] = str(getattr(p.data_type, 'value', p.data_type))
        except Exception:
            pass

    # 2. Fetch objects
    docs_list = []
    prop_values_map = {p: [] for p in props_meta}
    total_objects = 0
    tenant_desc = ""
    try:
        result = tenant_coll.query.fetch_objects(limit=limit)
        total_objects = len(result.objects)
        
        # Extract tenant-level description
        tenant_desc = _extract_tenant_description(result.objects, tenant_name)

        for obj in result.objects:
            obj_props = obj.properties or {}
            for k, v in obj_props.items():
                if k not in prop_values_map:
                    prop_values_map[k] = []
                prop_values_map[k].append(v)

            preview = json.dumps(obj_props, default=str)
            if len(preview) > 120:
                preview = preview[:120] + '...'

            docs_list.append({
                'uuid': str(obj.uuid),
                'properties': obj_props,
                'properties_json': json.dumps(obj_props, default=str),
                'properties_preview': preview,
            })
    except Exception as qe:
        print(f"Query tenant {tenant_name} objects error:", qe)

    summary = []
    for prop_name, values in prop_values_map.items():
        non_null_values = [v for v in values if v is not None]
        unique_values = []
        seen = set()
        for v in non_null_values:
            rep = str(v)
            if rep not in seen:
                seen.add(rep)
                unique_values.append(v)
        summary.append({
            'name': prop_name,
            'data_type': props_meta.get(prop_name, 'string'),
            'total_count': len(non_null_values),
            'unique_count': len(unique_values),
            'val_list': unique_values,
            'values': unique_values,
        })

    summary.sort(key=lambda x: x['name'].lower())

    return {
        'total_objects': total_objects,
        'tenant_description': tenant_desc,
        'summary': summary,
        'docs': docs_list
    }


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if weaviate_client:
        return redirect('/collections')
    return _render()


@app.route('/collections')
def page_collections():
    if not weaviate_client:
        return redirect('/')
    try:
        cols = _get_collections_list(weaviate_client)
        return _render(view='collections', collections=cols)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return _render(view='collections', collections=[], error=f"Could not load collections: {e}")


@app.route('/collection/<collection_name>')
def page_collection(collection_name):
    if not weaviate_client:
        return redirect('/')
    try:
        coll = weaviate_client.collections.get(collection_name)
        props = []
        is_multi_tenant = False
        desc = ""

        # Fetch schema details (try direct REST /schema/<name> first)
        try:
            res = weaviate_client._connection.get(f'/schema/{collection_name}')
            data = res.json() if hasattr(res, 'json') else res
            desc = data.get('description', '') or ''
            is_multi_tenant = bool(data.get('multiTenancyConfig', {}).get('enabled', False))
            for p in data.get('properties', []):
                dt = p.get('dataType', [])
                dt_str = dt[0] if isinstance(dt, list) and len(dt) > 0 else str(dt)
                props.append({
                    'name': p.get('name'),
                    'data_type': dt_str,
                    'description': p.get('description', '') or '-',
                })
        except Exception:
            try:
                cfg = coll.config.get()
                desc = cfg.description or ''
                is_multi_tenant = bool(cfg.multi_tenancy_config.enabled) if cfg.multi_tenancy_config else False
                for p in cfg.properties:
                    props.append({
                        'name': p.name,
                        'data_type': str(getattr(p.data_type, 'value', p.data_type)),
                        'description': p.description or '-',
                    })
            except Exception as ce:
                print("Could not get collection config:", ce)

        # Tenants (if multi-tenant)
        tenants = []
        if is_multi_tenant:
            try:
                t_dict = coll.tenants.get()
                for t in t_dict.values():
                    status = getattr(t, 'activity_status', 'Active')
                    if hasattr(status, 'value'):
                        status = status.value
                    
                    # Quick fetch of tenant description
                    t_desc = ""
                    try:
                        t_coll = coll.with_tenant(t.name)
                        sample_objs = t_coll.query.fetch_objects(limit=5).objects
                        t_desc = _extract_tenant_description(sample_objs, t.name)
                    except Exception:
                        t_desc = ""

                    tenants.append({
                        'name': t.name,
                        'activity_status': str(status),
                        'description': t_desc,
                    })
                tenants.sort(key=lambda t: t['name'])
            except Exception as te:
                print("Could not get tenants:", te)

        # Documents (if single-tenant / standard collection)
        documents = []
        if not is_multi_tenant:
            try:
                result = coll.query.fetch_objects(limit=100)
                for obj in result.objects:
                    obj_props = obj.properties or {}
                    preview = json.dumps(obj_props, default=str)
                    if len(preview) > 120:
                        preview = preview[:120] + '...'
                    documents.append({
                        'uuid': str(obj.uuid),
                        'properties': obj_props,
                        'properties_json': json.dumps(obj_props, default=str),
                        'properties_preview': preview,
                    })
            except Exception as de:
                print("Could not get objects:", de)

        return _render(
            view='collection',
            current_collection=collection_name,
            properties=props,
            is_multi_tenant=is_multi_tenant,
            tenants=tenants,
            documents=documents,
            description=desc,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return redirect('/collections')


@app.route('/tenant/<collection_name>/<tenant_name>')
def page_tenant(collection_name, tenant_name):
    if not weaviate_client:
        return redirect('/')
    try:
        tenant_data = _get_tenant_property_values(weaviate_client, collection_name, tenant_name, limit=100)
        
        # Also get tenant activity status
        coll = weaviate_client.collections.get(collection_name)
        tenant_status = "Active"
        try:
            t_obj = coll.tenants.get_by_name(tenant_name)
            raw_s = getattr(t_obj, 'activity_status', 'Active')
            if hasattr(raw_s, 'value'):
                raw_s = raw_s.value
            tenant_status = str(raw_s)
        except Exception:
            pass
        
        is_active = tenant_status.upper() in ['ACTIVE', 'HOT', 'TRUE', '1']

        return _render(
            view='tenant',
            current_collection=collection_name,
            current_tenant=tenant_name,
            tenant_status=tenant_status,
            is_tenant_active=is_active,
            tenant_description=tenant_data['tenant_description'],
            documents=tenant_data['docs'],
            tenant_properties=tenant_data['summary'],
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return redirect(f'/collection/{collection_name}')


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route('/api/connect', methods=['POST'])
def api_connect():
    global weaviate_client, weaviate_url
    data    = request.get_json(force=True)
    url     = (data.get('url') or '').rstrip('/')
    api_key = (data.get('apiKey') or '').strip()

    if not url:
        return jsonify({"success": False, "error": "URL is required"}), 400

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    # Close any existing connection cleanly
    if weaviate_client:
        try:
            weaviate_client.close()
        except Exception:
            pass
        weaviate_client = None
        weaviate_url = ""

    try:
        auth = weaviate.auth.AuthApiKey(api_key) if api_key else None
        parsed = urllib.parse.urlparse(url)
        host   = parsed.hostname or parsed.path
        port   = parsed.port or (443 if parsed.scheme == 'https' else 80)
        secure = parsed.scheme == 'https'

        headers = {}
        if os.environ.get("OPENAI_API_KEY"):
            headers["X-OpenAI-Api-Key"] = os.environ.get("OPENAI_API_KEY")

        if "weaviate.cloud" in host or "weaviate.network" in host:
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=auth,
                headers=headers or None,
            )
        else:
            client = weaviate.connect_to_custom(
                http_host=host,
                http_port=port,
                http_secure=secure,
                grpc_host=host,
                grpc_port=50051,
                grpc_secure=secure,
                auth_credentials=auth,
                headers=headers or None,
            )

        # Verify connection
        client.is_ready()
        weaviate_client = client
        weaviate_url = url
        return jsonify({"success": True, "url": url})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    global weaviate_client, weaviate_url
    if weaviate_client:
        try:
            weaviate_client.close()
        except Exception:
            pass
        weaviate_client = None
        weaviate_url = ""
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Tenant Status: Active <-> Inactive
# ---------------------------------------------------------------------------
@app.route('/api/collection/<collection_name>/tenant/<tenant_name>/status', methods=['POST'])
def api_update_tenant_status(collection_name, tenant_name):
    err = _require_client()
    if err: return err
    data = request.get_json(force=True)
    target_status = (data.get('status') or '').strip().upper()
    if not target_status:
        return jsonify({"success": False, "error": "status is required"}), 400

    is_active = target_status in ['ACTIVE', 'HOT']
    status_str = "ACTIVE" if is_active else "INACTIVE"
    weaviate_status_enum = wvc.tenants.TenantActivityStatus.HOT if is_active else wvc.tenants.TenantActivityStatus.COLD

    try:
        coll = weaviate_client.collections.get(collection_name)
        # 1. Try high-level client activate / deactivate
        try:
            if is_active:
                coll.tenants.activate(tenant_name)
            else:
                coll.tenants.deactivate(tenant_name)
        except Exception as e1:
            print("[Warn] coll.tenants.activate/deactivate failed, trying coll.tenants.update:", e1)
            try:
                coll.tenants.update([wvc.tenants.Tenant(name=tenant_name, activity_status=weaviate_status_enum)])
            except Exception as e2:
                print("[Warn] coll.tenants.update failed, trying REST /schema tenants PUT:", e2)
                payload = [{"name": tenant_name, "activityStatus": "HOT" if is_active else "COLD"}]
                weaviate_client._connection.put(f"/schema/{collection_name}/tenants", payload)

        return jsonify({"success": True, "tenant": tenant_name, "status": status_str})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Tenant Description and Property Values
# ---------------------------------------------------------------------------
@app.route('/api/collection/<collection_name>/tenant/<tenant_name>/property-values')
def api_tenant_property_values(collection_name, tenant_name):
    err = _require_client()
    if err: return err
    try:
        data = _get_tenant_property_values(weaviate_client, collection_name, tenant_name, limit=100)
        return jsonify({
            "success": True,
            "collection": collection_name,
            "tenant": tenant_name,
            "total_objects": data['total_objects'],
            "tenant_description": data['tenant_description'],
            "properties": data['summary']
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/collection/<collection_name>/tenant/<tenant_name>/description', methods=['POST'])
def api_save_tenant_description(collection_name, tenant_name):
    err = _require_client()
    if err: return err
    data = request.get_json(force=True)
    description = (data.get('description') or '').strip()
    try:
        coll = weaviate_client.collections.get(collection_name)
        t_coll = coll.with_tenant(tenant_name)
        res = t_coll.query.fetch_objects(limit=100)
        updated = False

        for obj in res.objects:
            p = obj.properties or {}
            el_type = str(p.get('element_type') or p.get('type') or p.get('kind') or '').lower()
            if el_type in ['table', 'view', 'tenant', 'tenant_metadata', 'metadata']:
                new_props = dict(p)
                new_props['description'] = description
                t_coll.data.replace(uuid=obj.uuid, properties=new_props)
                updated = True
                break

        if not updated:
            t_coll.data.insert(
                properties={
                    "description": description,
                    "type": "tenant_metadata",
                    "name": tenant_name,
                }
            )
        return jsonify({"success": True, "description": description})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Collection Properties (Edit Description, Add Property, Delete Property)
# ---------------------------------------------------------------------------
@app.route('/api/collection/<collection_name>/property/<prop_name>', methods=['PUT'])
def api_update_collection_property(collection_name, prop_name):
    """Edit property description in collection schema."""
    err = _require_client()
    if err: return err
    data = request.get_json(force=True)
    new_desc = (data.get('description') or '').strip()
    try:
        coll = weaviate_client.collections.get(collection_name)
        try:
            coll.config.update(property_descriptions={prop_name: new_desc})
        except Exception as ce:
            print("[Warn] coll.config.update(property_descriptions) failed, trying REST:", ce)
            # Try REST schema update if available
            weaviate_client._connection.put(f"/schema/{collection_name}", {
                "class": collection_name,
                "properties": [{"name": prop_name, "description": new_desc}]
            })
        return jsonify({"success": True, "collection": collection_name, "propertyName": prop_name, "description": new_desc})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/collection/<collection_name>/property', methods=['POST'])
def api_add_collection_property(collection_name):
    """Add a new property to collection schema."""
    err = _require_client()
    if err: return err
    data = request.get_json(force=True)
    name = (data.get('name') or '').strip()
    data_type_str = (data.get('dataType') or 'text').strip().lower()
    description = (data.get('description') or '').strip() or None

    if not name:
        return jsonify({"success": False, "error": "Property name is required"}), 400

    type_map = {
        'text': wvc.config.DataType.TEXT,
        'int': wvc.config.DataType.INT,
        'integer': wvc.config.DataType.INT,
        'number': wvc.config.DataType.NUMBER,
        'float': wvc.config.DataType.NUMBER,
        'boolean': wvc.config.DataType.BOOL,
        'bool': wvc.config.DataType.BOOL,
        'date': wvc.config.DataType.DATE,
        'text[]': wvc.config.DataType.TEXT_ARRAY,
        'int[]': wvc.config.DataType.INT_ARRAY,
        'number[]': wvc.config.DataType.NUMBER_ARRAY,
        'boolean[]': wvc.config.DataType.BOOL_ARRAY,
    }
    wvc_type = type_map.get(data_type_str, wvc.config.DataType.TEXT)

    try:
        coll = weaviate_client.collections.get(collection_name)
        coll.config.add_property(wvc.config.Property(name=name, data_type=wvc_type, description=description))
        return jsonify({"success": True, "name": name, "dataType": data_type_str, "description": description})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/collection/<collection_name>/property/<prop_name>', methods=['DELETE'])
def api_delete_collection_property(collection_name, prop_name):
    """
    Deletes property data across all documents in this collection (and across all tenants).
    Weaviate schemas retain background column definitions once created, so this scrubs the property
    cleanly from every object in the database.
    """
    err = _require_client()
    if err: return err
    try:
        coll = weaviate_client.collections.get(collection_name)
        is_mt = False
        try:
            cfg = coll.config.get()
            is_mt = bool(cfg.multi_tenancy_config.enabled) if cfg.multi_tenancy_config else False
        except Exception:
            pass

        updated_count = 0
        if is_mt:
            t_dict = coll.tenants.get()
            for t_name in t_dict.keys():
                try:
                    t_coll = coll.with_tenant(t_name)
                    objs = t_coll.query.fetch_objects(limit=1000).objects
                    for obj in objs:
                        if prop_name in (obj.properties or {}):
                            new_props = dict(obj.properties)
                            del new_props[prop_name]
                            t_coll.data.replace(uuid=obj.uuid, properties=new_props)
                            updated_count += 1
                except Exception as te:
                    print(f"Error scrubbing prop {prop_name} in tenant {t_name}:", te)
        else:
            objs = coll.query.fetch_objects(limit=1000).objects
            for obj in objs:
                if prop_name in (obj.properties or {}):
                    new_props = dict(obj.properties)
                    del new_props[prop_name]
                    coll.data.replace(uuid=obj.uuid, properties=new_props)
                    updated_count += 1

        return jsonify({
            "success": True,
            "collection": collection_name,
            "deletedProperty": prop_name,
            "updatedDocuments": updated_count,
            "message": f"Property '{prop_name}' removed from {updated_count} document(s)."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/collection/<collection_name>/tenant/<tenant_name>/property/<prop_name>', methods=['DELETE'])
def api_delete_tenant_property(collection_name, tenant_name, prop_name):
    """Deletes property data from all documents inside a specific tenant."""
    err = _require_client()
    if err: return err
    try:
        coll = weaviate_client.collections.get(collection_name)
        t_coll = coll.with_tenant(tenant_name)
        objs = t_coll.query.fetch_objects(limit=1000).objects
        updated_count = 0

        for obj in objs:
            if prop_name in (obj.properties or {}):
                new_props = dict(obj.properties)
                del new_props[prop_name]
                t_coll.data.replace(uuid=obj.uuid, properties=new_props)
                updated_count += 1

        return jsonify({
            "success": True,
            "tenant": tenant_name,
            "deletedProperty": prop_name,
            "updatedDocuments": updated_count,
            "message": f"Property '{prop_name}' removed from {updated_count} document(s) in tenant '{tenant_name}'."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Document Properties (Edit & Delete properties of individual documents)
# ---------------------------------------------------------------------------
@app.route('/api/document/<collection_name>/<doc_uuid>', methods=['PUT'])
def api_update_document_full(collection_name, doc_uuid):
    """Replace all properties of a specific document."""
    err = _require_client()
    if err: return err
    data = request.get_json(force=True)
    properties  = data.get('properties') or {}
    tenant_name = data.get('tenant') or request.args.get('tenant') or None
    try:
        coll = weaviate_client.collections.get(collection_name)
        if tenant_name:
            coll = coll.with_tenant(tenant_name)
        coll.data.replace(uuid=doc_uuid, properties=properties)
        return jsonify({"success": True, "uuid": doc_uuid, "properties": properties})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/document/<collection_name>/<doc_uuid>/property', methods=['POST', 'PATCH'])
def api_update_document_property(collection_name, doc_uuid):
    """Set or edit an individual property on a document."""
    err = _require_client()
    if err: return err
    data = request.get_json(force=True)
    prop_name = (data.get('propertyName') or '').strip()
    prop_val  = data.get('propertyValue')
    tenant_name = data.get('tenant') or request.args.get('tenant') or None

    if not prop_name:
        return jsonify({"success": False, "error": "propertyName is required"}), 400

    try:
        coll = weaviate_client.collections.get(collection_name)
        if tenant_name:
            coll = coll.with_tenant(tenant_name)

        coll.data.update(uuid=doc_uuid, properties={prop_name: prop_val})
        return jsonify({"success": True, "uuid": doc_uuid, "propertyName": prop_name, "propertyValue": prop_val})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/document/<collection_name>/<doc_uuid>/property/<prop_name>', methods=['DELETE'])
def api_delete_document_property(collection_name, doc_uuid, prop_name):
    """Delete a specific property from an individual document."""
    err = _require_client()
    if err: return err
    tenant_name = request.args.get('tenant') or None
    try:
        coll = weaviate_client.collections.get(collection_name)
        if tenant_name:
            coll = coll.with_tenant(tenant_name)

        obj = coll.query.fetch_object_by_id(doc_uuid)
        if not obj:
            return jsonify({"success": False, "error": "Document not found"}), 404

        current_props = dict(obj.properties or {})
        if prop_name in current_props:
            del current_props[prop_name]

        coll.data.replace(uuid=doc_uuid, properties=current_props)
        return jsonify({"success": True, "uuid": doc_uuid, "deletedProperty": prop_name, "remainingProperties": current_props})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Collection CRUD
# ---------------------------------------------------------------------------
@app.route('/api/collection', methods=['POST'])
def api_create_collection():
    err = _require_client()
    if err: return err
    data          = request.get_json(force=True)
    class_name    = (data.get('className') or '').strip()
    description   = (data.get('description') or '').strip() or None
    multi_tenancy = bool(data.get('multiTenancy', False))

    if not class_name:
        return jsonify({"success": False, "error": "className is required"}), 400
    try:
        mt_cfg = wvc.config.Configure.multi_tenancy(enabled=True) if multi_tenancy else None
        weaviate_client.collections.create(
            name=class_name,
            description=description,
            multi_tenancy_config=mt_cfg,
        )
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/collection/<collection_name>', methods=['DELETE'])
def api_delete_collection(collection_name):
    err = _require_client()
    if err: return err
    try:
        weaviate_client.collections.delete(collection_name)
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/collection/<collection_name>/tenant', methods=['POST'])
def api_create_tenant(collection_name):
    err = _require_client()
    if err: return err
    data        = request.get_json(force=True)
    tenant_name = (data.get('tenantName') or '').strip()
    description = (data.get('description') or '').strip()
    if not tenant_name:
        return jsonify({"success": False, "error": "tenantName is required"}), 400
    try:
        coll = weaviate_client.collections.get(collection_name)
        coll.tenants.create([wvc.tenants.Tenant(name=tenant_name)])
        if description:
            try:
                t_coll = coll.with_tenant(tenant_name)
                t_coll.data.insert(properties={"description": description, "type": "tenant_metadata", "name": tenant_name})
            except Exception as de:
                print("Could not insert tenant metadata doc:", de)
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/collection/<collection_name>/tenant/<tenant_name>', methods=['DELETE'])
def api_delete_tenant(collection_name, tenant_name):
    err = _require_client()
    if err: return err
    try:
        coll = weaviate_client.collections.get(collection_name)
        coll.tenants.remove([wvc.tenants.Tenant(name=tenant_name)])
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/document/<collection_name>', methods=['POST'])
def api_upload_document(collection_name):
    err = _require_client()
    if err: return err
    data        = request.get_json(force=True)
    properties  = data.get('properties') or {}
    uuid        = data.get('uuid') or None
    tenant_name = data.get('tenant') or None
    try:
        coll = weaviate_client.collections.get(collection_name)
        if tenant_name:
            coll = coll.with_tenant(tenant_name)
        new_uuid = coll.data.insert(properties=properties, uuid=uuid)
        return jsonify({"success": True, "uuid": str(new_uuid)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/document/<collection_name>/<doc_uuid>', methods=['DELETE'])
def api_delete_document(collection_name, doc_uuid):
    err = _require_client()
    if err: return err
    tenant_name = request.args.get('tenant') or None
    try:
        coll = weaviate_client.collections.get(collection_name)
        if tenant_name:
            coll = coll.with_tenant(tenant_name)
        coll.data.delete_by_id(doc_uuid)
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
