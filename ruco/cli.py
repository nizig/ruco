import click
import os
import shlex
import sys
import time
import threading
import traceback

from tabulate import tabulate
from websocket._exceptions \
  import WebSocketConnectionClosedException \
  as WebSocketClosedError

from . import clicker
from . import bits
from .bits import out, err, dbg, attrs, loads, dumps, spin
from .service import RustServiceThread

rc = attrs(
  address=None,
  port=28016,
  password=None,
  connect_timeout=20,
  response_timeout=3,
  tail_count=30,
  debug=1,
  dump=False,
  trace=False,
  trace_filter=1,
  service=None,
  rc_path=None,
  rc_paths=(
    os.path.join(os.path.expanduser("~"), ".config", "rucorc"),
    os.path.join(os.path.expanduser("~"), ".rucorc"),
    "rucorc",
    ".rucorc",
  ),
)

cli_spec = """

name: ruco

help: |
  Interact with a Rust game server admin console

options:

  - name: -a --address
    help: Server IP address or host name
    type: str
    required: yes

  - name: --port
    help: Server port, default 28016
    type: int
    default: {port}

  - name: -p --password
    help: Server password; use 'ask' to enter via a prompt
    type: str
    required: yes

  - name: -c --connect-timeout
    help: Connection timeout, default {connect_timeout}
    type: int
    default: {connect_timeout}

  - name: -r --response-timeout
    help: Command response timeout, default {response_timeout}
    type: int
    default: {response_timeout}

  - name: --debug
    help: "0: error and warning, 1: debug, 2: spam, default {debug}"
    type: int
    default: {debug}

  - name: --dump
    help: Dump messages
    is_flag: yes

  - name: --trace
    help: Trace function/method calls
    is_flag: yes

  - name: --trace-filter
    help: "0: trace all calls, 1: trace ruco calls only, default: {trace_filter}"
    type: int
    default: {trace_filter}

commands:

  - name: tail
    help: Print console output to the screen

    options:

      - name: -f --follow
        help: Follow output until interrupted
        is_flag: yes

      - name: -n --count
        help: Show a number of lines, starting from the end, default 15
        type: int
        default: {tail_count}

  - name: rcon
    help: Send a command to the server

    options:

      - name: -q --quiet
        help: Don't wait for a response after sending the command.
        is_flag: yes

    arguments:

      - name: command
        nargs: -1
        required: yes

  - name: players
    help: Show connected players


""".format(**rc)

class RucoException(Exception): pass
class ConnectTimeoutError(RucoException): pass
class ResponseTimeoutError(RucoException): pass

def exit(status=0):
  s = rc.service
  if s:
    on_error in s.on_error and s.on_error.remove(on_error)
    s.connected and s.disconnect()
    s.join()
  os._exit(status)

def error(exc_info):
  if isinstance(exc_info, Exception):
    exc_info = bits.make_exc_info(exc_info)
  if rc.debug:
    dbg(traceback.format_exception(*exc_info))
  else:
    err(exc_info[1])
  exit(-1)

def on_error(svc, exc_info):
  error(exc_info)

done = threading.Event()

def wait_for_connect():
  if not done.wait(rc.connect_timeout):
    error(ConnectTimeoutError("Timed out waiting for connect"))
  done.clear()

def wait_for_disconnect():
  if rc.service:
    spin(-1, 0.4, lambda: not rc.service.connected)

def wait_for_response():
  if not done.wait(rc.response_timeout):
    error(ResponseTimeoutError("Timed out waiting for command response"))
  done.clear()

def notify():
  done.set()

def get_service():
  s = rc.service
  if s:
    return s
  def on_connect(svc):
    notify()
  s = RustServiceThread(
    rc.address,
    rc.port,
    rc.password,
    trace=rc.trace,
    trace_filter=rc.trace_filter,
    dump=rc.dump
  )
  s.on_connect.append(on_connect)
  s.on_error.append(on_error)
  s.connect()
  wait_for_connect()
  s.on_connect.remove(on_connect)
  rc.service = s
  return s

def call(f, *args, **kwargs):
  try:
    return f(*args, **kwargs)
  except SystemExit:
    raise
  except KeyboardInterrupt:
    exit()
  except:
    error(sys.exc_info())

def display(msg):
  if rc.dump:
    # The service will dump all messages in dump mode.
    return
  if "time" in msg:
    pass # FIXME
  try:
    out(dumps(loads(msg.Message)))
    return
  except:
    pass
  out(msg.Message)

def ruco(
  address,
  port,
  password,
  connect_timeout,
  response_timeout,
  debug,
  dump,
  trace,
  trace_filter
):
  def _ruco():
    rc.address = address
    rc.port = port
    if password is "ask":
      raise Exception("not implemented") # FIXME
    rc.password = password
    nonlocal debug
    rc.debug = debug in (0, 1, 2) and debug or 0
    rc.dump = dump
    rc.trace = trace
    rc.trace_filter = trace_filter in (0, 1) and trace_filter or 1
    bits.trace(enabled=trace, filt=trace_filter)
  call(_ruco)

def ruco_tail(follow, count):
  def _ruco_tail():
    def on_message_recv(svc, msg):
      display(msg)
    def on_tail_response(svc, msg):
      logs = loads(msg.Message)
      for log in logs:
        on_message_recv(svc, log)
      notify()
    s = get_service()
    s.request("console.tail %d" % count, on_tail_response)
    wait_for_response()
    if follow:
      s.on_message_recv.append(on_message_recv)
      wait_for_disconnect()
    else:
      exit()
  call(_ruco_tail)

def ruco_rcon(quiet, command):
  def _ruco_rcon():
    def timeout():
      threading.currentThread().setName("<wait>")
      bits.trace(enabled=rc.trace, filt=rc.trace_filter)
      exit()
    def on_response(svc, msg):
      if msg.Message:
        display(msg)
    def on_message_send(svc, msg):
      exit()
    s = get_service()
    if quiet:
      s.on_message_send.append(on_message_send)
    else:
      s.on_message_recv.append(on_response)
      t = threading.Timer(rc.response_timeout, timeout)
      t.start()
    s.request(" ".join(command), on_response)
    wait_for_disconnect()
  call(_ruco_rcon)

def ruco_players():
  def _ruco_players():
    def on_response(svc, msg):
      try:
        players = loads(msg.Message)
        if not players:
          out("No players connected.")
          return
        headers = [
          "Name",
          "Steam ID",
          "Ping",
          "Address",
          "Connected",
          "Health",
          "Violation",
        ]
        def interval(i):
          h, r = divmod(i, 3600)
          m, s = divmod(r, 60)
          return "%sh%sm%ss" % (h, m, s)
        players = (
          (
            player.DisplayName,
            player.SteamID,
            player.Ping,
            player.Address,
            interval(player.ConnectedSeconds),
            player.Health,
            player.VoiationLevel,
          ) for player in players
        )
        out(tabulate(players, headers=headers))
      finally:
        notify()
    get_service().request("playerlist", on_response)
    wait_for_response()
    exit()
  call(_ruco_players)

def load_rc():
  def get_rc_path():
    envrc = (
      "RUCO_RC" in os.environ and os.environ["RUCO_RC"] or
      "RC" in os.environ and os.environ["RC"] or
      None
    )
    paths = envrc and (envrc,) + rc.rc_paths or rc.rc_paths
    for p in paths:
      if os.path.isfile(p):
        return p
    return None
  def read_rc(path):
    with open(path) as rc:
      return dict(token.split("=") for token in shlex.split(rc.read()))
  rc.rc_path = p = get_rc_path()
  if not p:
    return
  try:
    for k, v in read_rc(p).items():
      if k not in os.environ:
        os.environ[k] = v
  except:
    err("%s%sError loading config file: %s" % (
      traceback.format_exc(), os.linesep, p
    ))
    sys.exit(-1)

def main():
  threading.current_thread().setName("<main>")
  load_rc()
  # Start tracing as early as possible when set via the config file or an
  # environment variable.
  bits.trace(enabled=rc.trace, filt=rc.trace_filter)
  cli = clicker.Cli()
  cli.loads(cli_spec)
  cli.run(env=globals(), require_groups=True)

if __name__ == "__main__":
  main()
