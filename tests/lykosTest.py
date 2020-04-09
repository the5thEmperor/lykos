import oyoyo.parse as parse

def test_start_cmd():
    element = bytes(":Kevin!bncworld@I-Have.a.cool.vhost.com PRIVMSG #mIRC :I feel lucky today", encoding="utf8")
    check = parse.parse_raw_irc_command(element)
    print(check[0].decode())
    assert check[0].decode() == "Kevin!bncworld@I-Have.a.cool.vhost.com" and check[1] == "privmsg" \
           and check[2][0].decode() == "#mIRC" and check[2][1].decode() == 'I feel lucky today'

def test_parse_nick():
    user = "mywolfbot!~mywolfbot@pool-173-48-152-9.bstnma.fios.verizon.net"
    userName = parse.parse_nick(user)
    assert userName[0] == "mywolfbot" and userName[1] == None and userName[2] == "~mywolfbot" \
           and userName[3] == "pool-173-48-152-9.bstnma.fios.verizon.net"
