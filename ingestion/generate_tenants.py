from elasticsearch import Elasticsearch

def generate_tenants():
    es = Elasticsearch(["http://localhost:9200"])
    if not es.ping():
        raise Exception("Failed to connect to Elasticsearch")

    # Lista de tenants
    tenants = [
        {"id": "tenant1", "name": "Tenant 1", "index_name": "logs-tenant1"},
        {"id": "tenant2", "name": "Tenant 2", "index_name": "logs-tenant2"}
    ]

    # Crear el índice tenants si no existe
    if not es.indices.exists(index="tenants"):
        print("Creating tenants index...")
        es.indices.create(index="tenants")
    else:
        # Verificar si el índice tiene datos
        result = es.count(index="tenants")
        if result["count"] == 0:
            print("Tenants index is empty, populating with default tenants...")
        else:
            print(f"Tenants index already populated with {result['count']} documents, skipping initialization.")
            return

    # Insertar los tenants
    for tenant in tenants:
        es.index(index="tenants", id=tenant["id"], document=tenant)
    print("Tenants indexed successfully.")

    # Forzar un refresh
    es.indices.refresh(index="tenants")
    print("Tenants index refreshed.")

if __name__ == "__main__":
    generate_tenants()