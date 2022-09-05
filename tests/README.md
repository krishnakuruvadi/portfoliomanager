# How to run tests

## Setup
Tests create their own db and so any existing db with user data is not affected.

- Activate virtual environment.

```bash
source ./venv/bin/activate
```

- Install the required packages.

```bash
pip install -r test-requirements.txt
```

- Copy environment files to src directory if no environment is already present
```bash
cp -r env_files src
```

- Backup existing environment, if any
```bash
cd src/env_files
mv .pm-env .pm-env-backup
```

- Set test environment
```bash
mv .pm-env-test .pm-env
```

- Download, extract, and copy the chromedriver to root of the project (portfoliomanager), if not already done. You can obtain this driver from here: https://chromedriver.chromium.org/downloads. The directory should look as follows:

  - portfoliomanager
    - chromedriver

- Run tests
```bash
cd ../..
pytest
```

- Revert to old environment
```bash
cd src/env_files
mv .pm-env .pm-env-test
mv .pm-env-backup .pm-env
```