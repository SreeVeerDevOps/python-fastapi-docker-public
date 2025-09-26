# Testing OpenTelemetry Using Aspire Dashbpard
- Create a Ubuntu 22.04 machine in AWS or Azure with 2CPU and 4GB memory.
- Perform apt update && apt install -y python3-pip jq net-tools 
- Install docker in it using https://get.docker.com | sudo bash
- Run a Aspire Dashboard with below command. https://aspiredashboard.com/
    docker run --rm -it \
    -p 18888:18888 -p 4317:18889 \
    -d --name aspire-dashboard \
    -e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS="true" \
    mcr.microsoft.com/dotnet/aspire-dashboard:9.1
  - Dashboard can be accessed with URL http://<machine-public-ip>:18888/
  - Perform git clone -b otel https://github.com/SreeVeerDevOps/python-fastapi-docker-public.git otel
  - cd otel && pip3 install -r requirements.txt
  - Run uvicorn main:app --host 0.0.0.0 --port 8002
  - Access the fastapi app with https://<machine-public-ip>:8002/docs
  - Execute the API's and the logs will be sent to Aspire Dashboard.
    <img width="1912" height="481" alt="image" src="https://github.com/user-attachments/assets/72cb588b-13c5-4cc7-87d4-907184d16f24" />
  - Click on the trace and following will show.
    <img width="1893" height="373" alt="image" src="https://github.com/user-attachments/assets/fe772124-f307-4b3e-b885-df11515c3ba8" />
    <img width="1898" height="900" alt="image" src="https://github.com/user-attachments/assets/73ebc385-9369-4bdb-8736-9ab6cfaa048b" />






## Bootstrap Code For Linux 
#!/bin/bash    
rm -rf fastapi    
git clone https://github.com/SreeVeerDevOps/python-fastapi-docker-public.git fastapi      
cd fastapi     
pip3 install -r requirements.txt    
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &      
