#! /usr/bin/env python3
""" IRC protocol module for Acronymph

loosely based on Joel Rosdahl's irc.bot example

bot class implements and gets these messages from the game class:

self.send_channel_message(channel, message)
self.send_private_message(nick, message)

It should talk to the game like this:
self.g = game.game(channel, self)  # initialize "g" as game object
self.g.start()  # Start the acromania game
if self.g.running:
    self.send_channel_message(channel, 'The game is already running.  Please finish this one or !stopacro before starting a new game.')


"""

import logging
import time
import ssl

import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

import acronymph
import mysecrets

class DummyGame():
    def __init__(self):
        self.running = False

class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.g = DummyGame()
        self.connection.add_global_handler("error", self.on_error)


    def send_channel_message(self, channel, message):
        print("To " + channel + ": " + message)
        self.connection.privmsg(self.channel, message)

    def send_private_message(self, target, message):
        print("To " + target + ": " + message)
        self.connection.privmsg(target, message)


    def on_nicknameinuse(self, c, e):
        print(e)
        c.nick(c.get_nickname() + "_")

    def nickserv_identify(self):
        self.send_private_message('nickserv', mysecrets.nickservRegString)
        time.sleep(2)

    def on_error(self, c, e):
        print(e)

    def on_mode(self, c, e):
        print(e)

    def on_kick(self, c, e):
        print(e)

    def on_quit(self, c, e):
        print(e)

    def on_welcome(self, c, e):
        self.nickserv_identify()
        time.sleep(2)
        c.join(self.channel)

    def on_privmsg(self, c, e):
        print(e)
        sender = e.source.nick
        msg = e.arguments[0]
        if self.g.running:  # Is the game running?  If so...
            if self.g.takingacros:  # Are we waiting for submissions?
                self.g.take_acro(sender, msg)  # pass nick/submission to handler
            elif self.g.takingvotes:  # Are we waiting for votes instead?
                self.g.take_vote(sender, msg)  # pass nick/vote to handler
            else:  # We must be inbetween rounds...
                self.send_private_message(sender, 'Voting is over.  Please wait for the next round to begin.')
        else: self.send_private_message(sender, 'The game is currently not running.') 

        #self.do_command(e, e.arguments[0])


    def on_pubmsg(self, c, e):
        print(e)
        #a = e.arguments[0].split(":", 1)
        a = e.arguments[0]
        print(a)
        #if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(
        #    self.connection.get_nickname()
        #):
            #self.do_command(e, a[1].strip())
        self.do_command(e, a)
        #msg = e.capitalize()
        #msg = e.arguments[0].split(":", 1)
        return

    def on_dccmsg(self, c, e):
        # non-chat DCC messages are raw bytes; decode as text
        text = e.arguments[0].decode('utf-8')
        c.privmsg("You said: " + text)

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        channel = self.channel

        #if cmd == "disconnect":
        #    self.disconnect()
        #elif cmd == "die":
        #    self.die()
        #elif cmd == "stats":
        #    for chname, chobj in self.channels.items():
        #        c.notice(nick, "--- Channel statistics ---")
        #        c.notice(nick, "Channel: " + chname)
        #        users = sorted(chobj.users())
        #        c.notice(nick, "Users: " + ", ".join(users))
        #        opers = sorted(chobj.opers())
        #        c.notice(nick, "Opers: " + ", ".join(opers))
        #        voiced = sorted(chobj.voiced())
        #        c.notice(nick, "Voiced: " + ", ".join(voiced))
        #elif cmd == "dcc":
        #    dcc = self.dcc_listen()
        #    c.ctcp(
        #        "DCC",
        #        nick,
        #        "CHAT chat %s %d"
        #        % (ip_quad_to_numstr(dcc.localaddress), dcc.localport),
        #    )
        if cmd == "!help":
            print("Help")
            self.send_channel_message(self.channel, 'Commands include: !acro, !stopacro')
            #self.send_private_message(nick, 'Commands include: !acro, !stopacro')
        #else:
        #    c.notice(nick, "Not understood: " + cmd)
        if cmd == "!acro":
                try:
                    if self.g.running:
                        self.send_channel_message(channel, 'The game is already running.  Please finish this one or !stopacro before starting a new game.')
                    else:
                        self.g = acronymph.Game(channel, self)  # initialize "g" as game object
                        self.g.start()  # Start the acromania game
                except AttributeError:
                    self.g = acronymph.game(channel, self)  # initialize "g" as game object
                    self.g.start()  # Start the acromania game
        elif cmd == "!stopacro":
                try:
                    if self.g.running:
                        self.g.end_game()
                    else:
                        self.send_channel_message(channel, 'The game is not running.')
                except AttributeError:
                    self.send_channel_message(channel, 'The game is not running')


def init_ssl():
    pass

def main():
    import sys

    #if len(sys.argv) != 4:
    if len(sys.argv) < 4:
        print("Usage: irc-bot.py <server[:port]> <channel> <nickname> <-ssl>")
        sys.exit(1)
    
    if len(sys.argv) == 5:
        if sys.argv[4] == '-ssl':
            sslEnabled = True
            print("ssl enabled")
            init_ssl()
        else:
            sslEnabled = False

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = Bot(channel, nickname, server, port)
    bot.start()


if __name__ == "__main__":
    main()
