# Python FastAPI Application For Testing Azure AppService

## Bootstrap Code For Linux 
#!/bin/bash    
rm -rf fastapi    
git clone https://github.com/SreeVeerDevOps/python-fastapi-docker-public.git fastapi      
cd fastapi     
pip3 install -r requirements.txt    
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &      

## Deploying To Azure App Services:
## Deploying To Azure App Services:
1. Create branch azb48-appsvc-dev  and Download zip https://github.com/SreeVeerDevOps/python-fastapi-docker-public.git to local.   

2. Deploy new azure appservice with Python 3.10 platform.  

3. Once deployed go to Configuration -> Startup Command and give as below  
   uvicorn main:app --host 0.0.0.0   

4. Go to Deployment -> Deployment Slot -> Create Dev Slot. 
   Click on Dev Slot to go in to it for further configuration. This is needed as we test our app in the Dev Env first. 

5. Settings -> Environment variables -> App Settings -> Add 
   DEPLOYMENT_BRANCH = Dev and Select Deployment slot setting and save. 
   Also give AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

6.  Open powershell from the fastapi code and perform following comamnds: 
    git init; git add.; git commmit -m "BaseCode"; git branch; git checkout -b dev 

7. Go to Deployment Center and configure Local Git which will give a Git repo to push. 
   By default the app will take master as default branch. We can change that by using App Setting  
   DEPLOYMENT_BRANCH.   
   Create two branches for two slots. Dev Branch and Prod Branch for Prod Slot.  
   For Dev Slot DEPLOYMENT_BRANCH=Dev  
   For Prod Slot DEPLOYMENT_BRANCH=Prod   

   You can also change the DEPLOYMENT_BRANCH app setting in the Azure portal, by selecting Configuration under Settings 
   and adding a new Application Setting with a name of DEPLOYMENT_BRANCH and value of main.  

8. Run following commands: 
   git remote add origin <localgit URL> 
   git push origin Dev  - For Dev Slot 
   git push origin Prod - For Prod Slot 

   This will deploy the app to the AppService.  
   Access to URL for homepage. Refer to screeenshots.. 

https://azb45fastapi-dev.scm.azurewebsites.net/ - OLD    
https://azb45fastapi-dev.scm.azurewebsites.net/newui/ - NEW 


Sometimes it takes few minitues to get the app up and running.