import time
import threading
import requests
from messaging import RedisPubSub
import random
import joblib
from messaging import RedisPubSub
import uuid, time, psutil

API_URL = "http://localhost:8000"
INPUT_CHANNEL = "data_ready"
RESULT_CHANNEL = "analysis_results"
MODEL_UPDATE_CHANNEL = "model_updates"

class IrisModel:
    def __init__(self, model_path="iris_model.pkl"):
        self.model = joblib.load(model_path)

    def predict(self, data):
        try:
            X = [[
                data["sepal_length"],
                data["sepal_width"],
                data["petal_length"],
                data["petal_width"]
            ]]
            pred = self.model.predict(X)[0]
            return f"class_{pred}"
        except Exception as e:
            return f"error: {str(e)}"


class DataAnalysisAgent:
    def __init__(self):
        self.agent_id = None
        self.model = IrisModel()
        self.ps = RedisPubSub()

    def register(self):
        resp = requests.post(
            f"{API_URL}/agents/",
            json={
                'name': 'data_analysis_agent',
                'metadata': {'role': 'iris-prediction'}
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

    def listen_for_data(self):
        def handle(msg):
            print(f"[Agent {self.agent_id}] Received data: {msg}")
            result = self.model.predict(msg.get("data", {}))
            print(f"[Agent {self.agent_id}] Prediction result: {result}")
            # self.ps.publish(RESULT_CHANNEL, {
            #     'agent_id': self.agent_id,
            #     'input': msg,
            #     'result': result,
            #     "timestamp": time.time()
            # })
            import uuid

            input_id = str(uuid.uuid4())
            data     = msg.get("data", {})
            label    = msg.get("ground_truth")        # ← grab it
            result   = self.model.predict(data)
            ts       = time.time()  

            self.ps.publish(RESULT_CHANNEL, {
                'agent_id': self.agent_id,
                'input_id': input_id, 
                'input': msg,
                'result': result,
                "ground_truth": label,
                'timestamp': time.time()
            })


        self.ps.subscribe(INPUT_CHANNEL, handle)
        print(f"[Agent {self.agent_id}] Listening on '{INPUT_CHANNEL}' for data...")

    def listen_for_model_updates(self):
        def handle(update):
            print(f"[Agent {self.agent_id}] Model update received: {update}")
            model_path = update.get("model_path", "iris_model.pkl")
            try:
                self.model = IrisModel(model_path)
                print(f"[Agent {self.agent_id}] Model successfully reloaded from {model_path}.")
            except Exception as e:
                print(f"[Agent {self.agent_id}] Failed to reload model: {e}")

        self.ps.subscribe(MODEL_UPDATE_CHANNEL, handle)
        print(f"[Agent {self.agent_id}] Listening for model updates...")



    def run(self):
        self.register()

        threading.Thread(target=self.send_heartbeat, daemon=True).start()
        threading.Thread(target=self.listen_for_model_updates, daemon=True).start()

        threading.Thread(target=self.listen_for_data, daemon=True).start()

        while True:
            time.sleep(1)



if __name__ == '__main__':
    agent = DataAnalysisAgent()
    

    ps = RedisPubSub()
    agent.run()
