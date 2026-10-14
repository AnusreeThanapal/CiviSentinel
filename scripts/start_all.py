import os
import sys
import subprocess
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

def start_services():
    print("=" * 60)
    print("Launching Civic Pipeline & Apache Monitoring Stack...")
    print("=" * 60)

    # 1. Start Backend on port 8000
    print("[1/4] Starting FastAPI Backend on port 8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 2. Start Frontend on port 5173
    print("[2/4] Starting React / Vite Frontend on port 5173...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 3. Start Airflow Webserver UI on port 8080
    print("[3/4] Starting Apache Airflow Webserver on port 8080...")
    airflow_proc = subprocess.Popen(
        [sys.executable, os.path.join(SCRIPTS_DIR, "airflow_server.py")],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 4. Start Spark Application Web UI on port 4040
    print("[4/4] Starting Apache Spark Web UI on port 4040...")
    spark_proc = subprocess.Popen(
        [sys.executable, os.path.join(SCRIPTS_DIR, "spark_server.py")],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(3)
    print("\nAll 4 services launched successfully!")
    print("  - Frontend Command Center: http://localhost:5173")
    print("  - Backend REST API Docs:   http://localhost:8000/api/docs")
    print("  - Apache Airflow Web UI:   http://localhost:8080")
    print("  - Airflow DAG Grid View:   http://localhost:8080/dags/civic_pipeline_maintenance_dag/grid")
    print("  - Apache Spark Web UI:     http://localhost:4040")
    print("=" * 60)

    try:
        # Keep process alive
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        airflow_proc.terminate()
        spark_proc.terminate()

if __name__ == "__main__":
    start_services()
