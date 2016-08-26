#! /usr/bin/python3

from handlers.data import DataHandler
from apis.football import FootballApi
from handlers.crests import CrestHandler
from handlers.stream import StreamHandler
from apis.livescore import LivescoreApi
from apis.streamsports import StreamsportsApi
from apis.footlol import FootlolApi

# data = DataHandler()
# item = data.load_channels()

foot = FootballApi()
foot.save_fixtures()

crest = CrestHandler()
crest.load_all_crests()

live = LivescoreApi()
item = live.update_fixtures()

event = StreamsportsApi()
data = event.save_events()

chan = FootlolApi()
data = chan.save_channels()

# stream = StreamHandler(None)
# stream.open_stream('acestream://2daebf062c9e89835691fa5a48d5f7dc4d42eba7')
