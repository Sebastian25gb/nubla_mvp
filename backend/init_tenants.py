from elasticsearch import Elasticsearch

es = Elasticsearch(["http://localhost:9200"])

tenants = [
    {"id": "tenant1", "name": "Tenant 1", "index_name": "logs-tenant1"},
    {"id": "tenant2", "name": "Tenant 2", "index_name": "logs-tenant2"}
]

# Create tenants index and populate it
if not es.indices.exists(index="tenants"):
    es.indices.create(index="tenants")
for tenant in tenants:
    es.index(index="tenants", id=tenant["id"], body=tenant)

# Create indices for each tenant
for tenant in tenants:
    if not es.indices.exists(index=tenant["index_name"]):
        es.indices.create(index=tenant["index_name"])

print("Tenants and their indices initialized.")