# Portfolio Manager

## Other hosting options

~~If you or someone you know is unable to self host this application but would greatly benefit from it, checkout us out at [lukritive.com](https://lukritive.com), our hosted site (with a 1 year trial for a limited time)!~~
We have stopped the service due to lack of demand

---

## Be part of the community!

Feel free to join our [Discord](https://discord.gg/YknWEN6GAw).  Let us know your feedback - what do you like? what needs improvement? what features would you like to see added?

If you want to contribute to the repo and need help, you can reach us on discord as well.

---

## Intent

To build a portfolio manager which can track and provide insights into a individual or family's financial interests.

---

## What is supported?

- Users
- Goals

- Fixed Deposit
- ESPP (Employee Stock Purchase Plan)
- RSU (Restricted Stock Units)
- Shares
- Crypto
- Bank Accounts

INDIA:
- PPF (Public Provident Fund)
- EPF (Employee Provident Fund)
- SSY (Sukanya Samridhi Yojana)
- Mutual Funds
- Gold

USA:
- 401K

---

## Installation

- Baremetal (Laptop/Desktop/Server) and Virtual Machine
  - [Install Walkthrough](#baremetal-and-virtual-machine-deployment-method)
- Docker
  - [Install Walkthrough](#docker-deployment-method)

---

## Upgrades

- Baremetal (Laptop/Desktop/Server) and Virtual Machine
  - [Upgrade Walkthrough](#baremetal-and-virtual-machine-upgrade-steps)
- Docker
  - [Upgrade Walkthrough](#docker-upgrade-steps)

---

## Baremetal and Virtual Machine Deployment Method

### 1. Requirements

- Python v3.  Tested with v3.9, v3.10

- Libraries

  - macOS:

```bash
brew update
brew upgrade
brew install ghostscript tcl-tk
brew cleanup
```
  - Ubuntu

```bash
apt install ghostscript python3-tk
```

- Git v2.34.1 or above

  - [Official Git Installation Walkthrough](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

- Virtual Environment (optional)

  - Select and install your preferred virtual environment manager (anaconda, virtualenv, etc.)

### 2. Downloading the application

- Clone or download the source code.

```bash
git clone https://github.com/krishnakuruvadi/portfoliomanager.git
```

### Prepare the application to launch

- Change into the recently clone/downloaded directory.

```bash
cd ./portfoliomanager
```

- Set git configuration (optional).
```bash
git config user.name "Your Name"
git config user.email "youremail@provider.com"
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

```bash
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

- Create a normal user in django (recommended). Edit the fields below with your desired account details. For more details, please visit [Django's documentation](https://docs.djangoproject.com/en/4.1/topics/auth/default/#creating-users)

  - It is recommended to use a non-admin account for your daily use and only use an admin account for administrative purposes.

```bash
cd src
python manage.py shell
from django.contrib.auth.models import User
User.objects.create_user('johndoe', 'johndoe@gmail.com', 'johnpassword')
```

- Create a super user in django (optional).

```bash
python manage.py createsuperuser
```

  - You should be prompted to enter the desired username, email and password for this new admin.

  - You can create additional normal users by logging in as the superuser and going to: Internals > Admin > Authentication and Authorization > Users > Add User.

- Download, extract, and copy the chromedriver to root of the project (portfoliomanager). You can obtain this driver from here: https://chromedriver.chromium.org/downloads. The directory should look as follows:

  - portfoliomanager
    - chromedriver

### Launch PortfolioManager

- Start the server.

```bash
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
Note: Different charts and data gets updated at different fixed schedules.  If you want to manually update these, go to "Internals" and then "Tasks" and queue the tasks to run once

- **Enjoy Portfolio Manager!**

### Optional Features

#### Summary Emails

- Create a new [MailJet account](https://app.mailjet.com/signup?lang=en_US) and sign up for their free tier.
- Go to "Internals" then "Preferences" and provide the details to setup the integration.

---

## Baremetal and Virtual Machine Upgrade Steps

- Stop the server

``` bash
cd ./portfoliomanager/src
CTRL + C
deactivate
```

- Download the new app version and install any new packages

```bash
cd ./portfoliomanager
git pull
source ./venv/bin/activate
pip install -r requirements.txt
```

- Re-launch PortfolioManager

  - [Follow these steps](#launch-portfoliomanager)

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

```bash
git clone https://github.com/krishnakuruvadi/portfoliomanager.git
```

### Prepare the application to launch

- Change into the recently clone/downloaded directory.

```bash
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

```bash
docker compose up -d
```

- Should you need to tear down the app environment, run:

```bash
docker compose down
```

- Create a normal user in django (recommended). 

  - It is recommended to use a non-admin account for your daily use and only use an admin account for administrative purposes.

  - Edit the fields below with your desired account details. For more details, please visit [Django's documentation](https://docs.djangoproject.com/en/4.1/topics/auth/default/#creating-users)

  - Your Docker container name may vary. Please adjust the below commads to match your exact setup. In this example, I assume your docker container name running the PorfolioManager app is portfolio-manager-app.

```bash
docker ps
docker exec -it portfolio-manager-app bash
python manage.py shell
from django.contrib.auth.models import User
User.objects.create_user('johndoe', 'johndoe@gmail.com', 'johnpassword')
exit()
```

  - You can create additional normal users by logging in as the superuser and going to: Internals > Admin > Authentication and Authorization > Users > Add User.

### Browse to Portfolio Manager

- Open your favorite web browser and go to:
  
```
http://<docker-host-ip>/
```

OR 

```
http://localhost/
```
Note: Different charts and data gets updated at different fixed schedules.  If you want to manually update these, go to "Internals" and then "Tasks" and queue the tasks to run once

- **Enjoy Portfolio Manager!**
  
### Optional Features

#### Summary Emails

- Create a new [MailJet account](https://app.mailjet.com/signup?lang=en_US) and sign up for their free tier.
- Go to "Internals" then "Preferences" and provide the details to setup the integration.

---

## Docker Upgrade Steps

- Stop the containers

``` bash
cd ./portfoliomanager
docker compose down
```

- Download the new app version

```bash
git pull
```

- Build a new docker image with the updated application version

```bash
docker compose build --no-cache
```

- Restart the containers

```bash
docker compose up -d
```

- Delete the old images (optional but recommended)

```bash
docker image prune
```

---

## Help us and support our work

- Please consider supporting us by contributing/reporting bugs or feeding our coffee addiction. **Click on the link below!**

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/kkuruvadi)

---

