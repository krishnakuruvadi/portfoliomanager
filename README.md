# Portfolio Manager
## Live Server
Example live server hosted at https://india-portfolio-manager.herokuapp.com/. Not optimized for mobile. Best viewed on Chrome browser.
```diff
! Please be kind enough and not do any delete operations
```

## Important Update
*master* branch is deprecated and *main* will be the actively developed branch from now on
  
*main* branch supports standalone (similar to *master* branch) runtime as well as docker compose based runtime

We recommend using the standalone runtime since there is no automatic way of migrating data to docker runtime.  All data will be lost and user has to re-enter all data if user goes ahead with docker based runtime.

Please follow these steps to move to *main* branch while retaining data from *master* branch and continue with standalone runtime.

```
git fetch origin
git checkout main
git pull --rebase origin main
pip install -r requirements.txt
cp -r env_files src
cd src/env_files
cp .pm-env.sample .pm-env
```
Edit the following fields in .pm-env using vi or your favorite editor
SECRET_KEY - generate a secret and replace the string 
DB_ENGINE - choose sqlite3 to get the data from existing db.  Leave the other fields unchanged

```
cd ..
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```
Clear browser cache

<img width="538" alt="Screen Shot 2022-08-26 at 10 17 01 AM" src="https://user-images.githubusercontent.com/26920497/186977087-7689d572-92c1-4f1d-9d21-1f0e1c8881d6.png">

Start the portfolio manager application and huey task queue and continue to access Portfolio Manager in your browser

## Intent

To build a portfolio manager which can track and provide insights into a individual or family's financial interests


## What is supported

* Goals
* PPF (Public Provident Fund)
* EPF (Employee Provident Fund)
* Fixed Deposit
* ESPP (Employee Stock Purchase Plan)
* Users
* SSY (Sukanya Samridhi Yojana)
* RSU (Restricted Stock Units)
* Shares
* Mutual Funds
* Bank Accounts
* Gold
* 401K


## How to start
For docker-compose based hosting check this branch: https://github.com/krishnakuruvadi/portfoliomanager/tree/docker-dev

For hosting on baremetal/VM/laptop, proceed with the below steps
* Install the following libraries

MacOS:
```
brew install ghostscript tcl-tk
```
Ubuntu
```
apt install ghostscript python3-tk
```
* Clone or download this source code
* Create a virtual environment
```
userid@host portfoliomanager % python3 -m venv ./venv
```
* Activate virtual environment
```
userid@host portfoliomanager %  source ./venv/bin/activate
```
* Install the following:
```
(venv) userid@host portfoliomanager % pip install -r requirements.txt
```
* Setup server
```
(venv) userid@host portfoliomanager % cd src
(venv) userid@host src % python manage.py makemigrations
(venv) userid@host src % python manage.py migrate
```
* Create super user (Reference: https://docs.djangoproject.com/en/2.2/intro/tutorial02/#creating-an-admin-user)
```
(venv) userid@host src % python manage.py createsuperuser
Username: admin
Email address: admin@example.com
Password: **********
Password (again): *********
Superuser created successfully.
(venv) userid@host src % 
```
* Start django server
```
(venv) userid@host src % python manage.py runserver
```
* Open homepage at http://127.0.0.1:8000/

* In another terminal activate virtual environment and run background tasks
```
userid@host portfoliomanager %  source ./venv/bin/activate
(venv) userid@host portfoliomanager % cd src
(venv) userid@host src % python manage.py run_huey
```
* Copy chrome driver to root of the project (portfoliomanager) from here: https://chromedriver.chromium.org/downloads


[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/kkuruvadi)
