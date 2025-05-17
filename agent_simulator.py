import time
import threading
import requests
from messaging import RedisPubSub

API_URL = "http://localhost:8000"
COMMAND_CHANNEL = "agent_commands"
EVENT_CHANNEL = "agent_events"

ps = RedisPubSub()

def register_agent():
    resp = requests.post(
        f"{API_URL}/agents/",
        json={
            'name': 'simulated_agent',
            'metadata': {'role': 'simulator'}
        }
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"[Agent {data['id']}] Registered with registry.")
    return data['id']


def listen_for_commands(agent_id: str):
    """
    Subscribe to COMMAND_CHANNEL and handle incoming commands.
    """
    def handle(msg):
        # Filter messages for this agent or broadcasts
        if msg.get('target_id') in (None, 'broadcast', agent_id):
            print(f"[Agent {agent_id}] Received command: {msg}")
            # Simulate doing work
            task = msg.get('task', 'unknown')
            time.sleep(2)
            # Publish completion event
            ps.publish(EVENT_CHANNEL, {
                'action': 'task_complete',
                'agent_id': agent_id,
                'task': task
            })
            print(f"[Agent {agent_id}] Completed task: {task}")

    ps.subscribe(COMMAND_CHANNEL, handle)
    print(f"[Agent {agent_id}] Listening for commands on '{COMMAND_CHANNEL}'...")


# def send_heartbeat(agent_id: str):
    """
    Periodically send heartbeat to the registry.
    """
    while True:
        # try:
        #     resp = requests.post(f"{API_URL}/agents/{agent_id}/heartbeat")
        #     resp.raise_for_status()
        #     print(f"[Agent {agent_id}] Heartbeat sent.")
        # except Exception as e:
        #     print(f"[Agent {agent_id}] Heartbeat error: {e}")
        # time.sleep(10)
        try:
            response = requests.post(f"{API_URL}/agents/{agent_id}/heartbeat")
            if response.status_code == 200:
                print(f"[Agent {agent_id}] Heartbeat sent.")
            else:
                print(f"[Agent {agent_id}] Heartbeat failed (status {response.status_code})")
        except Exception as e:
            print(f"[Agent {agent_id}] Heartbeat error: {e}")
        time.sleep(10)

def send_heartbeat(agent_id_ref: list):
    while True:
        try:
            response = requests.post(f"{API_URL}/agents/{agent_id_ref[0]}/heartbeat")
            if response.status_code == 200:
                print(f"[Agent {agent_id_ref[0]}] Heartbeat sent.")
            elif response.status_code == 404:
                print(f"[Agent {agent_id_ref[0]}] Not found. Re-registering...")
                agent_id_ref[0] = register_agent()
        except Exception as e:
            print(f"[Agent {agent_id_ref[0]}] Heartbeat error: {e}")
        time.sleep(10)



def main():
    def main():
        agent_id_ref = [register_agent()]  # Use list to allow mutable reference

        hb_thread = threading.Thread(target=send_heartbeat, args=(agent_id_ref,), daemon=True)
        hb_thread.start()

        listen_for_commands(agent_id_ref[0])

        while True:
            time.sleep(1)



if __name__ == '__main__':
    main()
