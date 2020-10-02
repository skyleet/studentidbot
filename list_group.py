import csv
import getpass
import os
import sys

from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

api_id = os.environ['API_ID'] # get yours from my.telegram.org
api_hash = os.environ['API_HASH']
phone = os.environ['PHONE']

client = TelegramClient(phone, api_id, api_hash)
client.connect()
if not client.is_user_authorized():
  client.send_code_request(phone)
  code = input('Enter the code: ')
  try:
    client.sign_in(phone, code = code)
  except SessionPasswordNeededError:
    password = getpass.getpass('Enter tfa password: ')
    client.sign_in(phone, password = password)

result = client(GetDialogsRequest(
  offset_date = None,
  offset_id = 0,
  offset_peer = InputPeerEmpty(),
  limit = 1000,
  hash = 0
))

groups = [g for g in result.chats if hasattr(g, 'megagroup') and g.megagroup]

print('Choose a group to scrape members from:', file = sys.stderr)
for i, g in enumerate(groups): print(f'{i}- {g.title}', file = sys.stderr)
print('Enter a Number: ', file = sys.stderr)
target_group = groups[int(input())]

writer = csv.writer(sys.stdout, dialect = 'excel-tab', lineterminator = '\n')
for user in client.get_participants(target_group, aggressive = True):
  writer.writerow([user.id, user.username, user.first_name, user.last_name])
