# Requirements

- PostgreSQL 12.x: https://www.postgresql.org/download/
- Python 3.8.1: https://www.python.org/ftp/python/3.8.1/python-3.8.1.exe
- (Optional) PyCharm Professional (recommended, but community version is okay as well): https://www.jetbrains.com/pycharm/download

# Initial Setup

## Database

- Proceed with the installation of PostgreSQL. When asked for username and password, make sure the username is **postgres** and password is **abc123**.

- Search for **pgAdmin** in your computer and open it, this will redirect you to a browser page. When prompted for username and password, use the one set up in the previous step.

- Under the "Browser" column on the left side, click on **Servers** -> **PostgreSQL 12** -> Right click on **Databases** -> Select **Create** -> **Database**. In the **Name** row, write **Esteem**, and make sure that the "owner" is **postgres**, then click on save.

- Once the database is created, right click on it and select **Restore**. In the file name, select the **Esteem_DB** file found in the root directory of the repository.

## Installing required plugins

- PyCharm Professional is recommended as it supports and helps with the development of Django-based websites. After cloning the repository, open that folder as project in PyCharm and in the terminal, write **pip install -r requirements.txt**.

- Once completed, run the command **py manage.py makemigrations** (**py manage.py makemigrations _APPNAME_** if the first one doesn't work) and then **py manage.py migrate**.

- To start the server, write **py manage.py runserver** in terminal.
