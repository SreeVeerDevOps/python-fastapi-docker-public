#!/bin/bash
rm -rf fastapi
git clone https://github.com/SreeVeerDevOps/python-fastapi-docker-public.git fastapi
cd fastapi
pip3 install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &

Deploying To Azure App Service:
1. Clone https://github.com/SreeVeerDevOps/python-fastapi-docker-public.git to local.
2. Deploy new azure appservice with Python 3.10 platform.
3. Once deployed go to Configuration -> Startup Command and give as below
   uvicorn main:app --host 0.0.0.0
4. Go to Deployment Center and configure Local Git which will give a Git repo to push.
   You can also change the DEPLOYMENT_BRANCH app setting in the Azure portal, by selecting Configuration under Settings
   and adding a new Application Setting with a name of DEPLOYMENT_BRANCH and value of main.
6. Run following commands:
   git remote add origin <localgit URL>
   git push origin master

   This will deploy the app to the AppService.
   Access to URL for homepage. Refer to screeenshots.
