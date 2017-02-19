import os
import sys
import threading
import time
import websocket

from distutils.util import strtobool

from . import bits
from .bits import out, err, dbg, spam, attrs, loads, dumps, dispatch

DEBUG_WEBSOCKET = strtobool(os.environ.get("DEBUG_WEBSOCKET", "0"))

class RustService(object):

  REQUEST_EXPIRY = 300

  def __init__(self, address, port, password, dump=False):
    super().__init__()
    self.address = address
    self.port = port
    self.password = password
    self.dump = dump
    self.requests = {}
    self.socket = None
    self.on_connect = []
    self.on_disconnect = []
    self.on_message_recv = []
    self.on_message_send = []
    self.on_error = []
    self.on_stale_cleanup = []
    self._identifier = 1001

  @property
  def identifier(self):
    if self._identifier > 0x7FFFFFFF:
      self._identifier = 1001
    id = self._identifier
    self._identifier += 1
    return id

  def _on_message_recv(self, msg):
    if self.dump:
      err("RECV", dumps(msg))
    id = msg.Identifier
    if id > 1000:
      request = self.requests.get(id)
      if request is not None:
        msg.request = request
        dispatch((request.callback,), self, msg)
        return
      else:
        spam("Received response for unknown request: %s" % msg)
    dispatch(self.on_message_recv, self, msg)

  def _on_connect(self, socket):
    self.socket = socket
    dispatch(self.on_connect, self)

  def _on_error(self, socket, error):
    dispatch(self.on_error, self, bits.make_exc_info(error))
    try:
      # FIXME hmm...
      self.socket.on_close = None
      self.socket.close()
    except SystemExit:
      raise
    except:
      pass
    socket = None
    self.requests.clear()

  def _on_disconnect(self, socket):
    self.socket = None
    self.requests.clear()
    dispatch(self.on_disconnect, self)

  def _send(self, msg):
    if self.dump:
      err("SEND", dumps(msg))
    self.socket.send(dumps(msg))
    dispatch(self.on_message_send, self, msg)

  def _expire_requests(self):
    if len(self.requests) == 0:
      return 0
    now = time.time()
    stale = [
      id for id, request in self.requests.items()
      if (now - request.time) > self.REQUEST_EXPIRY
    ]
    for id in stale:
      del self.requests[id]
    dispatch(self.on_stale_cleanup, self, stale)
    spam("Expired %d requests" % len(stale))
    return stale

  @property
  def connected(self):
    return self.socket is not None

  def connect(self):
    def on_message(s, m):
      self._on_message_recv(loads(m))
    def on_pong(*a, **kw):
      self._expire_requests()
    socket = None
    try:
      websocket.enableTrace(DEBUG_WEBSOCKET)
      socket = websocket.WebSocketApp(
        "ws://%s:%d/%s" % (self.address, self.port, self.password),
        on_open = self._on_connect,
        on_close = self._on_disconnect,
        on_message = on_message,
        on_error = self._on_error,
        on_pong = on_pong
      )
      socket.run_forever()
    except SystemExit:
      raise
    except KeyboardInterrupt:
      self._on_error(socket, sys.exc_info())
      return
    except:
      self._on_error(socket, sys.exc_info())
      raise

  def disconnect(self):
    self.socket.close()

  def command(self, msg, id):
    if id is None:
      id = -1
    self._send({
      "Identifier": id,
      "Message": msg,
      "Name": "WebRcon",
    })

  def request(self, msg, cb):
    self._expire_requests()
    id = self.identifier
    assert(id not in self.requests)
    self.requests[id] = attrs(
      callback=cb,
      time=time.time(),
    )
    try:
      self.command(msg, id)
    except SystemExit:
      raise
    except:
      del self.requests[id]
      raise

class RustServiceThread(RustService):

  def __init__(self, *a, name="[rust]", trace=False, trace_filter=True, **kw):
    super().__init__(*a, **kw)
    self.name = name
    self.trace = trace
    self.trace_filter = trace_filter
    self.thread = None
    self.error = None

  def connect(self):
    s = super()
    def run():
      bits.trace(self.trace, filt=self.trace_filter)
      try:
        s.connect()
      except SystemExit:
        raise
      except:
        self.error = sys.exc_info()
        #self._on_error(self.socket, self.error)
      finally:
        self.thread = None
    self.thread = threading.Thread(target=run, name=self.name)
    self.thread.start()

  def disconnect(self, wait=0):
    super().disconnect()
    return self.join(wait)

  def join(self, timeout=-1):
    try:
      if timeout == 0:
        return self.connected
      elif timeout < 0:
        self.thread.join()
        return True
      else:
        self.thread.join(timeout)
        return self.connected
    except AttributeError:
      return self.connected
