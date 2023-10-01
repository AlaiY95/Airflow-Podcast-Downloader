from airflow.decorators import dag, task

import pendulum

import requests
import xmltodict


@dag(
    dag_id='podcast_summary2',
    schedule_interval="@daily",
    start_date=pendulum.datetime(2023, 9, 30),
    catchup=False,
)
def podcast_summary2():

    @task()
    def get_episodes():
        data = requests.get(
            "https://www.marketplace.org/feed/podcast/marketplace/")
        feed = xmltodict.parse(data.text)
        episodes = feed["rss"]["channel"]["item"]
        print(f"Found {len(episodes)} episodes.")
        return episodes

    podcast_episodes = get_episodes()


summary = podcast_summary2()
