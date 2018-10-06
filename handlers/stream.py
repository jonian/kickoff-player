import time
import hashlib
import pexpect

from helpers.utils import in_thread, run_command, kill_proccess


class StreamHandler(object):
  def __init__(self, player):
    self.player    = player
    self.acestream = None
    self.url       = None
    self.session   = None

  def notify(self, message):
    messages = {
      'starting':    'Starting stream engine...',
      'running':     'Stream engine running...',
      'error':       'Stream engine error!',
      'playing':     'Playing',
      'waiting':     'Waiting for response...',
      'unavailable': 'Stream unavailable!'
    }
    message = messages[message]
    self.player.update_status(message)

  def open(self, url):
    self.player.url = None
    self.player.stop()

    self.player.loading = True
    in_thread(target=self.open_stream, args=[url])

  def close(self):
    self.stop_acestream()

  def open_stream(self, url):
    self.close()
    self.notify('starting')

    if url.startswith('acestream://'):
      self.start_acestream(url)

    if not self.url is None:
      self.player.open(self.url)

    self.player.loading = False

  def start_acestream(self, url):
    engine = '/usr/bin/acestreamengine'
    client = '--client-console'

    try:
      self.acestream = run_command([engine, client])
      self.notify('running')
      time.sleep(5)
    except FileNotFoundError:
      self.notify('error')
      self.stop_acestream()

    pid = url.split('://')[1]
    self.start_acestream_session(pid)

  def stop_acestream(self):
    if not self.acestream is None:
      self.acestream.kill()

    if not self.session is None:
      self.session.close()

    kill_proccess('acestreamengine')

    self.player.loading = False

  def start_acestream_session(self, pid):
    product_key = 'n51LvQoTlJzNGaFxseRK-uvnvX-sD4Vm5Axwmc4UcoD-jruxmKsuJaH0eVgE'
    session = pexpect.spawn('telnet localhost 62062')
    self.notify('waiting')

    try:
      session.timeout = 10
      session.sendline('HELLOBG version=3')
      session.expect('key=.*')

      request_key  = session.after.decode('utf-8').split()[0].split('=')[1]
      signature    = (request_key + product_key).encode('utf-8')
      signature    = hashlib.sha1(signature).hexdigest()
      response_key = product_key.split('-')[0] + '-' + signature

      session.sendline('READY key=' + response_key)
      session.expect('AUTH.*')
      session.sendline('USERDATA [{"gender": "1"}, {"age": "3"}]')
    except (pexpect.TIMEOUT, pexpect.EOF):
      self.notify('error')
      self.stop_acestream()

    try:
      session.timeout = 30
      session.sendline('START PID ' + pid + ' 0')
      session.expect('http://.*')

      self.session = session
      self.url     = session.after.decode('utf-8').split()[0]
      self.notify('playing')
    except (pexpect.TIMEOUT, pexpect.EOF):
      self.notify('unavailable')
      self.stop_acestream()
