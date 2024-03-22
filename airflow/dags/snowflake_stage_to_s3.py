from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.amazon.aws.transfers.snowflake_to_s3 import SnowflakeToS3Operator
from airflow.utils.dates import days_ago

with DAG(
        dag_id='snowflake_stage_to_s3',
        schedule_interval='@daily',  # Adjust as needed
        start_date=days_ago(1),
        catchup=False
) as dag:

    # Tasks for each table
    upload_contributor_index = SnowflakeToS3Operator(
        task_id='upload_contributor_index',
        snowflake_conn_id='your_snowflake_conn',
        s3_bucket_name='your-s3-bucket',
        table='staging_db.cybersyn.uspto_contributor_index',
        stage='parquet_unload_stage',  # Assuming you have this stage
        file_format='PARQUET'
    )

    upload_relationships = SnowflakeToS3Operator(
        # ... similar task for 'uspto_patent_contributor_relationships' ...
    )

    upload_patent_index = SnowflakeToS3Operator(
        # ... similar task for 'uspto_patent_index' ...
    )

    # Task Dependencies (if needed)
    # Example:
    # upload_contributor_index >> upload_relationships >> upload_patent_index
