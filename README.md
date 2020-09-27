# Student Identities Bot

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)

This repository contains a simple [Telegram bot](https://core.telegram.org/bots)
that allows students taking part to group chats to voluntarily submit their real
identities (first and last name and identity number) to allow the teacher and
other students to connect their nicknames to their real identity.

Every group chat participant can issue the `/askme` command that will ask
him/her a few questions to create an association from the participant *nickname*
to the answered identity; if the participant changes his/her mind, the
association can be erased at any time with the `/forgetme` command.

Other group chat participants can query the association with the command
`/whois` followed by a list of space separated *nicknames* (possibly starting
with `@`).

## Instructions

The bot is based on the
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
library, so you should first install it, if you are new to Python, follow the nice
"[Installing Packages](https://packaging.python.org/tutorials/installing-packages/)" tutorial by the [Python Packaging Authority](https://www.pypa.io/).

Then, once obtained a *token* from the
[BotFather](https://telegram.me/BotFather) store it in an environment variable
named `TOKEN` and run the bot with

    python studentidbot.py

Collected data is persisted in `persistence_data.pickle` across runs.
