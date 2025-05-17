
from flask import Flask, render_template, jsonify
import requests
import threading
import time
import redis
import json

app = Flask(__name__)

FASTAPI_URL = "http://localhost:8000"
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# In-memory stores
analysis_events = []
workflow_events = []
resource_metrics = []
resource_usage = {}


# Redis client for Pub/Sub
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
ps = db.pubsub()

# Thread to collect events from Redis channels
def event_listener():
    ps.subscribe('analysis_results', 'workflow_events', 'resource_metrics')
    for message in ps.listen():
        if message['type'] != 'message':
            continue
        channel = message['channel']
        try:
            data = json.loads(message['data'])
        except json.JSONDecodeError:
            continue
        # preserve agent-provided timestamp; set only if missing
        data.setdefault('timestamp', time.time())
        # Store events
        if channel == 'analysis_results':
            analysis_events.append(data)
        elif channel == 'workflow_events':
            workflow_events.append(data)
        elif channel == 'resource_metrics':
            resource_usage[data['agent_id']] = {
            'cpu_percent': data['cpu_percent'],
            'mem_percent': data['mem_percent']
        }

# Start listener thread
t = threading.Thread(target=event_listener, daemon=True)
t.start()

@app.route('/')
def index():
    agents = requests.get(f"{FASTAPI_URL}/agents/").json()
    return render_template('index.html', agents=agents)

@app.route('/data')
def data():
    # Compute accuracy if ground-truth labels are present
    total = sum(1 for e in analysis_events if 'label' in e)
    correct = sum(1 for e in analysis_events if 'label' in e and e['label'] == e.get('result'))
    accuracy = (correct / total) * 100 if total > 0 else None

    # Compile latest resource metrics per agent
    latest_resources = {}
    for m in resource_metrics:
        aid = m.get('agent_id')
        latest_resources[aid] = {
            'cpu_percent': m.get('cpu_percent'),
            'memory_percent': m.get('memory_percent'),
            'timestamp': m.get('timestamp')
        }

    # Compute average latency between analysis and workflow
    latencies = []
    for we in workflow_events:
        sid = we.get('source_analysis', {}).get('input_id')
        match = next((ae for ae in analysis_events if ae.get('input_id') == sid), None)
        if match:
            latencies.append(we['timestamp'] - match['timestamp'])
    avg_latency = sum(latencies) / len(latencies) if latencies else None


    correct = sum(1 for ae in analysis_events
                  if ae.get('ground_truth') and ae['ground_truth'] == ae['result'])
    total   = sum(1 for ae in analysis_events if ae.get('ground_truth'))
    accuracy = (correct/total*100) if total else None
    return jsonify({
        'agents': requests.get(f"{FASTAPI_URL}/agents/").json(),
        'analysis_events': analysis_events,
        'workflow_events': workflow_events,
        'resource_metrics': resource_usage,
        'accuracy': accuracy,
        'avg_latency': avg_latency
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
