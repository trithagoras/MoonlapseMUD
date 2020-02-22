# ![MoonlapseMUD Logo](https://i.imgur.com/Ie6YZ4v.png)

Welcome to Moonlapse MUD: an open-source, multi-user dungeon designed to play directly in any terminal.

# How to play

Ensure Python 3.4 is installed on your machine and your terminal has a resolution at least 46x106 characters.

Simply download the latest client either using the download links above or by running the following command in your terminal:

```bash
wget https://github.com/trithagoras/MoonlapseMUD/releases/download/v0.2/Client.zip
```

Unzip the archive either using a GUI archiving tool (typically integrated with your file manager) or by running:

```bash
unzip Client.zip
```

Now simply run the client package using python 3:

```
python3 moonlapse
```

or alternatively if your OS uses python3 by default:

```bash
python moonlapse
```

## Note for Windows users:
Windows does not ship with curses, which is necessary for the client code to run. To install curses for Python, install the windows-curses library by opening a terminal and entering:

```powershell
pip install windows-curses
```

If that doesn't work because you do not have pip installed, follow these steps to install pip first and try again:
1. Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) to a folder on your computer
2. Open a terminal and navigate to the folder containing get-pip.py
3. Run the following command: `python get-pip.py`

For more information, visit https://moonlapse.net
