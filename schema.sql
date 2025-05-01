CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    tenant VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    bytes INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar clientes iniciales
INSERT INTO clients (tenant) VALUES ('tenant1'), ('tenant2');