#!/usr/bin/python
"""
Acromania engine, for communicating with chat protocols

Talks to chat protocol class "chat" through:

    # channel, nick and message are strings
    chat.send_channel_message(channel, message)
    chat.send_private_message(nick, message)

Receives messages from chat protocol class:
The chat protocol class can use it like this:

    mygame = acronymph.Game()
    g.start()
    g.end_game()
    if g.running: print("The game is running!")

"""

import string
import sys
import threading
import time
from random import randint


class GameConfig:
    def __init__(self):
        self.rounds = 5     # number of rounds per game
        self.acro_seconds = 90  # how many seconds people have to submit acronyms
        self.vote_seconds = 60  # how many seconds people have to vote
        self.time_between_rounds = 10

    def loadConfig():
        pass

    def saveConfig():
        pass

class Game:

    def __init__(self, channel, bot):
        self.bot = bot  # set game.bot to the silc object
        self.channel = channel  # okay, self.channel is the channel
        self.roundplayers = {}  # Participators in the current round, and their acro
        self.round = None  # int to represent current round number
        self.acronym = []  # the current acronym that must be matched
        self.running = False  # Is the game running or stopped?
        self.points = {} # total game points per player, {'username': pointsint}
        self.votes = {} # votes this round, user:points like above
        self.takingacros = False  # Are we in a mode where we're accepting acronyms?
        self.takingvotes = False  # Are we waiting for people to vote?
        self.votinggrid = {}  # our grid for voting, number:nick
        self.hasvotted = []  # List of who has voted so far this round
        # load config
        self.config = GameConfig()
    
    def start(self):
        """If someone hits !start and the game is not yet running,
        run this function to start the fun
        """
        self.points = {}  # clear out the points board for the new game
        self.round = 1  # starting at round 1
        self.running = True  # game on

        self.bot.send_channel_message(self.channel, 'The game is starting and goes to ' + str(self.config.rounds) + ' rounds.  You have ' + str(self.config.acro_seconds) + ' seconds to submit an acronym per round.  Submit your acronyms with /msg bot acronym.  Get ready!')
        self.start_round()

    def start_round(self):
        """Start a round
        """
        self.roundplayers = {}  # clear out the list of players/acros from last round
        self.votes = {}  # clear out the list of players/votes from last round
        self.hasvoted = []  # Clear out list of who has voted for the round
        self.acronym = None
        self.acronym = self.make_acro()  # make the acronym for this round
        print(self.acronym)
        print()
        self.bot.send_channel_message(self.channel, 'Round #%i.  The acronym for this round is: %s' % (self.round, ''.join(self.acronym)))
        print("The acronym for round #%i is: " % self.round)
        print(self.acronym)
        self.bot.send_channel_message(self.channel, "You have " + str(self.config.acro_seconds) + " seconds to submit an acronym using /msg bot <acro>.  Start now!")
        self.t = threading.Timer(self.config.acro_seconds, self.start_voting)  # Creating a timer thread to run start_voting() in 30 seconds
        self.t2 = threading.Timer(self.config.acro_seconds - 10, self.ten_second_warning)  # create a timer to give a warning 10 seconds before the submissions are up
        self.t.start()  # start the timer thread
        self.t2.start()  # start warning timer thread
        self.takingacros = True  # Let's start taking submissions for this round

    def ten_second_warning(self):   # dumb little method to use with t2 Timer object in start_round()
        self.bot.send_channel_message(self.channel, '10 seconds left!')

    def start_voting(self):
        """Run this function when the entries are all in and we're going to start voting.
        """
        self.takingacros = False  # We're no longer accepting entries.
        self.bot.send_channel_message(self.channel, "Time's up!  Please vote on your favorite acro with /msg bot #")
        # We need to set self.votes {} to a blank scoreboard with each user:0
        for k in self.roundplayers:
            self.votes[k] = 0
        # Initialize the voting grid
        votekey = 0  # this is the integer used to generate the key or voting #
        for k in self.roundplayers:  # for each player/key in roundplayers...
            votekey = votekey + 1  # set the index number
            self.votinggrid[votekey] = k  # assign number:nick for voting
        # finished initializing the voting grid
        # print self.votinggrid  # just let us see this voting grid
        # now let's see it as it should be seen in chat:
        for x in range(1, len(self.roundplayers) + 1):  # count each roundplayer key as x, and for each one
            print("Acronym #%i: %s" % (x, self.roundplayers[self.votinggrid[x]]))  # print a ballot (to the channel)
            self.bot.send_channel_message(self.channel, "#%i: %s" % (x, self.roundplayers[self.votinggrid[x]]))
        self.takingvotes = True  # We're now accepting votes
        print(self.roundplayers)  # self.roundplayers{} are our nick:acro entries
        self.bot.send_channel_message(self.channel, 'Please place your vote.  You have ' + str(self.config.vote_seconds) + ' seconds.')
        self.t = threading.Timer(self.config.vote_seconds, self.stop_voting)  # Create a timer thread to control how long we have to vote
        self.t.start()

    def stop_voting(self):
        """Run this when the time is up for voting.  This basically
        wraps up the round and sets us up for the next round.
        """
        self.takingvotes = False  # We're no longer accepting votes for this round.
        print("Voting time is over!  here are the results: ")
        self.bot.send_channel_message(self.channel, "Voting time is over.  Here are the results!")
        print(self.votes)  # self.votes{} is our nick:votes for this round
        # increment self.points scoreboard here
        for names in self.votes:
            # Here we need to add code that checks to see if the user voted this round,
            # and gives them 0 points if that's thecase. Otherwise, they get their round points.
            if names in self.hasvoted:
                try:
                    self.points[names] = self.points[names] + self.votes[names]
                except KeyError:
                    self.points[names] = self.votes[names]
            else:
                pass
        # print proper votes results here
        for names in self.roundplayers: 
            self.bot.send_channel_message(self.channel, "%s's acronym %s received %i votes" % (names, self.roundplayers[names], self.votes[names]))
            if names in self.hasvoted:
                pass
            else:
                self.bot.send_channel_message(self.channel, "But %s didn't vote, so they receive 0 points this round." % names)
        if self.round < self.config.rounds:  # after x rounds we end the game
            print("Total points: ")
            print(self.points) # self.points{} is our nick:points for the game
            # start proper scoreboard
            self.bot.send_channel_message(self.channel, "Total scores:")
            for names in self.points:
                self.bot.send_channel_message(self.channel, "%s: %i" % (names, self.points[names]))
            # stop scoreboard
            self.round = self.round + 1
            self.bot.send_channel_message(self.channel, "The next round starts in %i seconds. Get ready!" % self.config.time_between_rounds)
            self.t = threading.Timer(self.config.time_between_rounds, self.start_round) # create a timer to start the next round in 10
            self.t.start()
        else:
            self.end_game()  # If we're on the final round, time to end the game.

    def make_acro(self):
        """Returns a list object to describe the acronym, of random
        length between 3 and MAXACRO
        """
        #alphabet = [char for char in string.ascii_uppercase]   # If you want a non-weighted alphabet
        # add weight to the alphabet to prevent excessive Z Q and Xs
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'A', 'A', 'B', 'C', 'D', 'E', 'E', 'F', 'G', 'H', 'I', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y'] # weight
        acrolen = randint(4, 6)
        acro = []
        for i in range(1, acrolen):
            acro.append(alphabet[randint(0, len(alphabet) -1)])
        return acro

    def take_acro(self, nick, message):
        """When self.takingacros is True, we want to take a submission.
        Test to see if it's a good acronym, check and see if they've already
        submitted an answer.  Add the answer if it's good and they haven't,
        change it if they already have an answer.
        """
        if self.test_acro(message, self.acronym):  # Good acronym?
            # Check to see if user has voted already, if so, change answer. If not, accept it.
            if nick in self.roundplayers:
                self.bot.send_private_message(nick, 'Your acronym has been changed to: %s' % message)
                self.bot.send_channel_message(self.channel, "Acronym changed.")
            else:
                self.bot.send_private_message(nick, 'Acronym accepted. Thank you.')
                self.bot.send_channel_message(self.channel, "Acronym received.")
            self.roundplayers[nick] = message
        else:
            self.bot.send_private_message(nick, 'Acronym rejected.')
            pass

    def take_vote(self, nick, message):
        """ When self.takingvotes is true and it's time to vote, take votes
        and add them into self.votes
        """ 
        print(nick, message)
        try:  # Take the message string and check to see if it's a valid vote.
            vote = int(message)  # Can we convert it to an integer?
        except ValueError:  # If this fails, the vote is not valid.
            vote = None
            print("Vote rejected.")
            #self.bot.send_private_message(nick, 'Invalid vote.')
        if vote in self.votinggrid:  # same as above commented line
            # Right here we need to check and see if the person has voted before before accepting.
            # No duplicate votes
            # if list self.hasvoted contains nick, reject the vote.  otherwise, accept
            if nick in self.hasvoted:
                self.bot.send_private_message(nick, 'You have already voted for this round.')
            elif nick == self.votinggrid[vote]:
                self.bot.send_private_message(nick, 'You cannot vote for yourself.')
            else:
                # accept the vote - and add to list self.hasvoted[]
                self.votes[self.votinggrid[vote]] = self.votes[self.votinggrid[vote]] + 1 # add a round point
                self.bot.send_private_message(nick, 'Your vote is for #%i.  Thanks for voting!' % vote)
                self.hasvoted.append(nick)  # add name to self.hasvoted list
                self.bot.send_channel_message(self.channel, "Vote received.")
        else:  # If it's an integer but outside of the range of valid votes, don't count the vote.
            self.bot.send_private_message(nick, 'Invalid vote.')

    def test_acro(self, useracro, gameacro):
        """Returns True if acro is acceptable,
        False if not
        """
        acrolist = useracro.split()
        for i in range(0, len(acrolist)):
            acrolist[i - 1] = acrolist[i - 1][0].capitalize()
        return acrolist == gameacro

    def end_game(self):
        """This function is run either at the end of the last round,
        or if a game is canceled by a user
        """
        self.t.cancel()  # End any potentially running timer threads
        self.t2.cancel()  
        self.bot.send_channel_message(self.channel, "The game is over!  Final scores are: ")
        time.sleep(1)
        print(self.points)  # self.points{} is our nick:score dict for the game
        for names in self.points:
            self.bot.send_channel_message(self.channel, "%s: %i" % (names, self.points[names]))
            time.sleep(1)
        self.bot.send_channel_message(self.channel, "Congratulations to the winner.")
        self.running = False

