from operator import itemgetter
from lxml import html
from fuzzywuzzy import fuzz
from helpers.utils import cached_request, thread_pool, replace_all


class StreamsApi:

  def __init__(self, data, cache):
    self.data  = data
    self.cache = cache

  def get(self, url='', ttl=86400):
    base_url = 'livefootballol.me'
    response = cached_request(url=url, cache=self.cache, base_url=base_url, ttl=ttl)

    try:
      response = html.fromstring(response)
    except TypeError:
      response = None

    return response

  def get_channels_pages(self):
    data  = self.get('channels')
    items = ['channels']

    if data is not None:
      for page in data.xpath('//div[@id="system"]//div[@class="pagination"]//a[@class=""]'):
        items.append(page.get('href'))

    return items

  def get_channels_page_links(self, url):
    data  = self.get(url)
    items = []

    if data is not None:
      for channel in data.xpath('//div[@id="system"]//table//a'):
        items.append(channel.get('href'))

    return items

  def get_channels_links(self):
    pages = self.get_channels_pages()
    items = thread_pool(self.get_channels_page_links, pages)

    return items

  def get_channel_details(self, url):
    data  = self.get(url)
    items = []

    if data is None:
      return items

    try:
      root = data.xpath('//div[@id="system"]//table')[0]
      name = root.xpath('.//td[text()="Name"]//following-sibling::td[1]')[0]
      lang = root.xpath('.//td[text()="Language"]//following-sibling::td[1]')[0]
      rate = root.xpath('.//td[text()="Bitrate"]//following-sibling::td[1]')[0]
      strm = root.xpath('.//a[starts-with(@href, "acestream:")]|.//a[starts-with(@href, "sop:")]')

      name = name.text_content().strip()
      lang = lang.text_content().strip()
      rate = rate.text_content().strip()

      name = self.parse_name(name)
      lang = 'Unknown' if lang == '' or lang.isdigit() else lang
      lang = 'Bulgarian' if lang == 'Bulgaria' else lang
      rate = 0 if rate == '' else int(rate.replace('Kbps', ''))

      channel = { 'name': name, 'language': lang.title() }
      stream  = { 'rate': rate, 'language': lang[:3].upper(), 'url': None, 'hd_url': None }

      for link in strm:
        href = link.get('href')
        host = href.split('://')[0]
        text = link.getparent().text_content()

        if host == 'sop':
          stream['host'] = 'Sopcast'
        else:
          stream['host'] = 'Acestream'

        if 'HD' in text:
          stream['hd_url'] = href
        else:
          stream['url'] = href

      if stream['url'] is not None:
        items.append({ 'channel': channel, 'stream': stream })
    except (IndexError, ValueError):
      pass

    return items

  def get_channels(self):
    links = self.get_channels_links()
    items = thread_pool(self.get_channel_details, links)

    return items

  def save_channels(self):
    data  = self.get_channels()
    items = []

    for item in data:
      stream  = item['stream']
      channel = self.data.set_single('channel', item['channel'], 'name')
      ch_id   = "%s_%s" % (channel.id, stream['host'].lower())

      stream.update({ 'channel': channel.id, 'ch_id': ch_id })
      items.append(stream)

    self.data.set_multiple('stream', items, 'ch_id')

  def get_events_page(self):
    data = self.get()
    page = None

    if data is not None:
      link = data.xpath('//div[@id="system"]//a[starts-with(@href, "/live-football")]')[0]
      page = link.get('href')

    return page

  def get_events_page_links(self):
    link  = self.get_events_page()
    data  = self.get(url=link, ttl=120)
    items = []

    if data is not None:
      for link in data.xpath('//div[@id="system"]//a[contains(@href, "/streaming/")]'):
        items.append(link.get('href'))

    return items

  def get_event_channels(self, url):
    data  = self.get(url=url, ttl=60)
    items = []

    if data is None:
      return items

    try:
      root = data.xpath('//div[@id="system"]//table')[0]
      comp = root.xpath('.//td[text()="Competition"]//following-sibling::td[1]')[0]
      team = root.xpath('.//td[text()="Match"]//following-sibling::td[1]')[0]

      comp = comp.text_content().strip()
      team = team.text_content().strip().split('-')
      home = team[0].strip()
      away = team[1].strip()

      event = { 'competition': comp, 'home': home, 'away': away }
      chann = []

      for link in data.xpath('//div[@id="system"]//a[contains(@href, "/channel/")]'):
        name = link.text_content()
        name = self.parse_name(name)

        chann.append(name)

      if chann:
        items.append({ 'event': event, 'channels': chann })
    except (IndexError, ValueError):
      pass

    return items

  def get_events(self):
    links = self.get_events_page_links()
    items = thread_pool(self.get_event_channels, links)

    return items

  def save_events(self):
    fixtures = self.data.load_fixtures(today_only=True)
    events   = self.get_events()
    items    = []

    for fixture in fixtures:
      channels = self.get_fixture_channels(events, fixture)
      streams  = self.data.get_multiple('stream', 'channel', channels)

      for stream in streams:
        items.append({
          'fs_id':   "%s_%s" % (fixture.id, stream),
          'fixture': fixture.id,
          'stream':  stream
        })

    self.data.set_multiple('event', items, 'fs_id')

  def get_fixture_channels(self, events, fixture):
    chann = []
    items = []

    for item in events:
      evnt = item['event']
      comp = fuzz.ratio(fixture.competition.name, evnt['competition'])
      home = fuzz.ratio(fixture.home_team.name, evnt['home'])
      away = fuzz.ratio(fixture.away_team.name, evnt['away'])
      comb = (comp + home + away) / 3

      items.append({ 'ratio': comb, 'channels': item['channels'] })

    if items:
      sort = sorted(items, key=itemgetter('ratio'), reverse=True)[0]

      if sort['ratio'] > 70:
        chann = self.data.get_multiple('channel', 'name', sort['channels'])
        chann = [c.id for c in chann]

    return chann

  def parse_name(self, name):
    find = ['Acestream', 'AceStream', 'Sopcast', 'SopCast']
    name = replace_all(name, find, '').strip()

    return name
