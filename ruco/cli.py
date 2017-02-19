import click
import os
import pytz
import shlex
import sys
import threading
import time
import traceback

from tabulate import tabulate
from websocket._exceptions \
  import WebSocketConnectionClosedException \
  as WebSocketClosedError

from . import clicker
from . import bits
from .bits import out, err, dbg, attrs, loads, dumps, spin
from .service import RustService

rc = attrs(
  address=None,
  port=28016,
  password=None,
  connect_timeout=15,
  response_timeout=5,
  console_log_count=45,
  chat_log_count=45,
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

  - name: rcon
    help: Send a command to the server

    options:

      - name: -q --quiet
        help: Don't wait for a response after sending the command
        is_flag: yes

    arguments:

      - name: command
        nargs: -1
        required: yes

  - name: players
    help: Show connected players

  - name: console
    help: Print console log

    options:

      - name: -f --follow
        help: Follow console log until interrupted
        is_flag: yes

      - name: -n --count
        help: Show a number of lines from the end, default {console_log_count}
        type: int
        default: {console_log_count}

  - name: chat
    help: Print chat log

    options:

      - name: -f --follow
        help: Follow chat log until interrupted
        is_flag: yes

      - name: -n --count
        help: Scan a number of lines from the end for chat messages, default {chat_log_count}
        type: int
        default: {chat_log_count}

  - name: say
    help: Send a chat message to players

    arguments:

      - name: message
        nargs: -1
        required: yes

""".format(**rc)

class RucoException(Exception): pass
class ConnectTimeoutError(RucoException): pass
class ResponseTimeoutError(RucoException): pass

def exit(status=0):
  s = rc.service
  if s:
    on_error in s.on_error and s.on_error.remove(on_error)
    s.connected and s.disconnect()
  # This function could be called by threads other than main, so use os._exit
  os._exit(status)
  #sys.exit(status)

def error(exc_info):
  if isinstance(exc_info, Exception):
    exc_info = bits.make_exc_info(exc_info)
  if rc.debug:
    dbg("".join(traceback.format_exception(*exc_info)))
  else:
    err("%s: %s" % (exc_info[1].__class__.__name__, exc_info[1]))
  exit(-1)

def on_error(svc, exc_info):
  error(exc_info)

# FIXME I'm tired and this is awful:

def start_death_clock(name, timeout, extype=None):
  def on_timeout():
    threading.currentThread().setName("<%s>" % name)
    bits.trace(enabled=rc.trace, filt=rc.trace_filter)
    extype and error(extype("Timed out")) or exit()
  t = getattr(start_death_clock, "timer", None)
  if t:
    t.cancel()
  t = start_death_clock.timer = threading.Timer(timeout, on_timeout)
  t.start()

def stop_timer():
  t = getattr(start_death_clock, "timer", None)
  if t:
    t.cancel()
    start_death_clock.timer = None

def start_connect_timer(extype=ConnectTimeoutError):
  start_death_clock("[connect timer]", rc.connect_timeout, extype)

def start_response_timer(extype=ResponseTimeoutError):
  start_death_clock("[response timer]", rc.response_timeout, extype)

# FIXME End awful

def call(f, *args, **kwargs):
  try:
    return f(*args, **kwargs)
  except SystemExit:
    raise
  except KeyboardInterrupt:
    exit()
  except:
    error(sys.exc_info())

def connect(on_connect):
  def on_connect_cancel_timer(svc):
    stop_timer()
  s = rc.service = RustService(
    rc.address,
    rc.port,
    rc.password,
    dump=rc.dump
  )
  s.on_connect.append(on_connect_cancel_timer)
  s.on_connect.append(on_connect)
  start_connect_timer()
  s.connect()

def display(msg):
  if rc.dump:
    # The service will dump all messages in dump mode
    return
  stamp = time.strftime("%H:%M:%S", time.localtime(msg.get("Time")))
  type = "Type" in msg and msg.Type and "[%s] " % msg.Type or ""
  text = "%s %s%s" % (stamp, type, msg.Message)
  if "Username" in msg:
    text = "%s <%s> %s" % (stamp, msg.Username, msg.Message)
  else:
    try:
      text = "%s %s" % (stamp, dumps(loads(msg.Message), indent=4))
    except:
      pass
  out(text)

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

def ruco_rcon(quiet, command):
  timer_reset = attrs(value=False)
  def on_message_send(svc, msg):
    exit()
  def on_command_response(svc, msg):
    display(msg)
    if timer_reset.value is False:
      start_response_timer(extype=None)
      timer_reset.value = True
  def on_connect(svc):
    if quiet:
      svc.on_message_send.append(on_message_send)
    else:
      start_response_timer()
    svc.request(" ".join(command), on_command_response)
  call(connect, on_connect)

def ruco_players():
  def on_playerlist_response(svc, msg):
    players = loads(msg.Message)
    if not players:
      out("No players connected.")
      exit()
    headers = [
      "Name",
      "Steam ID",
      "Ping",
      "Address",
      "Connected",
      "Health",
      "Violation",
    ]
    players = (
      (
        player.DisplayName,
        player.SteamID,
        player.Ping,
        player.Address,
        bits.format_seconds(player.ConnectedSeconds),
        player.Health,
        player.VoiationLevel,
      ) for player in players
    )
    out(tabulate(players, headers=headers))
    exit()
  def on_connect(svc):
    svc.request("playerlist", on_playerlist_response)
  call(connect, on_connect)

def _ruco_log(follow, count, cmd, filt=None):
  def on_message_recv(svc, msg):
    if not filt or not filt(msg):
      display(msg)
  def on_tail_response(svc, msg):
    logs = loads(msg.Message)
    if len(logs) == 0:
      print("No messages available.")
    else:
      for log in logs:
        display(log)
    if follow:
      svc.on_message_recv.append(on_message_recv)
    else:
      exit()
  def on_connect(svc):
    svc.request("%s %d" % (cmd, count), on_tail_response)
  call(connect, on_connect)

def ruco_console(follow, count):
  _ruco_log(follow, count, "console.tail")

def ruco_chat(follow, count):
  filt = lambda m: "Type" in m and m.Type != "Chat"
  _ruco_log(follow, count, "chat.tail", filt)

def ruco_say(message):
  def on_message_send(svc, msg):
    exit()
  def on_connect(svc):
    svc.on_message_send.append(on_message_send)
    svc.command("say %s" % " ".join(message))
  call(connect, on_connect)

def get_rc_path():
  envrc = "RUCO_RC" in os.environ and os.environ["RUCO_RC"] or None
  paths = envrc and (envrc,) + rc.rc_paths or rc.rc_paths
  for p in paths:
    if os.path.isfile(p):
      return p
  return None

def read_rc(path):
  with open(path) as rc:
    return dict(token.split("=") for token in shlex.split(rc.read()))

def load_rc():
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
  # environment variable
  bits.trace(enabled=rc.trace, filt=rc.trace_filter)
  cli = clicker.Cli()
  cli.loads(cli_spec)
  cli.run(env=globals(), require_groups=True)

if __name__ == "__main__":
  main()
