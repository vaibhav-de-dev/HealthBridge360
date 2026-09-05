from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_ROOT = "/home/salvador/HealthBridge360"
PYTHON_BIN = f"{PROJECT_ROOT}/.venv/bin/python"


with DAG(
    dag_id="healthbridge360_phase7_validation",
    start_date=datetime(2026, 8, 23),
    schedule=None,
    catchup=False,
    tags=["healthbridge360", "phase7"],
) as dag:

    validate_environment = BashOperator(
        task_id="validate_healthbridge360_environment",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"{PYTHON_BIN} -c "
            "\"import api.config; "
            "print('HealthBridge360 environment validation: SUCCESS')\""
        ),
    )
