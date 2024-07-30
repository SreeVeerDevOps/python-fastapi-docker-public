#!/bin/bash
rm -rf fastapi
git clone https://github.com/SreeVeerDevOps/python-fastapi-docker-public.git fastapi
cd fastapi
pip3 install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
