import os
import time
from datetime import datetime

SERVICE_NAME = "Construction Agents Worker"

def main():
    print(f"[{SERVICE_NAME}] iniciado.")
    print(f"DATABASE_URL definido: {bool(os.getenv('DATABASE_URL'))}")
    print(f"REDIS_URL definido: {bool(os.getenv('REDIS_URL'))}")

    while True:
        print(f"[{SERVICE_NAME}] heartbeat {datetime.now().isoformat()}")
        time.sleep(60)

if __name__ == "__main__":
    main()
