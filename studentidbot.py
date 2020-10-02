#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import logging
from threading import Lock
import sqlite3

from telegram import ForceReply, ParseMode
from telegram.ext import (CommandHandler, ConversationHandler, Defaults,
                          Filters, MessageHandler, PicklePersistence, Updater)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
database = sqlite3.connect('studentidbot.db', check_same_thread = False)
dblock = Lock()

RealID = namedtuple('RealID', 'id, username, first_name, last_name, chat_id, chat_title, sid, real_first_name, real_last_name')
START, STUDENTID, FIRSTNAME, LASTNAME = range(4)

def db_init():
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
    print(select)
    cur = database.execute(select, params)
    rows = cur.fetchall()
  if rows:
    result = [f'In {chat_title} chat `{" ".join(query)}` information are:']
    for row in rows:
      result.append(f'{row[1]} {row[2]} ({row[0]})')
    return '\n'.join(result)
  else:
    return f'No information found for `{" ".join(query)}` in {chat_title} chat.'

def error(update, context):
  logger.warning('Update "%s" caused error "%s"', update, context.error)

def askme(update, context):
  chat = update.message.chat
  user = update.message.from_user
  context.chat_data[user.id] = {
    'id': user.id,
    'username': user.username,
    'first_name': user.first_name,
    'last_name': user.last_name,
    'chat_id': chat.id,
    'chat_title': chat.title,
  }
  greet = user.username if user.username else ' '.join([user.first_name, user.last_name])
  update.message.reply_text(
    f'Hi *{greet}*, I am the Student Identities Bot. I will now ask you some questions, '
    'feel free to use /cancel at any time to stop this conversation, if you make a mistake just start over with /askme.\n\n'
    'What is your student *ID number*?',
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
  print(context.chat_data[user.id])
  db_replace(context.chat_data[user.id])
  del context.chat_data[user.id]
  update.message.reply_text(f'Thank you, your identity has been recorded for the group *{chat.title}*.')
  return ConversationHandler.END

def cancel(update, context):
  user = update.message.from_user
  logger.info("User %s canceled the conversation.", user.first_name)
  del context.chat_data[user.username]
  update.message.reply_text('Your identity has not been recorded; you can use /askme to start over.')
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
      fallbacks = [CommandHandler('cancel', cancel)]
  ))
  dp.add_handler(CommandHandler(
    'whois', whois,
    pass_args = True,
    pass_chat_data = True
  ))
  dp.add_handler(CommandHandler(
    'forgetme', forgetme,
    pass_chat_data = True
  ))
  dp.add_error_handler(error)
  updater.start_polling()
  updater.idle()

if __name__ == '__main__':
  import os
  main(os.environ.get('TOKEN'))
