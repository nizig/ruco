ruco
====
Rust (by Facepunch Studios) rcon API and shell utility for Python.

**ru**st **co**nsole

Installation
------------
Only Python3 is supported. I will port it to Python2 eventually. Install with pip. For example, on Debian systems:

    # pip3 install ruco

Built-in Help
-------------
Every command provides a `--help` flag, which describes every sub-command and flag.

Shell Utility Example
---------------------
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

Shell Utility Configuration Example
-----------------------------------
There are three ways to configure the shell utility. In order of precedence:

    1. Command-line flags
    2. Environment variables
    3. Config file

**Flags**

Use `ruco --help` to get information about command line flags.

**Environment Variables**

    $ export RUCO_ADDRESS="my.rust.server.com"
    $ export RUCO_PORT="28016"
    $ export RUCO_PASSWORD="mySocratesNote"

**Config File**

The config file should be placed at `~/.config/rucorc` or `~/.rucorc`. Example:

    RUCO_ADDRESS="my.rust.server.com"
    RUCO_PORT="28016"
    RUCO_PASSWORD="mySocratesNote"

**Easy Peasy**

Now we can invoke ruco without passing a bunch of command-line flags. Here are the examples from the above with `RUCO_ADDRESS` and `RUCO_PASSWORD` set via a config file or environment variables:

    $ ruco players
    $ ruco rcon readcfg
    $ ruco rcon reload Build
    $ ruco rcon -q readcfg
    $ ruco rcon -q reload Build
    $ ruco tail
    $ ruco tail -n 5
    $ ruco tail -n 5 -f

Managing multiple servers
-------------------------

There are two ways to manage multiple servers.

- Multiple bash environments
- Multiple config files

**Multiple bash environments**

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

**Multiple Config Files**

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

API Usage Example
-----------------
Forthcoming...

