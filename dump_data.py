from pickle import load

with open('persistence_data.pickle', 'rb') as inf: data = load(inf)

used_in = data['bot_data']['used_in']
for cid, sid2info in data['chat_data'].items():
  print(used_in[cid])
  for sid, info in sid2info.items():
    print('\t' + sid + ' ' + str(info))