from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from uuid import uuid4

from messaging import RedisPubSub
pubsub = RedisPubSub()

class AgentInfo(BaseModel):
    id: str = None
    name: str
    status: str = "offline"
    metadata: dict = {}

app = FastAPI(title="AgentOS Registry & Lifecycle")

# In-memory store for registered agents
agents: Dict[str, AgentInfo] = {}

@app.post("/agents/", response_model=AgentInfo)
async def register_agent(info: AgentInfo):
    # register a new agent. Assigns a unique ID and marks it online.
    agent_id = str(uuid4())
    info.id = agent_id
    info.status = "online"
    agents[agent_id] = info


    pubsub.publish('agent_events', {
        'action': 'register',
        'id': agent_id,
        'name': info.name,
        'metadata': info.metadata
    })

    return info

@app.get("/agents/", response_model=List[AgentInfo])
async def list_agents():
    return list(agents.values())

@app.get("/agents/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents[agent_id]

@app.delete("/agents/{agent_id}")
async def deregister_agent(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    del agents[agent_id]
    return {"detail": "Agent deregistered"}

@app.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    agents[agent_id].status = "online"
    return {"detail": "Heartbeat received"}




# To run:
# uvicorn agent_os_core:app --reload --host 0.0.0.0 --port 8000

