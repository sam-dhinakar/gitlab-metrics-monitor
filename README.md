# gitlab-metrics-monitor
Fetches All projects Commits and members list


🧾 GitLab Commit & Access Monitor – Script Summary
🔐 Authenticates with GitLab and InfluxDB:

Uses GitLab personal access token to access private GitLab API endpoints.

Connects to an InfluxDB instance using a token for secure data writing.

🔧 Configures Group and Project Settings:

Targets specific GitLab Group IDs ([4, 14]) to fetch project data.

Uses pagination to safely fetch all projects per group (per_page=100 and page-wise iteration).

📦 Fetches All Projects Within Groups:

For each group_id, it calls GitLab API /groups/:id/projects to list projects.

It paginates over all available pages to avoid missing projects in large groups.

🧑‍💻 Streamlit Web Interface:

Shows a Streamlit UI with a title and a button.

On clicking the button, it triggers fetching and data push operations.

📜 For Each Project:

Displays the project name and ID in the UI.

📥 Collects Latest Commits (last 5):

Calls /projects/:id/repository/commits (with per_page=5) to get recent commit data.

Extracts commit author_name and committed_date.

Converts date to proper format and writes it to InfluxDB using the gitlab_commits measurement.

👥 Collects Project Members (access info):

Calls /projects/:id/members/all to list all users with access.

Captures each member's username, name, and access_level.

Stores this info in InfluxDB using the gitlab_access measurement.

📤 Pushes All Data to InfluxDB:

Uses the influxdb_client Python package to write both commit and access data into InfluxDB, under:

Bucket: gitlab_metrics

Org: 

⏳ Rate Limiting with Delay:

Waits 10 seconds (time.sleep(10)) between group and project API calls to avoid rate-limiting or overwhelming the GitLab API.

✅ Gives Visual Feedback via Streamlit:

Shows success/failure messages for commits, members, and project fetches using st.info, st.success, and st.warning.
