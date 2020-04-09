import oyoyo.parse as parse

def test_parse_raw_irc_command():
    element = bytes(":Kevin!bncworld@I-Have.a.cool.vhost.com PRIVMSG #mIRC :I feel lucky today", encoding="utf8")
    check = parse.parse_raw_irc_command(element)
    print(check[0].decode())
    assert check[0].decode() == "Kevin!bncworld@I-Have.a.cool.vhost.com" and check[1] == "privmsg" \
           and check[2][0].decode() == "#mIRC" and check[2][1].decode() == 'I feel lucky today'
