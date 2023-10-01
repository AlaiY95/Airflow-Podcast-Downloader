# Airflow-Podcast-Downloader

Q. Starting sqlite3:
sqlite3 episodes.db

Q. How to tell Airflow which database to Use?
airflow connections add 'podcasts' --conn-type 'sqlite' --conn-host 'path-to-db'

Q. How to check airflow database connection is configured correctly?
airflow connections get podcasts
