from airflow.decorators import dag, task

import pendulum

import requests
import xmltodict
import os

from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.providers.sqlite.hooks.sqlite import SqliteHook

EPISODE_FOLDER = "episodes"


@dag(
    dag_id='podcast_summary2',
    schedule_interval="@daily",
    start_date=pendulum.datetime(2023, 9, 30),
    catchup=False,
)
def podcast_summary2():

    create_database = SqliteOperator(
        task_id='create_table_sqlite',
        sql=r"""
        CREATE TABLE IF NOT EXISTS episodes (
            link TEXT PRIMARY KEY,
            title TEXT,
            filename TEXT,
            published TEXT,
            description TEXT,
            transcript TEXT
        );
        """,
        sqlite_conn_id="podcasts"
    )

    @task()
    def get_episodes():
        data = requests.get(
            "https://www.marketplace.org/feed/podcast/marketplace/")
        feed = xmltodict.parse(data.text)
        episodes = feed["rss"]["channel"]["item"]
        print(f"Found {len(episodes)} episodes.")
        return episodes

    podcast_episodes = get_episodes()
    # Connect operator with task flow tasks
    # Airflow works on the return value
    create_database.set_downstream(podcast_episodes)

    @task()
    def load_episodes(episodes):
        hook = SqliteHook(sqlite_conn_id="podcasts")
        stored_episodes = hook.get_pandas_df("SELECT * from episodes;")
        new_episodes = []
        for episode in episodes:
            if episode["link"] not in stored_episodes["link"].values:
                filename = f"{episode['link'].split('/')[-1]}.mp3"
                new_episodes.append([episode["link"], episode["title"],
                                    episode["pubDate"], episode["description"], filename])
        hook.insert_rows(table='episodes', rows=new_episodes, target_fields=[
                         "link", "title", "published", "description", "filename"])
        return new_episodes  # Returning new episodes

    new_episodes = load_episodes(podcast_episodes)

    # Task to download new episodes
    @task()
    def download_episodes(episodes):
        audio_files = []
        for episode in episodes:
            name_end = episode["link"].split('/')[-1]
            filename = f"{name_end}.mp3"
            audio_path = os.path.join(EPISODE_FOLDER, filename)
            if not os.path.exists(audio_path):
                print(f"Downloading {filename}")
                audio = requests.get(episode["enclosure"]["@url"])
                with open(audio_path, "wb+") as f:
                    f.write(audio.content)
            audio_files.append({
                "link": episode["link"],
                "filename": filename
            })
        return audio_files  # Returning the audio files

    audio_files = download_episodes(podcast_episodes)


summary = podcast_summary2()
