Logbook Telegram Bot
====================

Setup
-----
Install deps with pipenv

Clone env.ini.dist into env.ini

Fabric deployment
-----------------
```
# get list of commands and help
pipenv run fab --list
pipenv run fab --help deploy

# deploy
pipenv run fab deploy --hosts <host>
```

Systemd
-------
/etc/systemd/system/logbook.service
```
[Unit]
Description=Logbook Bot
After=network.target

[Service]
User=deployer
Group=nginx
WorkingDirectory=/srv/www/logbook-bot
ExecStart=/usr/local/bin/pipenv run python bot.py
```