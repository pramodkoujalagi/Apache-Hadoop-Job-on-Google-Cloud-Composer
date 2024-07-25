import datetime
import os

from airflow import models
from airflow.contrib.operators import dataproc_operator
from airflow.utils import trigger_rule

input_file = models.Variable.get('input_file')
output_dir = models.Variable.get('output_dir')
WORDCOUNT_JAR = ('file:///usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar')
wordcount_args=['wordcount', input_file, output_dir]

yesterday=datetime.datetime.combine(
    datetime.datetime.today() - datetime.timedelta(1),
    datetime.datetime.min.time())

default_dag_args={
    'start_date': yesterday,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': datetime.timedelta(minutes=5),
    'project_id': models.Variable.get('gcp_project')
}

with models.DAG(
        'airflow_wordcount',
        schedule_interval=datetime.timedelta(days=1),
        default_args=default_dag_args) as dag:

    create_dataproc_cluster=dataproc_operator.DataprocClusterCreateOperator(
        task_id='create_dataproc_cluster',
        cluster_name='composer-hadoop-tutorial-cluster-{{ ds_nodash }}',
        num_workers=2,
        zone=models.Variable.get('gcp_zone'),
        master_machine_type='n1-standard-1',
        worker_machine_type='n1-standard-1')

    run_dataproc_hadoop=dataproc_operator.DataProcHadoopOperator(
        task_id='run_dataproc_hadoop',
        main_jar=WORDCOUNT_JAR,
        cluster_name='composer-hadoop-tutorial-cluster-{{ ds_nodash }}',
        arguments=wordcount_args)

    delete_dataproc_cluster=dataproc_operator.DataprocClusterDeleteOperator(
        task_id='delete_dataproc_cluster',
        cluster_name='composer-hadoop-tutorial-cluster-{{ ds_nodash }}',
        trigger_rule=trigger_rule.TriggerRule.ALL_DONE)

    create_dataproc_cluster >> run_dataproc_hadoop >> delete_dataproc_cluster
