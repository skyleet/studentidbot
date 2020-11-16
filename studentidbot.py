#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.2.2'

import logging
import sqlite3
from collections import namedtuple
from threading import Lock

from telegram import ForceReply, ParseMode, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler, Defaults,
                          Filters, MessageHandler, Updater)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
database = None
dblock = Lock()

RealID = namedtuple('RealID', 'id, username, first_name, last_name, chat_id, chat_title, sid, real_first_name, real_last_name')
START, STUDENTID, FIRSTNAME, LASTNAME = range(4)

def db_close():
  global database
  database.commit()
  database.close()
  database = None
  logging.info('Database commited and closed')

def db_init():
  global database
  database = sqlite3.connect('studentidbot.db', check_same_thread = False)
  try:
    with dblock, database:
      database.execute("""
        CREATE TABLE realids (
          id INTEGER PRIMARY KEY,
          username TEXT,
          first_name TEXT,
          last_name TEXT,
          chat_id INTEGER,
          chat_title TEXT,
          sid TEXT,
          real_first_name TEXT,
          real_last_name TEXT
        )""")
    logging.info('Database created')
  except sqlite3.DatabaseError:
    logging.info('Database already present')

def db_replace(data):
  with dblock, database:
    database.execute('REPLACE INTO realids (id, username, first_name, last_name, chat_id, chat_title, sid, real_first_name, real_last_name) VALUES (:id, :username, :first_name, :last_name, :chat_id, :chat_title, :sid, :real_first_name, :real_last_name)', data)
  logging.info('Database replaced: %s', str(data))

def db_remove(id):
  with dblock, database:
    cur = database.execute('DELETE FROM realids WHERE id=:id', {'id': id})
  logging.info('Database removed: %s', id)
  return cur.rowcount == 1

def db_query(chat_title, query):
  if query[0].startswith('@'):
    select = 'SELECT sid, real_first_name, real_last_name FROM realids WHERE chat_title=:chat_title AND username=:username'
    params = {'chat_title': chat_title, 'username': query[0][1:]}
  else:
    select = 'SELECT sid, real_first_name, real_last_name FROM realids WHERE chat_title=:chat_title AND COALESCE(first_name, "") || COALESCE(last_name, "") LIKE :like'
    params = {'chat_title': chat_title, 'like': '%' + '%'.join(query) + '%'}
  with dblock, database:
    cur = database.execute(select, params)
    rows = cur.fetchall()
  if rows:
    result = [f'Identity:']
    for row in rows:
      result.append(f'{row[1]} {row[2]} (AIR: {row[0]})')
    return '\n'.join(result)
  else:
    return f'No information found for `{" ".join(query)}` in {chat_title} chat.'

def error(update, context):
  logger.warning(f'Update {update} caused error:', exc_info = context.error)

def _gas(obj, key):
  res = getattr(obj, key, None)
  return '' if res is None else res

def version(update, context):
  update.message.reply_text(f'This is StudentIDBot version {__version__}.')

def askme(update, context):
  chat = update.message.chat
  user = update.message.from_user
  context.chat_data[user.id] = {
    'id': user.id,
    'username': _gas(user, 'username'),
    'first_name': _gas(user, 'first_name'),
    'last_name': _gas(user, 'last_name'),
    'chat_id': chat.id,
    'chat_title': _gas(chat, 'title'),
  }
  greet = _gas(user, 'username')
  if not greet:
    greet = ' '.join([_gas(user, 'first_name'), _gas(user, 'last_name')])
  update.message.reply_text(
    f'Hi *{greet}*, I am the Student Identities Bot. I will now ask you some questions, '
    'feel free to use /cancel at any time to stop this conversation, if you make a mistake just start over with /askme.\n\n'
    'What is your *CGL18 AIR*?',
  reply_markup = ForceReply())
  return STUDENTID

def studentid(update, context):
  user = update.message.from_user
  sid = update.message.text.strip()
  logger.info("Student id of %s is %s", user.first_name, sid)
  context.chat_data[user.id]['sid'] = sid
  update.message.reply_text('What is your *real first name*?', reply_markup = ForceReply())
  return FIRSTNAME

def firstname(update, context):
  user = update.message.from_user
  fname = update.message.text.strip()
  logger.info("Student firstname of %s is %s", user.first_name, fname)
  context.chat_data[user.id]['real_first_name'] = fname
  update.message.reply_text('What is your *real last name*?', reply_markup = ForceReply())
  return LASTNAME

def lastname(update, context):
  chat = update.message.chat
  user = update.message.from_user
  lname = update.message.text.strip()
  logger.info("Student lastname of %s is %s", user.first_name, lname)
  context.chat_data[user.id]['real_last_name'] = lname
  db_replace(context.chat_data[user.id])
  del context.chat_data[user.id]
  update.message.reply_text(
    f'Thank you, your identity has been recorded for the group *{chat.title}*.',
    reply_markup = ReplyKeyboardRemove()
  )
  return ConversationHandler.END

def cancel(update, context):
  user = update.message.from_user
  logger.info("User %s canceled the conversation.", user.first_name)
  try:
    del context.chat_data[user.username]
  except KeyError:
    pass
  update.message.reply_text(
    'Your identity has not been recorded; you can use /askme to start over.',
    reply_markup = ReplyKeyboardRemove()
  )
  return ConversationHandler.END

def whois(update, context):
  chat = update.message.chat
  user = update.message.from_user
  args = context.args
  if not args:
    update.message.reply_text('Please specify at least a username, or fist/last name!')
    return
  logger.info("User %s asked for %s.", user.first_name, ', '.join(args))
  update.message.reply_text(db_query(chat.title, args))

def forgetme(update, context):
  chat = update.message.chat
  user = update.message.from_user
  logger.info("User %s asked to be forgotten", user.first_name)
  if db_remove(user.id):
    update.message.reply_text(f'You real identity has been removed from group *{chat.title}*.')
  else:
    update.message.reply_text(f'You real identity was not known in group *{chat.title}*.')

def main(token):
  logging.info(f'StudentIDBot version {__version__} starting…')
  db_init()
  defaults = Defaults(parse_mode = ParseMode.MARKDOWN)
  updater = Updater(token, defaults = defaults, use_context = True)
  dp = updater.dispatcher
  dp.add_handler(ConversationHandler(
      entry_points = [CommandHandler('askme', askme, pass_chat_data = True)],
      states = {
          STUDENTID: [MessageHandler(Filters.text & ~Filters.command, studentid, pass_chat_data = True)],
          FIRSTNAME: [MessageHandler(Filters.text & ~Filters.command, firstname, pass_chat_data = True)],
          LASTNAME: [MessageHandler(Filters.text & ~Filters.command, lastname, pass_chat_data = True)]
      },
      fallbacks = [CommandHandler('cancel', cancel, pass_chat_data = True)]
  ))
  dp.add_handler(CommandHandler('whois', whois, pass_args = True))
  dp.add_handler(CommandHandler('forgetme', forgetme))
  dp.add_handler(CommandHandler('version', version))
  dp.add_error_handler(error)
  updater.start_polling()
  updater.idle()
  db_close()

if __name__ == '__main__':
  import os
  main(os.environ.get('TOKEN'))
