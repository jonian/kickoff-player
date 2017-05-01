import time
import socket
import threading
import hashlib
import pexpect
import psutil

from subprocess import PIPE


class StreamHandler(object):
  """Handler for acestream and sopcast streams"""

  def __init__(self, player):
    self.player    = player
    self.acestream = None
    self.sopcast   = None
    self.url       = None
    self.session   = None

  def notify(self, message):
    """Notify player on stream status changes"""

    messages = {
      'starting': 'Starting stream engine...',
      'running': 'Stream engine running...',
      'error': 'Stream engine error!',
      'playing': 'Playing',
      'waiting': 'Waiting for response...',
      'unavailable': 'Stream unavailable!'
    }
    message = messages[message]
    self.player.update_status(message)

  def open(self, url):
    """Opean stream in a new thread"""

    self.player.loading = True
    thread = threading.Thread(target=self.open_stream, args=[url])
    thread.start()

  def close(self):
    """Close all streaming engines"""

    self.stop_acestream()
    self.stop_sopcast()

  def open_stream(self, url):
    """Open stream url and start player"""

    self.player.close()
    self.notify('starting')

    if url.startswith('acestream://'):
      self.start_acestream(url)

    if url.startswith('sop://'):
      self.start_sopcast(url)

    if not self.url is None:
      self.player.url = self.url
      self.player.open(self.url)

    self.player.loading = False

  def start_acestream(self, url):
    """Start acestream engine"""

    engine = '/usr/bin/acestreamengine'
    client = '--client-console'

    self.stop_acestream()

    try:
      self.acestream = psutil.Popen([engine, client], stdout=PIPE)
      self.notify('running')
      time.sleep(5)
    except FileNotFoundError:
      self.notify('error')
      self.stop_acestream()

    pid = url.split('://')[1]
    self.start_acestream_session(pid)

  def stop_acestream(self):
    """Stop acestream engine"""

    if not self.acestream is None:
      self.acestream.kill()

    if not self.session is None:
      self.session.close()

  def start_acestream_session(self, pid):
    """Handle acestream engine authentication"""

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

  def start_sopcast(self, url):
    """Start sopcast engine"""

    eng = '/usr/bin/sp-sc'
    lpo = '3000'
    ppo = '3001'

    self.stop_sopcast()

    try:
      self.sopcast = psutil.Popen([eng, url, lpo, ppo], stdout=PIPE)
      self.notify('running')
      time.sleep(5)
    except FileNotFoundError:
      self.notify('error')
      self.stop_sopcast()

    self.start_sopcast_session(ppo)

  def stop_sopcast(self):
    """Stop sopcast engine"""

    if not self.sopcast is None:
      self.sopcast.kill()

    if not self.session is None:
      self.session.close()

  def start_sopcast_session(self, port):
    """Handle sopcast channel availability"""

    session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.notify('waiting')

    retries, timeout, success = [6, 5, False]

    while success is False and retries > 0:
      try:
        session.connect(('localhost', int(port)))
        session.send(b'HELLOBG')
        session.recv(1024)
        session.close()
        success = True
      except socket.error:
        time.sleep(timeout)
        retries = retries - 1

    if success is True:
      self.session = session
      self.url     = 'http://localhost:' + port + '/sopcast.mp4'
      self.notify('playing')
    else:
      self.notify('unavailable')
      self.stop_sopcast()
