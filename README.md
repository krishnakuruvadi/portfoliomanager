# Portfolio Manager
## Intent

To build a portfolio manager which can track and provide insights into a individual or family's financial interests


## What is supported

* Goals
* PPF (Public Provident Fund)
* EPF (Employee Provident Fund)
* Fixed Deposit
* ESPP (Employee Stock Purchase Plan)


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
(venv) userid@host portfoliomanager % pip install Django==2.1.5
(venv) userid@host portfoliomanager % pip install djangorestframework==3.11.0
(venv) userid@host portfoliomanager % pip install python-dateutil==2.8.1
(venv) userid@host portfoliomanager % pip install requests==2.23.0
```
* Start django server
```
(venv) userid@host src % python manage.py makemigrations
(venv) userid@host src % python manage.py migrate
(venv) userid@host src % python manage.py runserver
```
* Open homepage at http://127.0.0.1:8000/
