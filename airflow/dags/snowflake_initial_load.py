from contextlib import closing
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook


def generate_date_ranges(start_year=1976, interval=5):
    start_date = datetime(start_year, 1, 1).date()  # Corrected to datetime().date()
    end_date = datetime.now().date()
    while start_date <= end_date:
        next_end_date = start_date + timedelta(days=365 * interval - 1)
        yield start_date, min(next_end_date, end_date)  # Handle last interval
        start_date = next_end_date + timedelta(days=1)


with DAG(
        dag_id='snowflake_initial_load',
        description='Pipeline for US Patent Grants data from Snowflake to S3',
        schedule_interval='@once',  # Run once for the initial import
        start_date=days_ago(2),
        catchup=False
) as dag:

    create_staging_db = SnowflakeOperator(
        task_id='create_staging_db',
        snowflake_conn_id='snowflake_default',
        sql="""
            CREATE OR REPLACE DATABASE staging_db;
            
            USE DATABASE staging_db; 
            GRANT USAGE ON DATABASE staging_db TO ROLE data_transfer_role;
            
            GRANT USAGE ON INTEGRATION gcs_int TO ROLE data_transfer_role;
            
            CREATE SCHEMA IF NOT EXISTS cybersyn;
            CREATE SCHEMA IF NOT EXISTS stages;
            
            GRANT USAGE ON SCHEMA staging_db.stages TO ROLE data_transfer_role;
            GRANT CREATE STAGE ON SCHEMA staging_db.stages TO ROLE data_transfer_role;
            
            USE DATABASE staging_db;
            USE SCHEMA cybersyn;
        """
    )

    load_contributor_index = SnowflakeOperator(
        task_id='load_contributor_index',
        snowflake_conn_id='snowflake_default',
        sql="""
            CREATE OR REPLACE TABLE staging_db.cybersyn.uspto_contributor_index AS
            SELECT * FROM US_PATENT_GRANTS.cybersyn.uspto_contributor_index;
        """
    )

    load_relationships = SnowflakeOperator(
        task_id='load_patent_contributor_relationships',
        snowflake_conn_id='snowflake_default',
        sql="""
            CREATE OR REPLACE TABLE staging_db.cybersyn.uspto_patent_contributor_relationships AS
            SELECT * FROM US_PATENT_GRANTS.cybersyn.uspto_patent_contributor_relationships;
        """
    )


    def load_patent_index_batch(**kwargs):
        with closing(SnowflakeHook(snowflake_conn_id='snowflake_default').get_conn()) as conn:
            with conn.cursor() as cur:
                start_date_str = kwargs['start_date'].strftime('%Y-%m-%d')  # Convert to string
                end_date_str = kwargs['end_date'].strftime('%Y-%m-%d')
                cur.execute(f"""
                    CREATE OR REPLACE TABLE staging_db.cybersyn.uspto_patent_index AS 
                    SELECT * FROM US_PATENT_GRANTS.cybersyn.uspto_patent_index
                    WHERE DOCUMENT_PUBLICATION_DATE >= '{start_date_str}' 
                      AND DOCUMENT_PUBLICATION_DATE < '{end_date_str}';
                """)


    batch_tasks = []
    for start_date, end_date in generate_date_ranges():
        load_patent_index_task = PythonOperator(
            task_id=f'load_patent_index_{start_date.year}_{end_date.year}',
            python_callable=load_patent_index_batch,
            op_kwargs={'start_date': start_date, 'end_date': end_date}
        )
        batch_tasks.append(load_patent_index_task)
    # Define task dependencies

    for batch_task in batch_tasks:
        create_staging_db >> load_contributor_index >> load_relationships >> batch_task

