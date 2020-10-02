# Student Identities Bot

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)

This repository contains a simple [Telegram bot](https://core.telegram.org/bots)
that allows students taking part to group chats to voluntarily submit their real
identities (first and last name and identity number) to allow the teacher and
other students to connect their usernames to their real identity.

## Usage in group chats

Every group chat participant can issue the `/askme` command that will ask
him/her a few questions to create an association from the participant *username*
to the answered identity; if the participant changes his/her mind, the
association can be erased at any time with the `/forgetme` command.

Other group chat participants can query the association with the command
`/whois` followed by a query. If the query starts with `@` the bot will match
Telegram *usernames* (consider that not every Telegram user has set is own); on
the other hand, the bot will try an approximate match using the provided query
as the Telegram *fist name* and *last name*.

## Installing and running instructions

The bot is based on the
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
library, so you should first install it, if you are new to Python, follow the nice
"[Installing Packages](https://packaging.python.org/tutorials/installing-packages/)" tutorial by the [Python Packaging Authority](https://www.pypa.io/).

Then, once obtained a *token* from the
[BotFather](https://telegram.me/BotFather) store it in an environment variable
named `TOKEN` and run (a **single instance** per token of) the bot with

    python studentidbot.py

It's also possible to run it using [Docker](https://www.docker.com/), just run

    docker run --name studetidbot -e TOKEN=$TOKEN -v $(pwd):/app -d mapio/studentidbot:latest

Collected data is persisted across runs as a [SQLite](https://www.sqlite.org/)
database in `studentidbot.db`; you can use

    sqlite3 -header -column studentidbot.db 'select * from realids;'

to inspect the collected information.

### Stopping the bot

To stop the bot, use a `TERM` signal, to be sure that the database will be
committed and closed (this is reported in the logs). If using Docker, run

    docker kill --signal=TERM studetidbot
