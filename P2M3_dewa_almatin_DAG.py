'''
=================================================
Milestone 3

Nama  : Dewa Dwi Al-matin
Batch : FTDS HCK-013

This program is designed to automate the process of transforming and loading data from PostgreSQL to Elasticsearch.
=================================================
'''

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from sqlalchemy import create_engine #koneksi ke postgres
import pandas as pd
from elasticsearch import Elasticsearch

def fetch_data():
    """
    Fetches data from a PostgreSQL database table named 'table_m3' and saves it to a CSV file.
    
    This function establishes a connection to the PostgreSQL database specified by the parameters:
    - database: Name of the database ('airflow_m3' by default)
    - username: Username for authentication ('airflow_m3' by default)
    - password: Password for authentication ('airflow_m3' by default)
    - host: Hostname or IP address of the database server ('postgres' by default)
    
    The data is fetched using SQLAlchemy engine and then read into a pandas DataFrame.
    The DataFrame is subsequently saved to a CSV file named 'P2M3_dewa_almatin_data_raw.csv' 
    in the directory '/opt/airflow/dags/'.
    
    Returns:
        None
    """

    # fetch data
    database = "airflow_m3"
    username = "airflow_m3"
    password = "airflow_m3"
    host = "postgres"

    # Membuat URL koneksi PostgreSQL
    postgres_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

    # Gunakan URL ini saat membuat koneksi SQLAlchemy
    engine = create_engine(postgres_url)
    conn = engine.connect()

    df = pd.read_sql_query("select * from table_m3", conn) #nama table sesuaikan sama nama table di postgres
    df.to_csv('/opt/airflow/dags/P2M3_dewa_almatin_data_raw.csv', sep=',', index=False)
    
def preprocessing(): 
    ''' 
    Function to clean data.

    This function reads the fetched CSV file.
    It then performs data cleaning operations which include:
    - Removing rows with missing values (NaNs) using dropna().
    - Removing duplicate rows using drop_duplicates().
    - Standardizing column names by converting them to lowercase, replacing spaces, 
      hyphens, and periods with underscores, and removing any non-alphanumeric characters.
    The cleaned DataFrame is then saved to a new CSV file named "P2M3_dewa_almatin_data_clean.csv" 
    in the directory '/opt/airflow/dags/'.

    Returns:
        None
    '''
    # pembisihan data
    data = pd.read_csv("/opt/airflow/dags/P2M3_dewa_almatin_data_raw.csv")

    # bersihkan data 
    data.dropna(inplace=True)
    data.drop_duplicates(inplace=True)

    cleaned_columns = []
    for column in data.columns:
        cleaned_column = column.lower().strip().replace(' ', '_').replace('-', '_').replace('.', '')
        cleaned_column = ''.join(e for e in cleaned_column if e.isalnum() or e == '_')
        cleaned_columns.append(cleaned_column)
    data.columns = cleaned_columns

    data['order_date'] = pd.to_datetime(data['order_date'])
    data['ship_date'] = pd.to_datetime(data['ship_date'])

    data.to_csv('/opt/airflow/dags/P2M3_dewa_almatin_data_clean.csv', index=False)
    
def upload_to_elasticsearch():
    '''
    Function to upload data to Elasticsearch.

    This function establishes a connection to Elasticsearch server located at "http://elasticsearch:9200".
    It reads data from the cleaned CSV file named "P2M3_dewa_almatin_data_clean.csv".
    The data is then uploaded to Elasticsearch index named "table_m3".
    
    Returns:
        None
    '''
    es = Elasticsearch("http://elasticsearch:9200", Timeout=240)
    df = pd.read_csv('/opt/airflow/dags/P2M3_dewa_almatin_data_clean.csv')
    
    for i, r in df.iterrows():
        doc = r.to_json()  # Convert the row to a dictionary
        res = es.index(index="table_m3", id=i+1, body=doc)
        print(f"Response from Elasticsearch: {res}")
        
        
default_args = {
    'owner': 'dewa_almatin', 
    'start_date': datetime(2024, 3, 20, 14, 20)
}

with DAG(
    "P2M3_dewa_almatin_DAG", #atur sesuai nama project kalian
    description='Milestone_3',
    schedule_interval='30 6 * * *', #atur schedule untuk menjalankan airflow pada 06:30.
    default_args=default_args, 
    catchup=False
) as dag:
    #task: 1
    fetch_data_pg = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_data) #
    
    # Task: 2
    '''  Fungsi ini ditujukan untuk menjalankan pembersihan data.'''
    clean_data = PythonOperator(
        task_id='clean_data',
        python_callable=preprocessing)

    # Task: 3
    upload_data = PythonOperator(
        task_id='upload_data',
        python_callable=upload_to_elasticsearch)

    #proses untuk menjalankan di airflow
    fetch_data_pg >> clean_data >> upload_data