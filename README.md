# glassy

Glass-style desktop widgets for Linux: a big clock at the top, a left panel (cat, network speed, weather, uptime) and a right panel (CPU, RAM, disk and battery rings).

![glassy preview](assets/preview.png)

## Install (one command)

Open a terminal and paste:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/pratik11500/glassy/main/install.sh)
```

That's it. The widgets appear right away, and they start by themselves every time you log in.

The installer asks before using `sudo` (only if some packages are missing). To skip the question, add `-y` at the end of the command.

### Install with git instead

```bash
git clone https://github.com/pratik11500/glassy
cd glassy
./install.sh
```

## What the installer does

1. Installs what the widgets need (Python GTK, psutil, wmctrl, Conky), only if missing
2. Copies the widgets to `~/.local/share/glassy`
3. Installs the two fonts the clock and panels use (Anurati and Ubuntu Sans)
4. Creates a small config file at `~/.config/glassy/config.ini`
5. Adds an autostart entry, so everything loads after every restart or login
6. Starts the widgets

Nothing outside your home folder is changed, except the packages from step 1.

## Works on which Linux?

The installer finds your package manager by itself:

| Family | Examples | Status |
|---|---|---|
| Debian / Ubuntu (`apt`) | Linux Mint, Ubuntu, Pop!_OS, Zorin, Debian | Made on Linux Mint 22.3 |
| Fedora (`dnf`) | Fedora, Nobara | Should work, not tested |
| Arch (`pacman`) | Arch, Manjaro, EndeavourOS | Should work, not tested |
| openSUSE (`zypper`) | Tumbleweed, Leap | Should work, not tested |

Desktops that load the autostart folder work fine: Cinnamon, GNOME, KDE, XFCE, MATE, LXQt.

## Limits (please read)

- **You need X11, not Wayland.** The widgets use `wmctrl` and a Conky desktop window, and these only work on X11. Check yours with:
  ```bash
  echo $XDG_SESSION_TYPE
  ```
  If it says `x11`, you are good. If it says `wayland`, log out, click your name on the login screen, find the small gear or session menu, and choose **Xorg** or **X11**. Then log in and run the installer again.
- **Tiling window managers** (i3, bspwm, sway, Hyprland) ignore the autostart folder. Add this line to your WM config instead: `~/.local/bin/glassy boot`. Wayland-only ones like sway and Hyprland are not supported.
- **Weather needs internet.** With no connection it shows `N/A`. The weather comes from wttr.in and refreshes every 5 minutes.
- **Battery ring:** on a laptop it shows the battery %, and `CHG` while charging. On a desktop PC (no battery) it shows a plug icon and `AC`, meaning "plugged in".
- **Several monitors:** the widgets go on your main (primary) monitor only.
- **Screen size:** the widgets grow or shrink to fit your screen automatically (checked at 1366x768, 1920x1080 and 2560x1440). On a very unusual screen, set the size yourself (see Settings).
- **Not supported:** immutable distros (Fedora Silverblue, SteamOS), Alpine, and systems without a normal package manager.
- **sudo** is needed once, only to install missing packages.

## Commands

```bash
glassy status     # which widgets are running
glassy stop       # stop all widgets
glassy start      # start them
glassy restart    # restart (use this after changing settings)
```

If the command is not found right after install, log out and in once, or use `~/.local/bin/glassy`.

## Settings

Edit `~/.config/glassy/config.ini`, then run `glassy restart`:

```ini
[glassy]
city = Delhi          # city for the weather
label = Delhi, IN     # text shown under the temperature
scale = auto          # "auto" fits your screen, or use a number like 1.25
```

## Something looks wrong?

| Problem | Fix |
|---|---|
| Panels are in the wrong place or on top of windows | You are probably on Wayland. See Limits above. |
| Two clocks | You already had a Conky clock starting at login. Remove the old one (for example `~/.conkyrc` and its autostart entry). |
| Weather shows `N/A` | No internet, or the city name is wrong. Check `config.ini`. |
| Weather icon is a box | Install an emoji font, for example `sudo apt install fonts-noto-color-emoji`. |
| Panels too small or too big | Set `scale` in `config.ini`, then `glassy restart`. |
| A widget does not start | Read `~/.cache/glassy/glassy.log`. |

## Uninstall

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/pratik11500/glassy/main/uninstall.sh)
```

This stops the widgets and removes everything glassy added. Your config is kept; add `--purge` at the end to delete it too. Packages like Conky and wmctrl are left installed.

## Credits

- **Anurati** font by Emmeran Richard (used for the clock's day name)
- **Ubuntu Sans** font by Canonical, under the Ubuntu Font Licence (see `fonts/UbuntuSans-LICENCE.txt`)
