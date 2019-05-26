# kap-bot
Python based Telegram bot that feeds you information on Kaplan Singapore classes. Because the classes at the Kaplan campus are not fixed, there is a need for students to check the location of the class manually before each lesson (The Kaplan 360 app also does not currently deliver push notifications of class information).  

This bot aims to remove that process by sending a user a Telegram message with the details of a class they have signed up for without having them manually check.

## Getting Started
These instructions will get you a copy of the Kaplan Schedule Bot up and running on your local machine.

### Prerequisites
kap-bot is a Python based Telegram bot that stores information in an SQL database. While you are free to use the bot with any version of Python 3 and a relational SQL based DBMS, the bot was developed using the following components and versions.

Components:
```
MariaDB 10.1.38
Python 3.6
```

Python Modules:
```
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
[configparser](https://pypi.org/project/configparser/)
[mysql-connector](https://pypi.org/project/mysql-connector/)
```

### Initial Configuration
In order to get your instance of the bot running, you need to populate the config file with more information about your database connection as well as Telegram bot API key.

To do this, make a copy of `config-sample.ini` as `config.ini`. To learn more about the Telegram Bot API, visit the Telegram Bot API [documentation page](https://core.telegram.org/bots/api).

Additional information include the Telegram account that will act as an Admin. If you do not have an Admin or do not know your Telegram ID, set this value as 0.

### Launching The Bot
After filling `config.ini`, the bot can be launced normally by running `kapbot.py`.

```
python3 kapbot.py
```

#### As a Background Process
Run kap-bot as a background process by running the following command

```
nohup python3 kapbot.py > log.txt 2> errors.log &
```

To check the process ID of the bot in the future, run the following command

```
ps aux | grep kapbot
```

To kill the bot process after identifying the process ID above

```
kill <PID>
```

## License
kap-bot is [MIT licensed](https://github.com/artfreyr/kap-bot/blob/master/LICENSE)

## Acknowledgements
Kaplan Singapore data source obtained from [Kaplan Singapore Class Schedule](http://webapps.kaplan.com.sg/schedule/)
