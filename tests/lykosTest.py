import oyoyo.parse as parse
import src
import src.settings as var

def test_parse_raw_irc_command():
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


def test_add_users():
    new_user = src.users.add(cli="6697", nick="Hoobshanker!None@None:None")
    assert new_user.nick == "Hoobshanker"


def test_get_users():
    src.users.add(cli="6697", nick="Hoobshanker!None@None:None")
    check = src.users.get(nick="Hoobshanker!None@None:None")
    assert check.nick == "Hoobshanker"


def test_get_players():
    new_user = src.users.add(cli="6697", nick="Hoobshanker!None@None:None")
    var.MAIN_ROLES = {"Hoobshanker": "villager"}
    var.ALL_PLAYERS = [new_user.nick]
    check = src.functions.get_players()
    assert check[0] == "Hoobshanker"


def test_is_silent():
    new = src.users.add(cli="6697", nick="Rissa09!None@None:None")
    src.status.add_silent(var=None, user=new)
    assert src.status.is_silent(var=None, user=new)


def test_add_dying():
    var.GAME_ID = 1
    new = src.users.add(cli="6697", nick="Rissa09!None@None:None")
    var.MAIN_ROLES = {new: "villager"}
    var.ALL_PLAYERS = [new]
    assert src.status.add_dying(var=var, player=new, killer_role="wolf", reason="kill")


def test_is_dying():
    new = src.users.add(cli="6697", nick="Rissa09!None@None:None")
    var.MAIN_ROLES = {new: "villager"}
    var.ALL_PLAYERS = [new]
    src.status.add_dying(var=var, player=new, killer_role="wolf", reason="kill")
    assert src.status.is_dying(var, new)
