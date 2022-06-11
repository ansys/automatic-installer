from influxdb import InfluxDBClient
from sharepoint_uploader import downloader_backend

client = InfluxDBClient(host=downloader_backend.STATISTICS_SERVER, port=downloader_backend.STATISTICS_PORT)

db_list = client.get_list_database()
print(db_list)

db_to_clean = "crashes"
client.drop_database(db_to_clean)
client.create_database(db_to_clean)

db_list = client.get_list_database()
print(db_list)
