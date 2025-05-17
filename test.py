from messaging import RedisPubSub
import time

ps = RedisPubSub()
ps.publish("data_ready", {
  "data": {
    "sepal_length": 6.0,
    "sepal_width": 2.9,
    "petal_length": 4.5,
    "petal_width": 1.5
  },
  "ground_truth": "class_1"  
})


ps.publish("workflow_events", {
    "agent_id": "workflow_sim",
    "action": "manual_trigger",
    "timestamp": time.time(),
    "source_analysis": {
        "input_id": "test123",
        "timestamp": time.time() - 2  # Simulate that analysis was 2 seconds ago
    }
})
