# Portfolio Manager

## Live Server

An sandbox live server is hosted at https://india-portfolio-manager.herokuapp.com/. **Not optimized for mobile. Best viewed on Chrome browser.**

```diff
! Please be kind enough and not do any delete operations.
```

## Intent

To build a portfolio manager which can track and provide insights into a individual or family's financial interests.

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

## Getting started with Portfolio Manager

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

- Clone or download this docker source code.

``` bash
git clone -b docker-dev https://github.com/krishnakuruvadi/portfoliomanager.git
```

### Prepare the application to launch

- Change into the recently clone/downloaded directory.

``` bash
cd ./portfoliomanager
```

- Open the docker compose file to edit the application environment.

``` bash
nano ./dev-docker-compose.yml
```

- Edit the application environment as needed. Parameters that can be changed are:

  - container_name
  - DJANGO_SUPERUSER_USERNAME
  - DJANGO_SUPERUSER_PASSWORD
  - DJANGO_SUPERUSER_EMAIL
  - DJANGO_ENABLE_DEBUG (**Caution. This value should only be change to True or False**)
  - DB_NAME (**Caution. This value should match POSTGRES_DB**)
  - DB_USER (**Caution. This value should match POSTGRES_USER**)
  - DB_PASSWORD (**Caution. This value should match POSTGRES_PASSWORD**)
  - POSTGRES_DB
  - POSTGRES_PASSWORD
  - POSTGRES_USER

- **Save the file once you are done editing.**

### Launch Portfolio Manager

- Within the application folder (i.e. portfoliomanager), run the docker compose file to build the appliaction and launch the docker containers. This step should take approximately *two* minutes.

``` bash
docker compose -f dev-docker-compose.yml up -d
```

- To tear down the app environment, run:

``` bash
docker compose -f dev-docker-compose.yml down
```

### Browse to Portfolio Manager

- Open your favorite web browser and go to:
  
``` http
http://<docker-host-ip>/
```

- Enjoy Portfolio Manager
  
### Help us and support our work

- Please consider supporting us by contributing/reporting bugs or feeding our coffee addiction. **Click on the link below!**

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/kkuruvadi)

##### Disclaimers

- This software is in its pre-alpha stage.
