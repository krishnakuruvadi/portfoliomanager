# Portfolio Manager

## Live Server

An sandbox live server is hosted at https://india-portfolio-manager.herokuapp.com/. **Not optimized for mobile. Best viewed on Chrome browser.**

```diff
! Please be kind enough and not do any delete operations.
```

---

## Intent

To build a portfolio manager which can track and provide insights into a individual or family's financial interests.

---

## What is supported?

- Goals
- PPF (Public Provident Fund)
- EPF (Employee Provident Fund)
- Fixed Deposit
- ESPP (Employee Stock Purchase Plan)
- Users
- SSY (Sukanya Samridhi Yojana)
- RSU (Restricted Stock Units)
- Shares
- Mutual Funds
- Bank Accounts
- Gold
- 401K

---

## Getting started with Portfolio Manager

### Deployment methods

- Baremetal (Laptop/Desktop/Server) and Virtual Machine
  - [Install Walkthrough](#baremetal-and-virtual-machine-deployment-method)
- Docker
  - [Install Walkthrough](#docker-deployment-method)

---

## Baremetal and Virtual Machine Deployment Method

### 1. Requirements

- Python v3.8 or above.

- Libraries

  - macOS:

``` bash
brew install ghostscript tcl-tk
```
  - Ubuntu

``` bash
apt install ghostscript python3-tk
```

- Git v2.34.1 or above

  - [Official Git Installation Walkthrough](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

- Virtual Environment (optional)

  - Select and install your preferred virtual environment manager (anaconda, virtualenv, etc.)

### 2. Downloading the appliaction

- Clone or download the source code.

``` bash
git clone https://github.com/krishnakuruvadi/portfoliomanager.git
```

### Prepare the application to launch

- Change into the recently clone/downloaded directory.

``` bash
cd ./portfoliomanager
```

- Create a virtual environment (optional).

```bash
python -m venv ./venv
```

- Activate virtual environment.

```bash
source ./venv/bin/activate
```

- Install the required packages.

```
pip install -r requirements.txt
```

- Edit the environment variables to suite your needs.

  - Open the env_files directory and edit the .pm-env.sample file.
  - Carefully read the comments throughout the file as it will provide additional context.
  - Edit the parameters as necessary.

- Rename the environment variables file.

  - Remove .sample from the filename. Ensure the filename is .pm-env before proceeding to the next step.
    - **WARNING** - The application is expecting .pm-env as the filename. If you wish to change it please also modify ***env_file_path*** in ***setting.py***

- Delete unused environment variables file (optional)

  - Since the postgresql-env.sample file is only used with docker deployments, this file can be safely deleted before proceeding to the next step.

- Copy or move the entire env_files directory to the src directory. The directory should look as follows:

  - portfoliomanager
    - src
      - env_files
        - .pm-env OR .CUSTOM-FILE-NAME set above.

- Setup the server.

```bash
cd src
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

- Create a super user in django (optional).

```
python manage.py createsuperuser
```

  - You should be prompted to enter the desired username, email and password for this new admin.

- Download, extract, and copy the chromedriver to root of the project (portfoliomanager). You can obtain this driver from here: https://chromedriver.chromium.org/downloads. The directory should look as follows:

  - portfoliomanager
    - chromedriver

### Launch Portfolio Manager

- Start the server.

```
python manage.py runserver
```

- Start the huey process

  - In another terminal activate virtual environment (if you created one above) and run background tasks

```bash
source ./venv/bin/activate
cd src
python manage.py run_huey
```

### Browse to Portfolio Manager

- Open your favorite web browser and go to:
  
```
http://<host-ip>:8000/
```

OR 

```
http://localhost:8000/
```

- Enjoy Portfolio Manager

---

## Docker Deployment Method

### 1. Requirements

- Docker Engine & Docker Compose v20.10.17 or above.

  - Official Installation Walkthrough

    - [Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
    - [CentOS](https://docs.docker.com/engine/install/centos/)
    - [Fedora](https://docs.docker.com/engine/install/fedora/)
    - [RHEL](https://docs.docker.com/engine/install/rhel/)
    - [Windows](https://docs.docker.com/desktop/install/windows-install/)

- Git v2.34.1 or above

  - [Official Git Installation Walkthrough](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### 2. Downloading the appliaction

- Clone or download the source code.

``` bash
git clone https://github.com/krishnakuruvadi/portfoliomanager.git
```

### Prepare the application to launch

- Change into the recently clone/downloaded directory.

``` bash
cd ./portfoliomanager
```

- Edit the environment variables to suite your needs.

  - Open the env_files directory and edit both files (.pm-env.sample and postgresql-env.sample).
  - Carefully read the comments throughout the files as it will provide additional context.
  - Edit the parameters as necessary.

- Rename the environment variables files.

  - Remove .sample from the filenames. Ensure the filename is .pm-env and .postgresql-env before proceeding to the next step.
    - **WARNING** - The application container (pm-app) is expecting .pm-env as the filename. If you wish to change it please also modify ***env_file_path*** in ***setting.py***. 
    - **WARNING** - The database container (pm-db) is expecting postgresql-env as the filename. If you wish to change it please also modify ***./env_files/.postgresql-env*** in pm-db > env_file section of docker-compose.yml

### Launch Portfolio Manager

- Within the application folder (i.e. portfoliomanager), run the docker compose file to build the appliaction and launch the docker containers. This step should take approximately *two* minutes.

``` bash
docker compose up -d
```

### Browse to Portfolio Manager

- Open your favorite web browser and go to:
  
```
http://<docker-host-ip>/
```

- Enjoy Portfolio Manager
  
- To tear down the app environment, run:

``` bash
docker compose down
```

---
  
### Help us and support our work

- Please consider supporting us by contributing/reporting bugs or feeding our coffee addiction. **Click on the link below!**

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/kkuruvadi)

---

##### Disclaimers

##### This software is in its pre-alpha stage.
