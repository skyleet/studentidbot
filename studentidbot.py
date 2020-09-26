#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from telegram import ForceReply, ParseMode
from telegram.ext import (CommandHandler, ConversationHandler, Defaults,
                          Filters, MessageHandler, PicklePersistence, Updater)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

START, STUDENTID, FIRSTNAME, LASTNAME = range(4)

def error(update, context):
  logger.warning('Update "%s" caused error "%s"', update, context.error)

def askme(update, context):
  user = update.message.from_user
  update.message.reply_text(
    f'Hi *{user.username}*, I am the Student Identities Bot. I will now ask you some questions, '
    'feel free to use /cancel at any time to stop this conversation, if you make a mistake just start over with /askme.\n\n'
    'What is your student *ID number*?',
  reply_markup = ForceReply())
  return STUDENTID

def studentid(update, context):
  user = update.message.from_user
  sid = update.message.text.strip()
  logger.info("Student id of %s is %s", user.first_name, sid)
  context.chat_data[user.username] = {'id': sid}
  update.message.reply_text('What is your *first name*?', reply_markup = ForceReply())
  return FIRSTNAME

def firstname(update, context):
  user = update.message.from_user
  fname = update.message.text.strip()
  logger.info("Student firstname of %s is %s", user.first_name, fname)
  context.chat_data[user.username]['first_name'] = fname
  update.message.reply_text('What is your *last name*?', reply_markup = ForceReply())
  return LASTNAME

def lastname(update, context):
  chat = update.message.chat
  user = update.message.from_user
  lname = update.message.text.strip()
  logger.info("Student lastname of %s is %s", user.first_name, lname)
  context.chat_data[user.username]['last_name'] = lname
  if 'used_in' not in context.bot_data: context.bot_data['used_in'] = {}
  context.bot_data['used_in'][chat.id] = chat.title
  update.message.reply_text(f'Thank you, your identity has been recorded for the group *{chat.title}*.')
  return ConversationHandler.END

def cancel(update, context):
  chat = update.message.chat
  user = update.message.from_user
  logger.info("User %s canceled the conversation.", user.first_name)
  try:
    del context.chat_data[user.username]
    update.message.reply_text(f'Your identity has been removed from group *{chat.title}*; you can use /askme to start over.')
  except KeyError:
    update.message.reply_text('Your identity has not been recorded; you can use /askme to start over.')
  return ConversationHandler.END

def whois(update, context):
  user = update.message.from_user
  args = context.args
  nicks = []
  for arg in args:
    arg = arg.strip()
    if arg.startswith('@'): arg = arg[1:]
    nicks.append(arg)
  nicks = sorted(set(nicks))
  logger.info("User %s asked for %s.", user.first_name, ', '.join(nicks))
  reply = []
  for nick in  nicks:
    try:
      info = context.chat_data[nick]
      reply.append(f'`{nick}` is {info["first_name"]} {info["last_name"]} ({info["id"]})')
    except KeyError:
      reply.append(f'`{nick}` has not yet introduced him/herself to this group')
  update.message.reply_text(',\n'.join(reply) + '.')

def forgetme(update, context):
  chat = update.message.chat
  user = update.message.from_user
  logger.info("User %s asked to be forgotten", user.first_name)
  try:
    del context.chat_data[user.username]
    update.message.reply_text(f'You real identity has been removed from group *{chat.title}*.')
  except KeyError:
    update.message.reply_text(f'You real identity was not known in group *{chat.title}*.')

def main(token):
  pickler = PicklePersistence(filename = 'persistence_data.pickle')
  defaults = Defaults(parse_mode = ParseMode.MARKDOWN)
  updater = Updater(token, persistence = pickler, defaults = defaults, use_context = True)
  dp = updater.dispatcher
  dp.add_handler(ConversationHandler(
      entry_points = [CommandHandler('askme', askme)],
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
