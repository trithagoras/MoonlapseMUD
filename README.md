# ![MoonlapseMUD Logo](https://i.imgur.com/Ie6YZ4v.png)
![Deploy MoonlapseMUD on production server](https://github.com/trithagoras/MoonlapseMUD/workflows/Deploy%20MoonlapseMUD%20on%20production%20server/badge.svg)

Welcome to MoonlapseMUD: an open-source, multi-user dungeon designed to play directly in any terminal.

# How to play

Ensure Python 3.4 is installed on your machine and your terminal has a resolution at least 41x106 characters.

Simply download the latest client either using the download links above or by running the following command in your terminal:

```shell
curl -L https://github.com/trithagoras/MoonlapseMUD/releases/download/v0.3/Client.tar -o Client.tar
```

Unzip the archive either using a GUI archiving tool (typically integrated with your file manager) or by running:

```shell
tar xvf Client.tar
```

Now simply run the client package using Python 3:

```shell
python3 MoonlapseMUD/client
```

> *or alternatively if your OS uses python3 by default:*
>
> ```shell
> python MoonlapseMUD/client
> ```

## Note for Windows users

Windows does not ship with curses, which is necessary for the client code to run. To install curses for Python, install the windows-curses library by opening a terminal and entering:

```powershell
pip install windows-curses
```

> *If that doesn't work, try using `pip3` instead of pip. If that still doesn't work, you might not have pip installed so follow these steps to install pip first and try again:*
>
> 1. *Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) to a folder on your computer*
> 2. *Open a terminal and navigate to the folder containing get-pip.py*
> 3. *Run the following command: `python get-pip.py`*

## For the sake of the heavens

Please do not use any real usernames or passwords when registering for an account. Make sure your credentials are specific to MoonlapseMUD.

Until we implement better security (roadmap for version 0.4), all passwords are:

* sent over the internet unencrypted,
* stored in our database as as plaintext (not hashed),
* even displayed in plaintext in the client window.

When this changes, expect to see a note in the [dev logs](https://moonlapse.net/blog) and this section will be removed from the front page.

- - -

Thanks for checking out the game, cheers!

For more information, visit https://moonlapse.net
