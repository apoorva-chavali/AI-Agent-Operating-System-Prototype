# AI-Agent-Operating-System-Prototype
## Overview :
A modular agent operating system prototype is built that facilitates collaboration between specialized AI agents in an enterprise setting. It's main features include a central agent registry, inter-agent communication via Redis, and live performance monitoring via a dashboard. 

The system includes:
1. A **Data Analysis Agent** using a machine learning model for iris classification.
2. A **Workflow Automation Agent** that triggers alerts or actions based on predictions.
3. A central **FastAPI-based registry and lifecycle manager**.
4. A **real-time dashboard** for agent performance and metrics.

## Workflow : 

   ![Untitled Diagram drawio](https://github.com/user-attachments/assets/8557a59a-b071-41db-b752-6212aa7cd6b4)

## Deployment Instructions :

1. To deploy this project create a virtual environment and install all the mentioned packages using: 

pip install -r requirements.txt

2. You can either train the model using train.py (generates iris_model.pkl, used by the Data Analysis Agent) or use the provided .pkl file. 

3. You also need to start the redis server (https://github.com/tporadowski/redis/releases - downlaod the latest .zip and start the redis-server.exe)

4. Then to run the FastApi Registry use this command: 

uvicorn main:app --reload --host 0.0.0.0 --port 8000

5. Then to enable inter-agent communication run : python messaging.py

6. To register data analysis agent and worflow agents, open another terminal while the FastApi Registry terminal is active and run python data_analysis_agent.py and python worflow_agent.py

7. To access dashboard run : dashboard.py

8. Use the test script to send input to the Data Analysis Agent: python test.py







