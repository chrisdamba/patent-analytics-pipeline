from airflow import DAG
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook
from airflow.operators.python_operator import PythonOperator


def incremental_load(ds, **kwargs):
    hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
    conn = hook.get_conn()
    cursor = conn.cursor()

    # Step 1: Get the last load date
    cursor.execute("SELECT MAX(last_load_date) FROM staging_db.cybersyn.metadata WHERE table_name = 'uspto_patent_index'")
    last_load_date = cursor.fetchone()[0]

    # Step 2: Load new data since the last load date
    load_sql = f"""
        INSERT INTO staging_db.cybersyn.uspto_patent_index
        SELECT * FROM US_PATENT_GRANTS.cybersyn.uspto_patent_index
        WHERE DOCUMENT_PUBLICATION_DATE > '{last_load_date}';
    """
    cursor.execute(load_sql)

    # Step 3: Update the metadata table with the new last load date
    update_metadata_sql = f"""
        UPDATE staging_db.cybersyn.metadata
        SET last_load_date = CURRENT_DATE()
        WHERE table_name = 'uspto_patent_index';
    """
    cursor.execute(update_metadata_sql)
    conn.commit()

with DAG(
        'incremental_load_uspto_patent_index',
        description='DAG for incremental load of USPTO Patent Index data',
        schedule_interval='0 0 * * 2',  # At 00:00 on Tuesday
        catchup=False
) as dag:

    incremental_load_task = PythonOperator(
        task_id='incremental_load',
        provide_context=True,
        python_callable=incremental_load,
        dag=dag,
    )

    incremental_load_task
