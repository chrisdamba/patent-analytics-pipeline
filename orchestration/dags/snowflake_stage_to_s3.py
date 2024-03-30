from datetime import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.utils.dates import days_ago

import awswrangler as wr
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook
from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook


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


def upload_file_from_snowflake_to_s3_with_hook(query, file_name, bucket):
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


with DAG(
        dag_id='snowflake_stage_to_s3',
        description='DAG to upload Snowflake tables to S3 as Parquet files',
        schedule_interval='0 0 * * 2',  # At 00:00 on Tuesday
        start_date=days_ago(1),
        catchup=False
) as dag:

    create_temp_table = SnowflakeOperator(
        task_id='create_temp_table',
        snowflake_conn_id='snowflake_default',
        sql="""
            CREATE OR REPLACE TRANSIENT TABLE staging_db.cybersyn.uspto_patent_index_incremental AS
            SELECT * FROM staging_db.cybersyn.uspto_patent_index
            WHERE DOCUMENT_PUBLICATION_DATE > (
                SELECT MAX(last_load_date) FROM staging_db.cybersyn.metadata WHERE table_name = 'uspto_patent_index'
            );
        """,
        dag=dag,
    )
    #
    # # Tasks for each table
    # upload_contributor_index = SnowflakeToS3Operator(
    #     task_id='upload_contributor_index',
    #     snowflake_conn_id='snowflake_default',
    #     s3_conn_id='s3_default',
    #     s3_bucket='patent-analytics-data-bucket',
    #     s3_key='uspto_contributor_index/',
    #     table='staging_db.cybersyn.uspto_contributor_index',
    #     stage='parquet_unload_stage',
    #     file_format='PARQUET'
    # )
    #
    # upload_relationships = SnowflakeToS3Operator(
    #     task_id='upload_patent_contributor_relationships',
    #     snowflake_conn_id='snowflake_default',
    #     s3_conn_id='s3_default',
    #     s3_bucket='patent-analytics-data-bucket',
    #     s3_key='uspto_patent_contributor_relationships/',
    #     table='staging_db.cybersyn.uspto_patent_contributor_relationships',
    #     stage='parquet_unload_stage',
    #     file_format='PARQUET'
    # )
    #
    # upload_patent_index = SnowflakeToS3Operator(
    #     task_id='upload_patent_index',
    #     snowflake_conn_id='snowflake_default',
    #     s3_conn_id='s3_default',
    #     s3_bucket='patent-analytics-data-bucket',
    #     s3_key='uspto_patent_index/',
    #     table='staging_db.cybersyn.uspto_patent_index',
    #     stage='parquet_unload_stage',
    #     file_format='PARQUET'
    # )

    # upload_patent_index_incremental = SnowflakeToS3Operator(
    #     task_id='upload_patent_index_incremental',
    #     snowflake_conn_id='snowflake_default',
    #     s3_conn_id='s3_default',
    #     s3_bucket='patent-analytics-data-bucket',
    #     s3_key='uspto_patent_index/incremental/',
    #     table='staging_db.cybersyn.uspto_patent_index_incremental',
    #     stage='parquet_unload_stage',
    #     file_format='PARQUET'
    # )
    query = """SELECT * FROM staging_db.cybersyn.uspto_patent_index_incremental;"""
    upload_patent_index_incremental = PythonOperator(
        task_id='upload_patent_index_incremental_to_s3',
        python_callable=upload_file_from_snowflake_to_s3_with_hook,
        op_kwargs={
            "query": query,
            "file_name": f"incremental/uspto_patent_index_{datetime.now().strftime('%Y%m%d')}.parquet",
            "bucket": 'patent-analytics-data-bucket'
        },
    )

    create_temp_table >> upload_patent_index_incremental
