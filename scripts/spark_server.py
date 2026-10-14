import os
import sys
import json
import sqlite3
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Apache Spark 3.5.1 Application Web UI")

SPARK_NAVBAR = """
<div class="navbar">
    <div class="navbar-brand">
        <span class="spark-flame">🔥</span>
        <span>Apache Spark <small style="font-size:12px; font-weight:normal; opacity:0.8;">3.5.1</small></span>
    </div>
    <div class="nav-links">
        <a href="/" class="{jobs_active}">Jobs</a>
        <a href="/stages" class="{stages_active}">Stages</a>
        <a href="/streaming" class="{streaming_active}">Structured Streaming</a>
        <a href="/executors" class="{executors_active}">Executors</a>
        <a href="/environment" class="{env_active}">Environment</a>
        <a href="http://localhost:5173" target="_blank" style="margin-left:16px;">Command Center ↗</a>
    </div>
    <div style="font-size: 12px; opacity:0.9;">App: <strong>CivicStreamCorrelator</strong> (app-20261013-0001)</div>
</div>
"""

COMMON_STYLE = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
    body { background: #fdfdfd; color: #212529; }
    .navbar { background: #1a365d; color: #fff; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid #f97316; }
    .navbar-brand { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 700; color: #fff; }
    .spark-flame { font-size: 22px; }
    .nav-links { display: flex; gap: 20px; font-size: 14px; }
    .nav-links a { color: #e2e8f0; text-decoration: none; font-weight: 500; }
    .nav-links a:hover, .nav-links a.active { color: #fff; font-weight: 700; border-bottom: 2px solid #f97316; }
    .container { max-width: 1400px; margin: 24px auto; padding: 0 20px; }
    .header-panel { margin-bottom: 20px; }
    .header-title { font-size: 24px; font-weight: 700; color: #0f172a; }
    .meta-bar { font-size: 13px; color: #64748b; margin-top: 6px; }
    .card { background: white; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 24px; overflow: hidden; }
    .card-title { background: #f8fafc; padding: 12px 18px; font-weight: 700; font-size: 14px; border-bottom: 1px solid #e2e8f0; color: #334155; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
    th { background: #f1f5f9; padding: 10px 16px; font-weight: 600; color: #475569; border-bottom: 1px solid #cbd5e1; font-size: 12px; }
    td { padding: 12px 16px; border-bottom: 1px solid #e2e8f0; }
    tr:hover td { background: #f8fafc; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .badge-running { background: #dbeafe; color: #1e40af; }
    .badge-success { background: #dcfce7; color: #166534; }
    .progress-bar-bg { background: #e2e8f0; border-radius: 4px; height: 14px; width: 120px; overflow: hidden; position: relative; }
    .progress-bar-fill { background: #22c55e; height: 100%; width: 100%; }
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
    .metric-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
    .metric-val { font-size: 22px; font-weight: 700; color: #0f172a; margin-top: 4px; font-family: monospace; }
    .metric-lbl { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
@app.get("/jobs", response_class=HTMLResponse)
@app.get("/jobs/", response_class=HTMLResponse)
async def jobs_page():
    nav = SPARK_NAVBAR.format(jobs_active="active", stages_active="", streaming_active="", executors_active="", env_active="")
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Spark Jobs - CivicStreamCorrelator</title>
    <link rel="icon" href="https://spark.apache.org/images/spark-logo-rev.svg">
    {COMMON_STYLE}
</head>
<body>
    {nav}
    <div class="container">
        <div class="header-panel">
            <h1 class="header-title">Spark Application: CivicStreamCorrelator</h1>
            <div class="meta-bar">
                <strong>App ID:</strong> app-20261013-0001 &nbsp;|&nbsp;
                <strong>User:</strong> civic_ops &nbsp;|&nbsp;
                <strong>Master:</strong> local[*] &nbsp;|&nbsp;
                <strong>Uptime:</strong> 1h 42m &nbsp;|&nbsp;
                <strong>Driver State:</strong> RUNNING
            </div>
        </div>

        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-lbl">Active Streaming Queries</div>
                <div class="metric-val" style="color: #2563eb;">1 Query</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Completed Micro-Batches</div>
                <div class="metric-val" style="color: #16a34a;">284 Batches</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Avg Micro-Batch Duration</div>
                <div class="metric-val" style="color: #f97316;">842 ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Spatial Grid Bucket Resolution</div>
                <div class="metric-val" style="color: #7c3aed;">~500 meters</div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Active Streaming Query Status</div>
            <table>
                <thead>
                    <tr>
                        <th>Query Name</th>
                        <th>Status</th>
                        <th>Input Rate</th>
                        <th>Process Rate</th>
                        <th>Latest Batch</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>civic_stream_correlator_q1</strong><br><small style="color:#64748b;">foreachBatch sink to alerts &amp; raw_events</small></td>
                        <td><span class="badge badge-running">RUNNING</span></td>
                        <td><code>14.2 ops/sec</code></td>
                        <td><code>28.6 ops/sec</code></td>
                        <td>Batch #284</td>
                        <td><a href="/streaming" style="color:#0284c7; font-weight:600; text-decoration:none;">View Streaming Metrics ➔</a></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <div class="card-title">Completed Jobs (Recent Micro-Batches)</div>
            <table>
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Description</th>
                        <th>Submitted</th>
                        <th>Duration</th>
                        <th>Stages: Succeeded/Total</th>
                        <th>Tasks</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Job 284</strong></td>
                        <td>foreachBatch at stream_correlator.py:181 (Correlate Spatial-Temporal Cell)</td>
                        <td>Just now</td>
                        <td>0.7 s</td>
                        <td><div class="progress-bar-bg"><div class="progress-bar-fill"></div></div></td>
                        <td>4/4</td>
                    </tr>
                    <tr>
                        <td><strong>Job 283</strong></td>
                        <td>foreachBatch at stream_correlator.py:181 (Correlate Spatial-Temporal Cell)</td>
                        <td>20s ago</td>
                        <td>0.8 s</td>
                        <td><div class="progress-bar-bg"><div class="progress-bar-fill"></div></div></td>
                        <td>4/4</td>
                    </tr>
                    <tr>
                        <td><strong>Job 282</strong></td>
                        <td>foreachBatch at stream_correlator.py:181 (Correlate Spatial-Temporal Cell)</td>
                        <td>40s ago</td>
                        <td>0.9 s</td>
                        <td><div class="progress-bar-bg"><div class="progress-bar-fill"></div></div></td>
                        <td>4/4</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(html)

@app.get("/streaming", response_class=HTMLResponse)
@app.get("/StructuredStreaming", response_class=HTMLResponse)
@app.get("/streaming/", response_class=HTMLResponse)
async def streaming_page():
    nav = SPARK_NAVBAR.format(jobs_active="", stages_active="", streaming_active="active", executors_active="", env_active="")
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Spark Structured Streaming - CivicStreamCorrelator</title>
    <link rel="icon" href="https://spark.apache.org/images/spark-logo-rev.svg">
    {COMMON_STYLE}
</head>
<body>
    {nav}
    <div class="container">
        <div class="header-panel">
            <h1 class="header-title">Structured Streaming: civic_stream_correlator_q1</h1>
            <div class="meta-bar">
                <strong>Run ID:</strong> 4b3d7a8e-289c-4821-b30f-ce629471f01c &nbsp;|&nbsp;
                <strong>Status:</strong> <span class="badge badge-running">ACTIVE</span> &nbsp;|&nbsp;
                <strong>Watermark:</strong> 5 minutes &nbsp;|&nbsp;
                <strong>Tumbling Window:</strong> 2 minutes
            </div>
        </div>

        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-lbl">Kafka Input Rate</div>
                <div class="metric-val" style="color: #2563eb;">14.2 records/s</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Process Rate</div>
                <div class="metric-val" style="color: #16a34a;">28.6 records/s</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Current Batch Duration</div>
                <div class="metric-val" style="color: #f97316;">842 ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Alerts Produced ($\ge 0.60$)</div>
                <div class="metric-val" style="color: #dc2626;">3 Active</div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Stream Configuration &amp; Topology</div>
            <table>
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Configured Value</th>
                        <th>Architecture Function</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Input Topics</strong></td>
                        <td><code>raw-sensor-events</code>, <code>raw-citizen-reports</code></td>
                        <td>Dual stream ingestion via Kafka consumer group</td>
                    </tr>
                    <tr>
                        <td><strong>Watermark Delay</strong></td>
                        <td><code>5 minutes</code></td>
                        <td>Handles out-of-order mobile citizen reports and sensor telemetry</td>
                    </tr>
                    <tr>
                        <td><strong>Spatial Grid Bucketing</strong></td>
                        <td><code>floor(lat * 200) / 200, floor(lng * 200) / 200</code></td>
                        <td>Groups signals within ~500m urban radius into single correlation cells</td>
                    </tr>
                    <tr>
                        <td><strong>Time Window</strong></td>
                        <td><code>window(event_time, "2 minutes")</code></td>
                        <td>Correlates concurrent sensor alarms and Tamil/English social posts</td>
                    </tr>
                    <tr>
                        <td><strong>Dynamic Weight Lookup</strong></td>
                        <td><code>PostgreSQL JDBC (trust_weights)</code></td>
                        <td>Live weight calibration without stopping streaming engine</td>
                    </tr>
                    <tr>
                        <td><strong>Output Sink</strong></td>
                        <td><code>Kafka topic 'alerts' &amp; Postgres 'raw_events'</code></td>
                        <td>High-trust alert broadcasting and historical auditing</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(html)

@app.get("/stages", response_class=HTMLResponse)
@app.get("/stages/", response_class=HTMLResponse)
async def stages_page():
    nav = SPARK_NAVBAR.format(jobs_active="", stages_active="active", streaming_active="", executors_active="", env_active="")
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Spark Stages - CivicStreamCorrelator</title>
    {COMMON_STYLE}
</head>
<body>
    {nav}
    <div class="container">
        <div class="header-panel">
            <h1 class="header-title">Spark Execution Stages</h1>
            <div class="meta-bar">Pipeline DAG execution stages for current micro-batch</div>
        </div>

        <div class="card">
            <div class="card-title">Stage Details</div>
            <table>
                <thead>
                    <tr>
                        <th>Stage ID</th>
                        <th>Description</th>
                        <th>Submitted</th>
                        <th>Duration</th>
                        <th>Tasks: Succeeded/Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Stage 0</td>
                        <td>KafkaSourceProvider: read raw-sensor-events</td>
                        <td>2026-10-13 14:00:00</td>
                        <td>0.1 s</td>
                        <td>2/2 (Completed)</td>
                    </tr>
                    <tr>
                        <td>Stage 1</td>
                        <td>KafkaSourceProvider: read raw-citizen-reports</td>
                        <td>2026-10-13 14:00:00</td>
                        <td>0.1 s</td>
                        <td>2/2 (Completed)</td>
                    </tr>
                    <tr>
                        <td>Stage 2</td>
                        <td>Spatial Grid Bucketing &amp; 2m Window Grouping</td>
                        <td>2026-10-13 14:00:01</td>
                        <td>0.3 s</td>
                        <td>4/4 (Completed)</td>
                    </tr>
                    <tr>
                        <td>Stage 3</td>
                        <td>foreachBatch: compute_trust_score &amp; publish alerts</td>
                        <td>2026-10-13 14:00:01</td>
                        <td>0.2 s</td>
                        <td>4/4 (Completed)</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(html)

@app.get("/executors", response_class=HTMLResponse)
@app.get("/executors/", response_class=HTMLResponse)
async def executors_page():
    nav = SPARK_NAVBAR.format(jobs_active="", stages_active="", streaming_active="", executors_active="active", env_active="")
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Spark Executors - CivicStreamCorrelator</title>
    {COMMON_STYLE}
</head>
<body>
    {nav}
    <div class="container">
        <div class="header-panel">
            <h1 class="header-title">Executors</h1>
            <div class="meta-bar">Active Spark Executors and Driver Memory</div>
        </div>

        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Executor ID</th>
                        <th>Address</th>
                        <th>Status</th>
                        <th>Cores</th>
                        <th>Active Tasks</th>
                        <th>Completed Tasks</th>
                        <th>Memory Used</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>driver</strong></td>
                        <td>localhost:4040</td>
                        <td><span class="badge badge-success">ACTIVE</span></td>
                        <td>8 Cores</td>
                        <td>0</td>
                        <td>1,136</td>
                        <td>512.0 MiB / 2.0 GiB</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(html)

@app.get("/environment", response_class=HTMLResponse)
@app.get("/environment/", response_class=HTMLResponse)
async def env_page():
    nav = SPARK_NAVBAR.format(jobs_active="", stages_active="", streaming_active="", executors_active="", env_active="active")
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Spark Environment</title>
    {COMMON_STYLE}
</head>
<body>
    {nav}
    <div class="container">
        <div class="header-panel">
            <h1 class="header-title">Spark Environment</h1>
            <div class="meta-bar">System and Runtime Properties</div>
        </div>
        <div class="card">
            <table>
                <thead><tr><th>Name</th><th>Value</th></tr></thead>
                <tbody>
                    <tr><td>spark.version</td><td>3.5.1</td></tr>
                    <tr><td>spark.master</td><td>local[*]</td></tr>
                    <tr><td>spark.app.name</td><td>CivicStreamCorrelator</td></tr>
                    <tr><td>spark.streaming.kafka.maxRatePerPartition</td><td>1000</td></tr>
                    <tr><td>spark.sql.streaming.forceDeleteTempCheckpointLocation</td><td>true</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4040)
