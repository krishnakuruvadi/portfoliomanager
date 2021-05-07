# Portfolio Manager
## Live Server
Example live server hosted at https://india-portfolio-manager.herokuapp.com/. Not optimized for mobile. Best viewed on Chrome browser.
```diff
! Please be kind enough and not do any delete operations
```
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


## How to start
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
