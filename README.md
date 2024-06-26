# Patent Analytics Pipeline

## About the Project

The Patent Analytics Pipeline is a comprehensive data engineering solution designed to ingest, process, and analyze US Patent Grants data. Utilizing a batch processing approach, this project aims to uncover trends and insights within the realm of US patents, facilitating a deeper understanding of technological innovations, sector growth, and temporal patterns in patent filings. Through the integration of technologies such as AWS, Terraform, Airflow, Apache Spark, and Snowflake, alongside visualization tools like Metabase, this pipeline offers a robust platform for data-driven decision-making and strategic planning.

### Project Overview

#### Problem Statement

In an era where innovation is a key driver for economic growth and competitive advantage, understanding the landscape of technological advancements through patents becomes crucial for businesses, researchers, and policymakers. The US Patent Grants dataset represents a rich source of information on technological innovations, offering insights into the direction of research and development across various sectors. However, the vast amount of data, combined with its complexity and the dynamic nature of patent filings, poses significant challenges in extracting actionable insights.

The patent-analytics-pipeline project aims to address several specific questions to navigate through these challenges and unlock the value contained within the US Patent Grants data:

1. **What are the current trends in patent filings?** Identifying trends over time can help in understanding which technology sectors are experiencing growth and are likely to dominate the innovation landscape.

2. **How are patent filings distributed across different technology sectors?** This question seeks to uncover the sectors that are most active in innovation, providing insights into where research and development efforts are concentrated.

3. **What is the pace of innovation within key technology sectors?** By examining the volume and growth of patent filings within specific sectors, the project aims to measure the pace of innovation and identify areas with accelerated technological advancements.

4. **Are there emerging technologies that are gaining traction in recent patent filings?** Identifying technologies that are beginning to see increased activity in patent filings can highlight emerging trends and potential areas for investment or research.

5. **How do patent filings correlate with industry trends and market demands?** This question explores the relationship between patent activity and broader industry trends, helping to validate whether patent filings are a leading indicator of market demands.

6. **What geographic regions are leading in innovation, based on patent filings?** If geographic data is available, analyzing the distribution of patents by region can provide insights into global innovation hubs and regional strengths in certain technology sectors.

7. **Can predictive analytics be applied to forecast future trends in patent filings?** By leveraging historical data, the project aims to explore the potential for predictive modeling to forecast future trends in patent filings, aiding strategic planning and decision-making.

This pipeline also supports competitive analysis by extracting insights from patent data. It aims to answer questions like:

- Which technology areas are experiencing the most growth in patent activity?
- Are there cyclical patterns or seasonal shifts in patent filings?
- Which companies or inventors are driving innovation in specific fields?
- How does my company's patent portfolio compare to key competitors in terms of size and technology focus?
- Are there emerging players within our industry who are rapidly increasing their patent output?
- Can patent filings reveal potential new entrants or disruptors within our market?

The pipeline also enables an in-depth analysis of a specific technology area using patent data. It can help answer questions like:

- What are the key milestones and seminal patents within the field of Quantum Computing?
- Who are the top patent holders and influential inventors in Renewable Energy Technologies?
- Are there signs of maturity or potential disruption within Biotechnology and CRISPR based on patent trends?

By answering these questions, the patent-analytics-pipeline project intends to provide a comprehensive overview of the innovation landscape as reflected in patent filings, offering valuable insights for businesses, researchers, and policymakers to make informed decisions and strategize accordingly.

## Project Workflow

### 1. Data Ingestion

- **Source**: The dataset is available at Snowflake, with updates every Tuesday.
- **Batch Processing Approach**: Given the update frequency, we set up a weekly batch ingestion pipeline to fetch new data.

### 2. Cloud Platform: AWS

- **S3 Bucket**: We use AWS S3 as the primary data lake to store raw patent data. S3 is scalable, durable, and secure, making it ideal for storing large datasets.
- **IAM Roles and Policies**: We ensure that appropriate IAM roles and policies are in place for secure access to AWS resources.

### 3. Infrastructure as Code: Terraform

- **Resource Management**: We define the AWS infrastructure with Terraform, including S3 buckets, AWS Glue Data Catalog, AWS Lambda functions, and Amazon EMR clusters. This approach facilitates reproducibility, scalability, and version control of your cloud infrastructure.

### 4. Workflow Orchestration: Airflow

- **DAGs for Batch Jobs**: We create Directed Acyclic Graphs (DAGs) in Airflow to manage the workflow of our batch jobs. This includes tasks for data ingestion, processing, and loading into the data warehouse.
- **Scheduling**: We schedule the DAG to run weekly, in alignment with the dataset update frequency.

### 5. Data Processing and Analysis

- **AWS Glue**: We use AWS Glue for ETL (extract, transform, load) jobs. We define Glue crawlers to catalog the data in S3 and prepare it for analysis.
- **Apache Spark on Amazon EMR**: For data processing and transformation, we leverage Apache Spark running on Amazon EMR. Spark's distributed computing capability is well-suited for processing large datasets efficiently.
- **Data Warehouse (Snowflake)**: We load the processed data into Snowflake for further analysis and querying. Snowflake's scalability and performance make it an excellent choice for data analytics workloads.

### 6. Dashboard Visualization: Metabase

- **Metabase Setup**: We set up Metabase on an AWS EC2 instance. We then connect Metabase to the Snowflake data warehouse.
- **Visualization**:
  - **Categorical Data Distribution Graph**: We create a dashboard in Metabase to display the distribution of patents across different technology sectors.
  - **Temporal Distribution Graph**: We design a time series chart in Metabase to show the number of patents filed over time, possibly segmented by technology sector.

## Getting Started

### Prerequisites

- AWS account
- Terraform installed on your machine
- Access to Snowflake
- Airflow setup (locally or on a server)
- Metabase setup (locally or on a server)

### Installation

1. **Clone the repository**

   ```sh
   git clone https://github.com/chrisdamba/patent-analytics-pipeline.git

   ```

2. **Deployment**
   - Clone this repository.
   - Set up your AWS environment. Configure your AWS CLI with aws configure. Ensure you have the necessary permissions for S3, Glue, Lambda, and EMR.
   - Change directory to `/infra`
   - Add the required terraform env variables, for example my local env variables :

   ```
   export TF_VAR_region='us-east-1'
   export TF_VAR_account_id='<your aws account ID>'
   export TF_VAR_environment_name='dev'
   export TF_VAR_my_ip='<your machine IP address>'
   export TF_VAR_public_key_path='~/.ssh/patentkey.pub' 
   export TF_VAR_raw_patent_data_bucket_name='<s3 bucket name for raw patent data>' 
   export TF_VAR_mwaa_source_bucket_name='<s3 bucket name for mwaa dags>'
   export TF_VAR_mwaa_source_bucket_arn='arn:aws:s3:::<s3 bucket name for mwaa dags>'
   export TF_VAR_vpc_cidr='10.16.0.0/16'
   export TF_VAR_private_subnet_cidrs='["10.16.1.0/24","10.16.2.0/24"]'
   export TF_VAR_public_subnet_cidrs='["10.16.3.0/24","10.16.4.0/24"]'
   export TF_VAR_source_bucket_arn=""

   ```
   - Run `terraform init`
   - Run `terraform apply`
3. **Data Exploration in Snowflake**
   - TODO: Brief guide for users on how to explore the dataset in Snowflake.



### Configuration
- **Airflow DAGs**: Configure your DAGs in Airflow for scheduling and orchestrating your ETL jobs.
- **Spark Jobs**: Customize your Spark jobs according to the data processing requirements.
- **Metabase Dashboards**: Set up your dashboards in Metabase for data visualization.

**Dashboard**

- The dashboard will be available at [https://mopinion.com/business-intelligence-bi-tools-overview/](https://mopinion.com/business-intelligence-bi-tools-overview/) [placeholder]
- Sample visualizations include:
  - Distribution of patents across technology categories
  - Patent filing trends over time

**Customization**

**Project Status**

## Usage
After completing the setup, you can run the pipeline by triggering the Airflow DAGs. This will initiate the process of data ingestion, processing, and loading into Snowflake, where it can be analyzed and visualized through Metabase.

## License
Distributed under the MIT License. See `LICENSE` for more information.
