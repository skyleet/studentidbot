from pickle import load

from prettytable import PrettyTable

with open('persistence_data.pickle', 'rb') as inf: data = load(inf)

used_in = data['bot_data']['used_in']

table = PrettyTable()
table.field_names = ['Chat name', 'Chat ID', 'Username', 'Student ID', 'Last name', 'First name']
table.align['Chat name'] = 'l'
table.align['Chat ID'] = 'r'
table.align['Username'] = 'l'
table.align['Student ID'] = 'l'
table.align['Last name'] = 'l'
table.align['First name'] = 'l'

for cid, sid2info in data['chat_data'].items():
  cname = used_in[cid] if cid in used_in else ''
  for sid, info in sid2info.items():
    table.add_row([cname, cid, sid, info['id'], info['last_name'], info['first_name']])

print(table)