# instagrapi-bot

_A bot that uses the instagrapi library_

## Requirements

- Python >= 3.6

## Instructions

- Install the dependencies

```
$ pip install -r requirements.txt
```

- Create the bot configuration file

```
$ py config_generator.py -p /home/me/instagrapi/accounts
```

- Edit the created configuration file at your convenience

```
$ vi /home/me/instagrapi/accounts/my.ig.user/config.json
```

- Run the bot

```
$ py ig_bot.py -p /home/me/instagrapi/accounts/my.ig.user
```

- Take a nap

- If you need to update the credentials

```
$ py relogin.py -p /home/me/instagrapi/accounts
```
