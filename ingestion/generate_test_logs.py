import random
from datetime import datetime, timedelta
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_test_logs(filename, num_logs=5000, days_back=30):
    # Lista de IPs para simular diferentes fuentes
    ips = [
        "192.168.1.100", "192.168.1.101", "192.168.1.102", "192.168.1.103",
        "10.0.0.50", "10.0.0.51", "172.16.0.10", "172.16.0.11",
        "203.0.113.1", "203.0.113.2"
    ]

    # Lista de usuarios para simular actividad
    users = ["admin", "user1", "user2", "guest", "testuser", "sysadmin"]

    # Lista de métodos HTTP
    methods = ["GET", "POST", "PUT", "DELETE"]

    # Lista de endpoints para simular solicitudes
    endpoints = [
        "/login", "/api/users", "/api/data", "/dashboard", "/api/auth",
        "/api/update", "/api/delete", "/api/query", "/api/search"
    ]

    # Patrones de SQL injection
    sql_injections = [
        "?user=admin' OR '1'='1",
        "SELECT * FROM users WHERE id=1; --",
        "?query=SELECT * FROM data",
        "DROP TABLE users;",
        "?id=1 UNION SELECT 1,2,3--",
        "' OR '1'='1' --"
    ]

    # Patrones de actividad sospechosa
    suspicious_messages = [
        "Malware detected in request",
        "Exploit attempt detected",
        "Ransomware signature found",
        "Brute force attempt on /login",
        "Unauthorized access attempt"
    ]

    # Lista de ubicaciones simuladas para IPs
    locations = ["US", "EU", "ASIA", "LATAM"]

    # Período de tiempo: últimos 30 días
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days_back)

    # Asegurar una distribución equitativa entre tenants
    logs_per_tenant = num_logs // 2  # 2500 logs por tenant
    tenant_logs = {"tenant1": [], "tenant2": []}

    try:
        # Convertir filename a una ruta absoluta si no lo es
        if not os.path.isabs(filename):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            filename = os.path.join(base_dir, "ingestion", filename)

        # Crear el directorio si no existe
        dirname = os.path.dirname(filename)
        if dirname:  # Solo intentar crear el directorio si dirname no está vacío
            os.makedirs(dirname, exist_ok=True)
        else:
            logger.warning("No directory specified for the file; using current directory.")

        for tenant in ["tenant1", "tenant2"]:
            for i in range(logs_per_tenant):
                # Generar un timestamp dentro del rango de tiempo
                seconds_range = (end_time - start_time).total_seconds()
                random_seconds = random.uniform(0, seconds_range)
                timestamp = start_time + timedelta(seconds=random_seconds)
                timestamp_str = timestamp.isoformat() + "Z"

                # Seleccionar IP y ubicación
                ip = random.choice(ips)
                location = random.choice(locations)

                # Generar un mensaje de log realista
                log_type = random.choices(
                    ["normal", "failed", "sql_injection", "suspicious"],
                    weights=[0.5, 0.3, 0.1, 0.1],  # 50% normal, 30% failed, 10% sql_injection, 10% suspicious
                    k=1
                )[0]

                if log_type == "normal":
                    method = random.choice(methods)
                    endpoint = random.choice(endpoints)
                    user = random.choice(users)
                    message = f"{method} {endpoint} by {user} from {ip} ({location})"

                elif log_type == "failed":
                    user = random.choice(users)
                    message = f"Failed login attempt for {user} from {ip} ({location})"

                elif log_type == "sql_injection":
                    method = random.choice(methods)
                    endpoint = random.choice(endpoints)
                    injection = random.choice(sql_injections)
                    message = f"{method} {endpoint}{injection} from {ip} ({location})"

                else:  # suspicious
                    user = random.choice(users)
                    suspicion = random.choice(suspicious_messages)
                    message = f"{suspicion} by {user} from {ip} ({location})"

                log = f"{timestamp_str} {tenant} {message}\n"
                tenant_logs[tenant].append(log)

        # Mezclar los logs de ambos tenants para simular un orden más realista
        all_logs = tenant_logs["tenant1"] + tenant_logs["tenant2"]
        random.shuffle(all_logs)

        # Escribir los logs en el archivo
        with open(filename, 'w') as f:
            f.writelines(all_logs)

        logger.info(f"Generated {num_logs} test logs in {filename} covering the last {days_back} days.")
    except Exception as e:
        logger.error(f"Error generating test logs: {str(e)}")
        raise

if __name__ == "__main__":
    # Usar una ruta absoluta para test_logs.txt
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logs_file = os.path.join(base_dir, "ingestion", "test_logs.txt")
    generate_test_logs(logs_file, num_logs=5000, days_back=30)