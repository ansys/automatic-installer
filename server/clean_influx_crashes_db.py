import os
import sys

from influxdb import InfluxDBClient

root_folder = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)

from downloader_backend import STATISTICS_SERVER, STATISTICS_PORT


client = InfluxDBClient(host=STATISTICS_SERVER, port=STATISTICS_PORT)

db_list = client.get_list_database()
print(db_list)

db_to_clean = "crashes"
client.drop_database(db_to_clean)
client.create_database(db_to_clean)

db_list = client.get_list_database()
print(db_list)
