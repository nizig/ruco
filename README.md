# ruco

Rust (by Facepunch Studios) rcon API and shell utility for Python.

**ru**st **co**nsole

## Contents

- [Installation](#installation)
- [Utility Built-In Help](#utility-built-in-help)
- [Utility Examples](#utility-examples)
- [Utility Configuration Example](#utility-configuration-example)
- [Managing Multiple Servers](#managing-multiple-servers)
- [API Usage Example](#api-usage-example)

## Installation

Only Python3 is supported. I will port it to Python2 eventually. Install with pip. For example, on Debian systems:

    # pip3 install ruco

## Utility Built-in Help

Every command provides a `--help` flag, which describes every sub-command and flag.

## Utility Examples

Show connected players:

    $ ruco --address narwhal.eckso.io --password mySocratesNote players
    <... or with short options ...>
    $ ruco -a narwhal.eckso.io -p mySocratesNote players
    <... or with settings from the config file ...>
    $ ruco players
    Name                      Steam ID    Ping  Address                 Connected    Health   Violation
    ---------------  -----------------  ------  --------------------  -----------  --------  ----------
    Stale Cheese     76561000000000001      22  1.2.3.4:59441              1h7m3s    91.265           0
    Joseph Mama      76561000000000002      68  1.2.3.5:54338            2h48m48s    66.029           0
    Billy Bass       76561000000000003     128  1.2.3.6:48119             0h3m16s    35.071           0
    $

Issue rcon commands, and wait for a response message from the server:

    $ ruco -a narwhal.eckso.io -p mySocratesNote rcon readcfg
    User 'exo(76561000000000004)' added to group: admin
    Server Config Loaded
    $

    $ ruco -a narwhal.eckso.io -p mySocratesNote rcon reload Build
    Unloaded plugin Build v1.1.7 by Reneb & NoGrod
    Loaded plugin Build v1.1.7 by Reneb & NoGrod
    $

Issue rcon commands without waiting for a server response:

    $ ruco -a narwhal.eckso.io -p mySocratesNote rcon -q readcfg
    $ ruco -a narwhal.eckso.io -p mySocratesNote rcon -q reload Build
    $

Show console output:

    $ ruco -a narwhal.eckso.io -p mySocratesNote tail
    Unloaded plugin Build v1.1.7 by Reneb & NoGrod
    Loaded plugin Build v1.1.7 by Reneb & NoGrod
    Saved 55,481 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.08).
    Saving complete
    Saved 55,480 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    Saved 55,472 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    Saved 55,471 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    [Updater] Couldn't get the latest version of plugin Copy Paste
    [Updater] Couldn't get the latest version of plugin PumpsOut
    [Updater]
    Following plugins are outdated:

    # FancyDrop | Installed: 2.6.6 - Latest: 2.6.7 | http://oxidemod.org/plugins/1934/

    # QuickSort | Installed: 1.0.4 - Latest: 1.0.5 | http://oxidemod.org/plugins/1263/

    # Stack Size Controller | Installed: 1.9.3 - Latest: 1.9.4 | http://oxidemod.org/plugins/2320/

    Saved 55,475 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    Saved 55,474 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.08).
    Saving complete
    Saved 55,480 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    Saved 55,479 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    Unloaded plugin Build v1.1.7 by Reneb & NoGrod
    Loaded plugin Build v1.1.7 by Reneb & NoGrod
    Unloaded plugin Build v1.1.7 by Reneb & NoGrod
    Loaded plugin Build v1.1.7 by Reneb & NoGrod
    [FancyDrop] Timed Airdrop skipped, not enough Players
    [FancyDrop] Next timed Airdrop in 22 minutes
    Saved 55,472 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    $

Show the last 5 lines of console output:

    $ ruco -a narwhal.eckso.io tail -n 5
    [FancyDrop] Next timed Airdrop in 22 minutes
    Saved 55,472 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    Saved 55,463 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    $

Show the last 5 lines of console output, but stay connected, showing future server output in real time.    

    $ ruco -a narwhal.eckso.io tail -n 5 -f
    [FancyDrop] Next timed Airdrop in 22 minutes
    Saved 55,472 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    Saved 55,463 ents, serialization(0.01), write(0.03), disk(0.01) totalstall(0.07).
    Saving complete
    <... additional output would appear here until interrupted ...>
    ^C
    $

## Utility Configuration Example

There are three ways to configure the shell utility. In order of precedence:

    1. Command-line flags
    2. Environment variables
    3. Config file

### Flags

Use `ruco --help` to get information about command line flags.

### Environment Variables

    $ export RUCO_ADDRESS="my.rust.server.com"
    $ export RUCO_PORT="28016"
    $ export RUCO_PASSWORD="mySocratesNote"

### Config File

The config file should be placed at `~/.config/rucorc` or `~/.rucorc`. Example:

    RUCO_ADDRESS="my.rust.server.com"
    RUCO_PORT="28016"
    RUCO_PASSWORD="mySocratesNote"

### Easy Peasy

Now we can invoke ruco without passing a bunch of command-line flags. Here are the examples from the above with `RUCO_ADDRESS` and `RUCO_PASSWORD` set via a config file or environment variables:

    $ ruco players
    $ ruco rcon readcfg
    $ ruco rcon reload Build
    $ ruco rcon -q readcfg
    $ ruco rcon -q reload Build
    $ ruco tail
    $ ruco tail -n 5
    $ ruco tail -n 5 -f

## Managing multiple servers


There are two ways to manage multiple servers.

- Multiple bash environments
- Multiple config files

### Multiple bash environments

    # Create a directory for your environments.
    $ mkdir ~/servers

    # Create the first server's environment file.
    cat <<EOT >~/servers/server1.sh
    export RUST_ADDRESS="server1.rustonia.com"
    export RUST_PASSWORD="boffermatic"
    EOT

    # Create the second server's environment file.
    cat <<EOT >~/servers/server2.sh
    export RUST_ADDRESS="server2.rustonia.com"
    export RUST_PASSWORD="rubarbell"
    EOT

    # Run commands against server1
    $ . ~/server/server1.sh
    $ ruco players
    $ ruco tail -n 5

    # Run commands against server2
    $ . ~/server/server2.sh
    $ ruco rcon reload FancyCopter
    $ ruco rcon -q spawn.fill_populations

### Multiple Config Files

    # Create a directory for your config files.
    $ mkdir ~/servers

    # Create the first server's config file.
    $ cat <<EOT >~/servers/server1.rucorc
    RUST_ADDRESS="server1.rustastic.com"
    RUST_PASSWORD="foobarlicious"
    EOT

    # Create the second server's config file.
    $ cat <<EOT >~/servers/server2.rucorc
    RUST_ADDRESS="server2.rustastic.com"
    RUST_PASSWORD="jammityjamjam"
    EOT

    <... either ...>

    # Run commands against server1
    $ export RUCO_RC=~/servers/server1.rucorc
    $ ruco players
    $ ruco tail -n 5

    # Run commands against server2
    $ export RUCO_RC=~/servers/server2.rucorc
    $ ruco rcon reload FancyCopter
    $ ruco rcon -q spawn.fill_populations

    <... or ...>

    # Run commands against server1
    $ RUCO_RC=~/servers/server1.rucorc ruco players
    $ RUCO_RC=~/servers/server1.rucorc ruco tail -n 5

    # Run commands against server2
    $ RUCO_RC=~/servers/server2.rucorc ruco rcon reload FancyCopter
    $ RUCO_RC=~/servers/server2.rucorc ruco rcon spawn.fill_populations

## API Usage Example

### Event loop

    import ruco
    import time
    import traceback

    from ruco.bits import loads
    from ruco.service import RustService

    def on_tail_response(service, message):
      logs = loads(message.Message)
      if logs:
        for log in logs:
          print("tail:", log.Message)
      else:
        print("No console logs available")

    def on_playerlist_response(service, message):
      players = loads(message.Message)
      if players:
        for player in players:
          print("Player:", player.DisplayName, "- SteamID:", player.SteamID)
      else:
        print("No players connected")
      service.disconnect()

    def on_message_recv(service, message):
      print("Console message: %s" % message.Message)

    def on_error(service, error):
      traceback.print_exception(*error)

    def on_disconnect(service):
      print("Disconnected from rust server")

    def on_connect(service):
      service.on_message_recv.append(on_message_recv)
      service.on_error.append(on_error)
      service.on_disconnect.append(on_disconnect)
      service.request("tail 10", on_tail_response)
      service.request("playerlist", on_playerlist_response)

    def main():
      rust = RustService("my.rust.server.com", 28016, "myPassword")
      rust.on_connect.append(on_connect)
      rust.connect()

    if __name__ == "__main__":
      main()


### Threads

    import ruco
    import time
    import threading
    import traceback

    from ruco.bits import loads
    from ruco.service import RustServiceThread

    tail_event = threading.Event()

    def on_tail_response(service, message):
      logs = loads(message.Message)
      if logs:
        for log in logs:
          print("tail:", log.Message)
      else:
        print("No console logs available")
      tail_event.set()

    playerlist_event = threading.Event()

    def on_playerlist_response(service, message):
      players = loads(message.Message)
      if players:
        for player in players:
          print("Player:", player.DisplayName, "- SteamID:", player.SteamID)
      else:
        print("No players connected")
      playerlist_event.set()

    def on_connect(service):
      service.request("console.tail 10", on_tail_response)
      service.request("playerlist", on_playerlist_response)

    def on_message_recv(service, message):
      print("Console message: %s" % message.Message)

    def on_error(service, error):
      traceback.print_exception(*error)

    def on_disconnect(service):
      print("Disconnected from rust server")

    def main():
      rust = RustServiceThread("my.rust.server.com", 28016, "myPassword")

      rust.on_connect.append(on_connect)
      rust.on_message_recv.append(on_message_recv)
      rust.on_error.append(on_error)
      rust.on_disconnect.append(on_disconnect)

      rust.connect()

      tail_event.wait()
      playerlist_event.wait()

      rust.disconnect()

    if __name__ == "__main__":
      main()

### Threads with Comments

    import ruco
    import time
    import threading
    import traceback

    from ruco.bits import loads
    from ruco.service import RustServiceThread

    # Event used to notify main thread that the tail response was received.
    tail_event = threading.Event()

    # Handle the response for the 'tail' command.
    def on_tail_response(service, message):
      logs = loads(message.Message)
      if logs:
        for log in logs:
          print("tail:", log.Message)
      else:
        print("No console logs available")
      tail_event.set()

    # Event used to notify main thread that the playerlist response was received.
    playerlist_event = threading.Event()

    # Handle the response for the 'playerlist' command.
    def on_playerlist_response(service, message):
      players = loads(message.Message)
      if players:
        for player in players:
          print("Player:", player.DisplayName, "- SteamID:", player.SteamID)
      else:
        print("No players connected")
      playerlist_event.set()

    # on_connect callbacks are called after successful handshake with the rust
    # server.
    def on_connect(service):
      # Send the 'tail' command to get the last few lines of console output. Send
      # the command request along with a callback to handle the command's response.
      service.request("console.tail 10", on_tail_response)

      # Print the list of connected players. Send the command request along with
      # the callback to handle the command's response.
      service.request("playerlist", on_playerlist_response)

    # on_message_recv callbacks are called when a message is received that is
    # not a response to a command - i.e., they're console messages.
    def on_message_recv(service, message):
      print("Console message: %s" % message.Message)

    # on_error callbacks are called when an error occurs in the websocket event
    # loop. The websocket will be explicitly closed after on_error handlers are
    # called, but, depending on the error, may already be closed when handlers are
    # called.
    def on_error(service, error):
      traceback.print_exception(*error)

    # on_disconnect will be called after we have been disconnected from the rust
    # server.
    def on_disconnect(service):
      print("Disconnected from rust server")

    def main():
      # RustService is the non-threaded version.
      rust = RustServiceThread("my.rust.server.com", 28016, "myPassword")

      # Add handlers before connecting.
      rust.on_connect.append(on_connect)
      rust.on_message_recv.append(on_message_recv)
      rust.on_error.append(on_error)
      rust.on_disconnect.append(on_disconnect)

      # Connect, and the handlers will take care of the rest. In the non-threaded
      # version, this will return only after disconnect() is called.
      rust.connect()

      # Wait for the message handlers to receive their responses.
      tail_event.wait()
      playerlist_event.wait()

      # Or to stay connected and listen to console output, comment out the last
      # two lines, and uncomment this:
      # rust.join()

      rust.disconnect()

    if __name__ == "__main__":
      main()
