# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
from typing import Dict, Sequence, Optional, Any
from logging import Logger
import argparse
import pprint
import sys
 
from pyspark.sql import SparkSession, DataFrame, DataFrameWriter
 
from dataproc_templates import BaseTemplate
import dataproc_templates.util.template_constants as constants

from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession

 
__all__ = ['CassandraToGCSTemplate']
 
 
class CassandraToGCSTemplate(BaseTemplate):
   """
   Dataproc template implementing exports from CASSANDRA to GCS
   """

   @staticmethod
   def parse_args(args: Optional[Sequence[str]] = None) -> Dict[str, Any]:
       parser: argparse.ArgumentParser = argparse.ArgumentParser()
 
       parser.add_argument(
           f'--{constants.CASSANDRA_TO_GCS_INPUT_KEYSPACE}',
           dest=constants.CASSANDRA_TO_GCS_INPUT_KEYSPACE,
           required=True,
           help='CASSANDRA GCS Input Keyspace'
       )
       parser.add_argument(
           f'--{constants.CASSANDRA_TO_GCS_INPUT_TABLE}',
           dest=constants.CASSANDRA_TO_GCS_INPUT_TABLE,
           required=True,
           help='CASSANDRA GCS Input Table'
       )
       parser.add_argument(
           f'--{constants.CASSANDRA_TO_GCS_INPUT_HOST}',
           dest=constants.CASSANDRA_TO_GCS_INPUT_HOST,
           required=True,
           help='CASSANDRA GCS Input Host'
       )
       parser.add_argument(
           f'--{constants.CASSANDRA_TO_GCS_OUTPUT_FORMAT}',
           dest=constants.CASSANDRA_TO_GCS_OUTPUT_FORMAT,
           required=True,
           help='Output file format (one of: avro,parquet,csv,json)',
           choices=[
               constants.FORMAT_AVRO,
               constants.FORMAT_PRQT,
               constants.FORMAT_CSV,
               constants.FORMAT_JSON
           ]
       )
       parser.add_argument(
           f'--{constants.CASSANDRA_TO_GCS_OUTPUT_PATH}',
           dest=constants.CASSANDRA_TO_GCS_OUTPUT_PATH,
           required=True,
           help='GCS location for output files'
       )
       parser.add_argument(
           f'--{constants.CASSANDRA_TO_GCS_OUTPUT_SAVEMODE}',
           dest=constants.CASSANDRA_TO_GCS_OUTPUT_SAVEMODE,
           required=False,
           default=constants.OUTPUT_MODE_APPEND,
           help=(
               'Output write mode '
               '(one of: append,overwrite,ignore,errorifexists) '
               '(Defaults to append)'
           ),
           choices=[
               constants.OUTPUT_MODE_OVERWRITE,
               constants.OUTPUT_MODE_APPEND,
               constants.OUTPUT_MODE_IGNORE,
               constants.OUTPUT_MODE_ERRORIFEXISTS
           ]
       )
 
       known_args: argparse.Namespace
       known_args, _ = parser.parse_known_args(args)
 
       return vars(known_args)
 
   def run(self, spark: SparkSession, args: Dict[str, Any]) -> None:
 
       logger: Logger = self.get_logger(spark=spark)
 
       # Arguments
       input_host: str = args[constants.CASSANDRA_TO_GCS_INPUT_HOST]
       input_keyspace: str = args[constants.CASSANDRA_TO_GCS_INPUT_KEYSPACE]
       input_table: str = args[constants.CASSANDRA_TO_GCS_INPUT_TABLE]
       output_format: str = args[constants.CASSANDRA_TO_GCS_OUTPUT_FORMAT]
       output_mode: str = args[constants.CASSANDRA_TO_GCS_OUTPUT_SAVEMODE]
       output_location: str = args[constants.CASSANDRA_TO_GCS_OUTPUT_PATH]
 
       logger.info(
           "Starting CASSANDRA to GCS spark job with parameters:\n"
           f"{pprint.pformat(args)}"
       )
 
       # Read
       options = {"keyspace": input_keyspace,
           "table": input_table,
           "spark.cassandra.connection.host": input_host}
       input_data = spark.read \
           .format("org.apache.spark.sql.cassandra") \
           .options(**options) \
           .load()

 
       # Write
       writer: DataFrameWriter = input_data.write.mode(output_mode)
 
       if output_format == constants.FORMAT_PRQT:
           writer.parquet(output_location)
       elif output_format == constants.FORMAT_AVRO:
           writer \
               .format(constants.FORMAT_AVRO) \
               .save(output_location)
       elif output_format == constants.FORMAT_CSV:
           writer \
               .option(constants.HEADER, True) \
               .csv(output_location)
       elif output_format == constants.FORMAT_JSON:
           writer.json(output_location)
