import requests
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import streamlit as st
import datetime
import time

# ==============================
# Configuration
# ==============================

GITLAB_TOKEN = "Gitlab_token"
INFLUXDB_TOKEN = "influxdb_token"
INFLUX_URL = "http://localhost:8086"
ORG = "ORG_NAME"
BUCKET = "gitlab_metrics"

GITLAB_API_URL = "https://gitlab.com/api/v4"
GROUP_IDS = [4, 14]  # 🔁 Replace with your actual group IDs
DELAY_BETWEEN_CALLS = 10  # seconds (✅ increased from 1 to 10)

# ==============================
# Helper Functions
# ==============================

def get_projects_by_group(group_id):
    """Paginated fetch for all projects in a group"""
    all_projects = []
    page = 1
    while True:
        url = f"{GITLAB_API_URL}/groups/{group_id}/projects?per_page=100&page={page}"
        res = requests.get(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})
        if res.status_code != 200:
            break
        data = res.json()
        if not data:
            break
        all_projects.extend(data)
        page += 1
    return all_projects

# ==============================
# Streamlit UI
# ==============================

st.title("GitLab Project Commit & Access Monitor")

if st.button("Fetch and Push All Project Info"):
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}

    all_projects = []
    for gid in GROUP_IDS:
        st.info(f"🔎 Fetching projects from group ID: {gid}")
        group_projects = get_projects_by_group(gid)
        all_projects.extend(group_projects)
        time.sleep(DELAY_BETWEEN_CALLS)

    st.success(f"✅ Fetched {len(all_projects)} total projects across {len(GROUP_IDS)} groups")

    with InfluxDBClient(url=INFLUX_URL, token=INFLUXDB_TOKEN, org=ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)

        for project in all_projects:
            project_id = project['id']
            project_name = project['name']
            st.subheader(f"📁 Project: {project_name} (ID: {project_id})")

            # ----- Get limited commits -----
            commits_url = f"{GITLAB_API_URL}/projects/{project_id}/repository/commits?per_page=5"
            commits_response = requests.get(commits_url, headers=headers)

            if commits_response.status_code == 200:
                commits = commits_response.json()
                st.write(f"✅ Fetched {len(commits)} commits")

                for commit in commits:
                    user_name = commit.get("author_name")
                    committed_date = commit.get("committed_date")
                    try:
                        commit_time = datetime.datetime.fromisoformat(committed_date.replace("Z", "+00:00"))
                        point = (
                            Point("gitlab_commits")
                            .tag("user", user_name)
                            .tag("project", project_name)
                            .field("count", 1)
                            .time(commit_time)
                        )
                        write_api.write(bucket=BUCKET, org=ORG, record=point)
                    except Exception as e:
                        st.warning(f"⚠️ Error writing commit by {user_name}: {e}")
            else:
                st.warning(f"❌ Failed to fetch commits for project {project_name}")

            # ----- Get members -----
            members_url = f"{GITLAB_API_URL}/projects/{project_id}/members/all"
            members_response = requests.get(members_url, headers=headers)

            if members_response.status_code == 200:
                members = members_response.json()
                st.write(f"👥 Found {len(members)} members")

                for member in members:
                    username = member.get("username")
                    name = member.get("name")
                    access_level = member.get("access_level")
                    access_time = datetime.datetime.utcnow()

                    point = (
                        Point("gitlab_access")
                        .tag("project", project_name)
                        .tag("user", username)
                        .field("access_level", access_level)
                        .field("name", name)
                        .time(access_time)
                    )
                    write_api.write(bucket=BUCKET, org=ORG, record=point)
            else:
                st.warning(f"❌ Failed to fetch members for project {project_name}")

            time.sleep(DELAY_BETWEEN_CALLS)

    st.success("🎉 All commit and access data pushed to InfluxDB!")
