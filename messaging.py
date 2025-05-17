import redis
import threading
import json
from typing import Callable


class RedisPubSub:

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.pubsub = self.redis.pubsub()

    def publish(self, channel: str, message: dict) -> None:
        payload = json.dumps(message)
        self.redis.publish(channel, payload)

    def subscribe(self, channel: str, callback: Callable[[dict], None]) -> None:
        def _listener():
            self.pubsub.subscribe(channel)
            for item in self.pubsub.listen():
                if item['type'] == 'message':
                    try:
                        data = json.loads(item['data'])
                        callback(data)
                    except json.JSONDecodeError:
                        # Handle invalid JSON
                        print(f"Received non-JSON message on {channel}: {item['data']}")
        # Start listener thread
        thread = threading.Thread(target=_listener, daemon=True)
        thread.start()


if __name__ == '__main__':
    import time

    def handle(msg):
        print(f"[Subscriber] Got message: {msg}")

    ps = RedisPubSub()
    # Subscribe to a test channel
    ps.subscribe('agent_events', handle)

    # Publish a test message
    ps.publish('agent_events', {'from': 'agent1', 'event': 'registered', 'id': '1234'})

    while True:
        time.sleep(1)

