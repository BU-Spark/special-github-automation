# special-github-automation

### how to run locally

0. docker? `sudo docker compose up --build`
---

1. make sure you have node.js, npm, python3, pip, & pipenv installed
2. install the python dependencies 
- `$ pipenv shell`
- `$ pipenv install`
3. run the backend server
- `$ pipenv run python3 app/main.py`
4. install the node dependencies
- `$ cd frontend`
- `$ npm install`
5. run the frontend server
- `$ npm start`

### how to run own instance
easiest way to get this up an running is via railway
0. create an empty railway project
1. click the "Add a new service" button
2. choose the github repo "special-github-automation"
3. the initial deployment will fail, that is fine
4. this resource will be our **server**
- navigate to the environment variables tab, paste in all the required variables from the .env file
- Important: also add a PORT environment variable with the value **5000**
- navigate to the source section under settings, and change the build directory to "app"
- click the "Deploy" button
- generate a domain for this resource via the networking section (ensure port is 5000)
5. click the "Add a new service" button
6. choose the github repo "special-github-automation"
7. the initial deployment will fail, that is fine
8. this resource will be our **client**
- navigate to the environment variables tab, paste in all the required variables from the .env file
- Important: also add a PORT environment variable with the value **3000**
- navigate to the Source section under settings, and change the build directory to "client"
- click the "Deploy" button
- generate a domain for this resource via the networking section (ensure port is 3000)
9. you should now have a working instance of this project

