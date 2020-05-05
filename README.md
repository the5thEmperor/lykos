**Project Summary**

Lykos is a mafia style text game using an IRC bot to manage the game, give players their role, allow players to take actions, and determine the winners.  The game itself secretly assigns roles via direct message.  There are always villagers and wolves in the game, but the more participating players, the more types of roles are assigned.  There are also game variations that have certain roles assigned based on the rules of that particular game play.  The object of the game is for either the villagers to lynch all the wolves or the wolves to kill enough villagers so that there is an equal amount.  

***

**How To Run**

Log into freenode:

An account for an IRC webchat service is required.  We used freenode.net and will describe how to set the bot up to connect to freenode.net. To login go to webchat.freenode.net, click the checkbox indicating you have a password, and fill in the nick and password for an account provided below, and for channel put in ##wolftrial. Then complete the “I’m not a robot” captcha and sign in. 

Here are some test accounts:
```
Username: ProfSantore
Password: password

Username: Hoobshanker
Password: password

Username: The5thEmperor
Password: password

Username: TestCapstone1
Password: password

Username: TestCapstone2
Password: password

Username: TestCapstone3
Password: password
```
*Note one our group issues is for a game mode called “Boreal” that requires at least 6 players to start the game, so six accounts have been provided. However, freenode.net only allows 5 accounts to sign in from the same IP, and using two computers with one sporting a VPN can cause problems with the bots connection. This is what caused this to be a group issue as it required more than one person to fix and test. We will demo this issue to you as it may be difficult for you to test it on your own. 
___
**Setting up the bot:**

To set up the bot, you should clone the git repo. Then on control panel navigate to the subdirectory that houses the clone. 

*Note there is already a botconfig.py file in master that connects with the account “Hoobshanker” and gives “Hoobshanker” admin commands, however this next step is included as it is needed if cloned from the original repo. Can also go into the current botconfig.py and alter the settings to use a different account as the admin.
Using your OS command for copying files, copy botconfig.py.example to a new file called botconfig.py. Then go into botconfig.py on pycharm and change the following settings:
```
USERNAME = “” (fill in the quotation marks with a freenode username we have provided, ex. ProfSantore)

PASS = “my_nickserv_pass” (replace inside the quotation marks with a freenode password, all our accounts just use password)

CHANNEL = “##mywolfgame” (change inside the quotation marks to ##wolftrial)

OWNERS = ("unaffiliated/wolfbot_admin1",)  (Replace inside the quotation marks with the account used in Username, ex. ProfSantore this allows admin commands to be used. Leave the comma after as it is needed)

OWNERS_ACCOUNTS = ("1owner_acc",) (Replace inside the quotation marks with the account used in Username, ex. ProfSantore this allows admin commands to be used. Leave the comma after as it is needed.)
```
Once the botconfig.py is set up as described above, open a command line and navigate to the subdirectory the project is in. Use the python command to run wolfbot.py, which should then present output showing it creating a connection to freenode.net.
___
**Running the Game:**

To run a game there must be at least 4 players logged in and joined the game (6 if playing in Boreal mode). 
Log in as described above to webchat.freenode.net with at least 4 accounts, one of which being the account which has admin commands (the default if botconfig.py is not altered is “Hoobshanker”)
Go to the wolftrial channel on the account with admin privileges.  

The admin commands can be found on: https://werewolf.chat/Admin_commands  The commands we used most frequently are:
```
!fjoin <Nick>           Admin can add players to the game regardless of warnings.  Replace <Nick> with freenode username.	

!fday	                Advance the game play to turn to day

!fnight	                Advance the game play to turn to night

!fgame <game type>	Force a particular game mode. Replace <game type> with mode. i.e. “boreal”

!fstart	                Forces a game to start

!fstop	                Ends a game
```
*Note:  There is a game type called “roles.”  To play it, you would use the command:
````
!fgame roles=<role>:<amount>,<role>:<amount>,…etc 
````
This allows the admin to force a game with specific roles.  This was an imperative command for testing.  Replace <role> with the desired role and replace <amount> with the desired number of players you wish to receive that role.  Distribution of which username will receive that role however remains random.

Once players are joined, and game is started, the bot with direct message players their role.  Players will interact with each other and the bot via messages.  The bot will direct players on commands, timelines, and status of the game.  Once a game is ended, players will need to be rejoined before starting a new game. 
