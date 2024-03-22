from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.amazon.aws.transfers.snowflake_to_s3 import SnowflakeToS3Operator
from airflow.utils.dates import days_ago

with DAG(
        dag_id='snowflake_stage_to_s3',
        description='DAG to upload Snowflake tables to S3 as Parquet files',
        schedule_interval='@daily',  # Adjust as needed
        start_date=days_ago(1),
        catchup=False
) as dag:

    # Tasks for each table
    upload_contributor_index = SnowflakeToS3Operator(
        task_id='upload_contributor_index',
        snowflake_conn_id='snowflake_default',
        s3_bucket_name='patent-analytics-data-bucket',
        table='staging_db.cybersyn.uspto_contributor_index',
        stage='parquet_unload_stage',
        file_format='PARQUET'
    )

    upload_relationships = SnowflakeToS3Operator(
        task_id='upload_contributor_index',
        snowflake_conn_id='snowflake_default',
        s3_bucket_name='patent-analytics-data-bucket',
        table='staging_db.cybersyn.uspto_patent_contributor_relationships',
        stage='parquet_unload_stage',
        file_format='PARQUET'
    )

    upload_patent_index = SnowflakeToS3Operator(
        task_id='upload_contributor_index',
        snowflake_conn_id='snowflake_default',
        s3_bucket_name='patent-analytics-data-bucket',
        table='staging_db.cybersyn.uspto_patent_index',
        stage='parquet_unload_stage',
        file_format='PARQUET'
    )

    upload_contributor_index >> upload_relationships >> upload_patent_index
