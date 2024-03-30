from contextlib import closing

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


