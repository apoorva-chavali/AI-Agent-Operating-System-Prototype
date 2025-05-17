import time
import threading
import requests
from messaging import RedisPubSub
import psutil, time

API_URL = "http://localhost:8000"
INPUT_CHANNEL = "analysis_results"
RESPONSE_CHANNEL = "workflow_events"

class WorkflowAgent:
    def __init__(self):
        self.agent_id = None
        self.ps = RedisPubSub()

    def register(self):
        resp = requests.post(
            f"{API_URL}/agents/",
            json={
                'name': 'workflow_agent',
                'metadata': {'role': 'automation-engine'}
            }
        )
        resp.raise_for_status()
        self.agent_id = resp.json()['id']
        print(f"[Agent {self.agent_id}] Registered with registry.")

    def send_heartbeat(self):
        while True:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            self.ps.publish("resource_metrics", {
                "agent_id": self.agent_id,
                "cpu_percent": cpu,
                "mem_percent": mem,
                "timestamp": time.time()
            })
            try:
                response = requests.post(f"{API_URL}/agents/{self.agent_id}/heartbeat")
                if response.status_code == 200:
                    print(f"[Agent {self.agent_id}] Heartbeat sent.")
                elif response.status_code == 404:
                    print(f"[Agent {self.agent_id}] Not found in registry. Re-registering...")
                    self.register()
            except Exception as e:
                print(f"[Agent {self.agent_id}] Heartbeat error: {e}")

            time.sleep(10)

    def listen_for_analysis(self):
        # def handle(msg):
        #     print(f"[Agent {self.agent_id}] Received analysis result: {msg}")
        #     result = msg.get("result")
        #     if result == "anomaly":
        #         # Simulate triggering an alert/workflow
        #         print(f"[Agent {self.agent_id}] Anomaly detected. Triggering workflow.")
        #         self.ps.publish(RESPONSE_CHANNEL, {
        #             'agent_id': self.agent_id,
        #             'action': 'triggered_remediation',
        #             'source_analysis': msg
        #         })
        #     else:
        #         print(f"[Agent {self.agent_id}] Normal result. No action taken.")
        def handle(msg):
            print(f"[Agent {self.agent_id}] Received analysis result: {msg}")
            result = msg.get("result")

            if result == "class_0":
                print(f"[Agent {self.agent_id}] Safe: class_0 detected. No action required.")

            elif result == "class_1":
                print(f"[Agent {self.agent_id}] Warning: class_1 detected. Sending alert.")
                # self.ps.publish(RESPONSE_CHANNEL, {
                #     'agent_id': self.agent_id,
                #     'action': 'send_alert',
                #     'source_analysis': msg,
                #     'message': 'class_1 detected warning alert issued.',
                #     "timestamp": msg.get("timestamp")
                # })
                self.ps.publish(RESPONSE_CHANNEL, {
                'agent_id': self.agent_id,
                'action': 'send_alert',
                'source_analysis': {
                    'input_id': msg.get("input_id"),
                    'timestamp': msg.get("timestamp")
                },
                'message': 'class_1 detected warning alert issued.',
                'timestamp': time.time()
            })


            elif result == "class_2":
                print(f"[Agent {self.agent_id}] Critical: class_2 detected. Triggering automation.")
                self.ps.publish(RESPONSE_CHANNEL, {
                    'agent_id': self.agent_id,
                    'action': 'trigger_external_system',
                    'source_analysis': {
                        'input_id': msg.get("input_id"),
                        'timestamp': msg.get("timestamp")
                    },
                    'message': 'class_2 detected – automation triggered.',
                    'timestamp': time.time()
                })


            else:
                print(f"[Agent {self.agent_id}] Unknown result type: {result}. No automation defined.")

                self.ps.subscribe(INPUT_CHANNEL, handle)
                print(f"[Agent {self.agent_id}] Listening on '{INPUT_CHANNEL}' for analysis results...")

    def run(self):
        self.register()

        threading.Thread(target=self.send_heartbeat, daemon=True).start()
        threading.Thread(target=self.listen_for_analysis, daemon=True).start()

        # Keep main thread alive
        while True:
            time.sleep(1)


if __name__ == '__main__':
    agent = WorkflowAgent()
    agent.run()
