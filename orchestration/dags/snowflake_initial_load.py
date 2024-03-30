from contextlib import closing
from datetime import datetime, timedelta

import awswrangler as wr
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from airflow import DAG
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
from airflow.operators.python_operator import PythonOperator
from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.utils.dates import days_ago


def execute_snowflake(sql, snowflake_conn_id, with_cursor=False):
    """Execute snowflake query."""
    hook_connection = SnowflakeHook(
        snowflake_conn_id=snowflake_conn_id
    )

    with closing(hook_connection.get_conn()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(sql)
            res = cur.fetchall()
            if with_cursor:
                return res, cur
            else:
                return res


def upload_file_from_snowflake_to_s3_with_hook(query, file_name, bucket=Variable('BUCKET_NAME')):
    """Convert snowflake list to df."""
    result, cursor = execute_snowflake(query, 'snowflake_default', True)
    headers = list(map(lambda t: t[0], cursor.description))
    df = pd.DataFrame(result)
    df.columns = headers

    # save file before to send
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, file_name, row_group_size=100)
    # Send to S3

    hook = AwsBaseHook(aws_conn_id="s3_default")
    wr.s3.to_parquet(
        df=df,
        path=f"s3://{bucket}/{file_name}",
        boto3_session=hook.get_session()
    )


def generate_date_ranges(start_year=1976, interval=5):
    start_date = datetime(start_year, 1, 1).date()  # Corrected to datetime().date()
    end_date = datetime.now().date()

    while start_date <= end_date:
        next_end_date = start_date + timedelta(days=365 * interval - 1)
        yield start_date, min(next_end_date, end_date)  # Handle last interval
        start_date = next_end_date + timedelta(days=1)


with DAG(
    dag_id='snowflake_initial_load',
    description='One time data load pipeline for US Patent Grants data from Snowflake to S3',
    schedule_interval='@once',  # Run once for the initial import
    start_date=days_ago(1),  # Specify a start date in the past
    catchup=False
) as dag:
    create_staging_db = SnowflakeOperator(
        task_id='create_staging_db',
        snowflake_conn_id='snowflake_default',
        sql="""
            CREATE OR REPLACE DATABASE staging_db;
            
            USE DATABASE staging_db;
            CREATE SCHEMA IF NOT EXISTS cybersyn;

            USE SCHEMA cybersyn;
            
            CREATE TABLE IF NOT EXISTS staging_db.cybersyn.metadata (
                table_name VARCHAR(255),
                last_load_date DATE
            );
            
            INSERT INTO staging_db.cybersyn.metadata (table_name, last_load_date)
                VALUES ('uspto_patent_index', '1976-01-01');
        """
    )

    create_snowflake_s3_storage_integration = SnowflakeOperator(
        task_id='create_snowflake_s3_storage_integration',
        snowflake_conn_id='snowflake_default',
        sql=f"""
            CREATE OR REPLACE STORAGE INTEGRATION s3_int
                TYPE = EXTERNAL_STAGE
                STORAGE_PROVIDER = S3
                ENABLED = TRUE
                STORAGE_AWS_ROLE_ARN = '{Variable('IAM_EXECUTION_ROLE_ARN')}'
                STORAGE_ALLOWED_LOCATIONS = ('s3://{Variable('BUCKET_NAME')}/');
            """
    )

    create_snowflake_stage = SnowflakeOperator(
        task_id='create_snowflake_stage',
        snowflake_conn_id='snowflake_default',
        sql=f"""
            USE DATABASE staging_db;
            CREATE OR REPLACE ROLE data_transfer_role;
            CREATE SCHEMA IF NOT EXISTS stages;

            GRANT USAGE ON SCHEMA staging_db.stages TO ROLE data_transfer_role;
            GRANT CREATE STAGE ON SCHEMA staging_db.stages TO ROLE data_transfer_role;

            USE SCHEMA cybersyn;

            CREATE OR REPLACE FILE FORMAT parquet_unload_file_format
                TYPE = 'PARQUET'
                SNAPPY_COMPRESSION = TRUE
                COMMENT = 'FILE FORMAT FOR UNLOADING AS PARQUET FILES';

            CREATE OR REPLACE STAGE parquet_unload_stage
                URL = 's3://{Variable('BUCKET_NAME')}/'
                STORAGE_INTEGRATION = s3_int
                FILE_FORMAT = parquet_unload_file_format
                COMMENT = 'Stage for the Snowflake external Parquet export';
        """
    )

    extract_contributor_index = SnowflakeOperator(
        task_id='extract_contributor_index',
        snowflake_conn_id='snowflake_default',
        sql="""
            CREATE OR REPLACE TABLE staging_db.cybersyn.uspto_contributor_index AS
            SELECT * FROM US_PATENT_GRANTS.cybersyn.uspto_contributor_index;
        """
    )

    extract_relationships = SnowflakeOperator(
        task_id='extract_patent_contributor_relationships',
        snowflake_conn_id='snowflake_default',
        sql="""
            CREATE OR REPLACE TABLE staging_db.cybersyn.uspto_patent_contributor_relationships AS
            SELECT * FROM US_PATENT_GRANTS.cybersyn.uspto_patent_contributor_relationships;
        """
    )

    upload_contributor_index_task = PythonOperator(
        task_id=f'upload_uspto_contributor_index_to_s3',
        python_callable=upload_file_from_snowflake_to_s3_with_hook,
        op_kwargs={
            "query": 'SELECT * FROM staging_db.cybersyn.uspto_contributor_index',
            "file_name": 'uspto_contributor_index.parquet'
        },
    )

    upload_patent_contributor_relationships_task = PythonOperator(
        task_id=f'upload_uspto_patent_contributor_relationships_to_s3',
        python_callable=upload_file_from_snowflake_to_s3_with_hook,
        op_kwargs={
            "query": 'SELECT * FROM staging_db.cybersyn.uspto_patent_contributor_relationships',
            "file_name": 'uspto_patent_contributor_relationships.parquet'
        },
    )

    update_last_load_date = SnowflakeOperator(
        task_id='update_last_load_date',
        snowflake_conn_id='snowflake_default',
        sql="""
            UPDATE staging_db.cybersyn.metadata
            SET last_load_date = CURRENT_DATE
            WHERE table_name = 'uspto_patent_index';
        """
    )

    def load_patent_index_batch(**kwargs):
        with closing(SnowflakeHook(snowflake_conn_id='snowflake_default').get_conn()) as conn:
            with conn.cursor() as cur:
                start_date_str = kwargs['start_date'].strftime('%Y-%m-%d')  # Convert to string
                end_date_str = kwargs['end_date'].strftime('%Y-%m-%d')
                cur.execute(f"""
                    CREATE OR REPLACE TABLE staging_db.cybersyn.uspto_patent_index_{kwargs['start_date'].year}_{kwargs['end_date'].year} AS 
                    SELECT * FROM US_PATENT_GRANTS.cybersyn.uspto_patent_index
                    WHERE DOCUMENT_PUBLICATION_DATE >= '{start_date_str}' 
                      AND DOCUMENT_PUBLICATION_DATE < '{end_date_str}';
                """)


    with TaskGroup(group_id='warehouse_prep_tasks_group') as warehouse_prep_task:
        t1 = EmptyOperator(task_id='create_staging_db')
        t2 = EmptyOperator(task_id='create_snowflake_s3_storage_integration')
        t3 = EmptyOperator(task_id='create_snowflake_stage')

        t1 >> t2 >> t3

    with TaskGroup(group_id='extract_staging_tasks_group') as extract_staging_task:
        t1 = EmptyOperator(task_id='extract_contributor_index')
        t2 = EmptyOperator(task_id='extract_patent_contributor_relationships')

        batch_tasks = []
        for start_date, end_date in generate_date_ranges():
            task_id = f'load_patent_index_{start_date.year}_{end_date.year}'
            load_patent_index_task = PythonOperator(
                task_id=task_id,
                python_callable=load_patent_index_batch,
                op_kwargs={'start_date': start_date, 'end_date': end_date}
            )
            batch_tasks.append(load_patent_index_task)  # Append the correct task here

        for batch_task in batch_tasks:
            t1 >> t2 >> batch_task  # This establishes dependencies correctly

    batch_tasks = []
    for start_date, end_date in generate_date_ranges():
        start = start_date.strftime('%Y-%m-%d')
        end = end_date.strftime('%Y-%m-%d')
        file_name = f'uspto_patent_index_{start_date.year}_{end_date.year}.parquet'
        query = f"""
            SELECT * FROM staging_db.cybersyn.uspto_patent_index_{start_date.year}_{end_date.year};
        """
        upload_to_s3_patent_index_batch_task = PythonOperator(
            task_id=f'upload_patent_index_{start_date.year}_{end_date.year}_to_s3',
            python_callable=upload_file_from_snowflake_to_s3_with_hook,
            op_kwargs={
                "query": query,
                "file_name": file_name,
            },
        )
        batch_tasks.append(upload_to_s3_patent_index_batch_task)
    # Define task dependencies

    for upload_patent_index_batch_task in batch_tasks:
        warehouse_prep_task >> extract_staging_task >> update_last_load_date
