# Livebox TV UHD

This is a custom component to allow control of Livebox TV UHD in [Homeassistant](https://home-assistant.io).

- :new: **Support for orange.fr and orange.pl Livebox** (thanks to WRLPDZ) :new:
- Power On/Off
- Play/Pause
- Next/Previous (Channel)
- Volume (+/-/mute)
- Channel source
- Retrieval for displaying in home assistant of:
  - Channel name
  - Show
  - Show background image
  - Show time
  - Serie title, season and episode

Two platform entities are available : 
- media player entity to handle the features above
- remote entity to bring additional controls

## Installation 

**Recommanded**

Use [HACS](https://hacs.xyz/).

**Manual**

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `liveboxtvuhd`.
4. Download _all_ the files from the `custom_components/liveboxtvuhd/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant

## Configuration

### Media Player
Edit `configuration.yaml` and add `liveboxtvuhd` as a new `media_player`

```yaml
media_player:
  - platform: liveboxtvuhd
    name: livebox-salon
    host: 192.168.1.2
    port: 8080
    scan_interval: 30
    country: poland
```
Name|Required|Description|Default
--|--|--|--
`name`|no|Friendly name|liveboxtvuhd
`host`|yes|Host or ip address| 
`port`|no|port number|8080 
`scan_interval`|no|Time between scan in seconds|10
`country`|no|choose between france and poland|france

### Remote
(Optional) add `remote` entity to have additional commands, with the same parameters : 
```yaml
remote:
  - platform: liveboxtvuhd
    name: livebox_salon
    host: 192.168.1.2
    port: 8080
    scan_interval: 30
    country: poland
```

Available commands for remote entity :

Command|Description
--|--
POWER|Power toggle
`0`|0
`1`|1
`2`|2
`3`|3
`4`|4
`5`|5
`6`|6
`7`|7
`8`|8
`9`|9
`CH+`|Channel Up
`CH-`|Channel Down
`VOL+`|Volume Up
`VOL-`|Volume Down
`MUTE`|Mute
`UP`|Cursor Up
`DOWN`|Cursor Down
`LEFT`|Cursor Left
`RIGHT`|Cursor Right
`OK`|OK
`BACK`|Back
`MENU`|Menu
`PLAY/PAUSE`|Play/Pause
`FBWD`|Rewind
`FFWD`|Fast Forward
`REC`|Record
`VOD`|VOD
`GUIDE`|GUIDE

## Examples
### Media Player
With standard media-player 

![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example2.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example3.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example6.png)


With [mini-media-player](https://github.com/kalkih/mini-media-player):

![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example4.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example5.png)
```yaml
type: 'custom:mini-media-player'
entity: media_player.livebox_salon
artwork: full-cover
volume_stateless: true
```

### Remote
With [universal-remote-card](https://github.com/Nerwyn/universal-remote-card/) (thanks to WarC0zes)

![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/remote.png)
```yaml
type: custom:universal-remote-card
rows:
  - power
  - circlepad
  - - back
    - menu
  - - - volume_up
      - volume_down
    - - volume_mute
    - - channel_up
      - channel_down
  - numpad
  - - rewind
    - play_pause
    - fast_forward
  - guide
  - - netflix
    - prime
remote_id: remote.livebox_salon
media_player_id: media_player.livebox_salon
platform: Android TV
custom_actions:
  - type: button
    name: netflix
    tap_action:
      action: perform-action
      perform_action: remote.send_command
      target:
        entity_id: remote.livebox_salon
      data:
        hold_secs: 0
        command:
          - 6
          - 6
    icon: phu:netflix
    haptics: true
    styles: ""
  - type: button
    name: prime
    icon: phu:prime-video
    tap_action:
      action: perform-action
      perform_action: remote.send_command
      target:
        entity_id: remote.livebox_salon
      data:
        hold_secs: 0
        command:
          - 6
          - 7
    haptics: true
  - type: circlepad
    name: circlepad
    tap_action:
      action: key
      key: OK
    up:
      icon: mdi:chevron-up
      tap_action:
        action: key
        key: UP
      hold_action:
        action: repeat
      type: button
    down:
      icon: mdi:chevron-down
      tap_action:
        action: key
        key: DOWN
      hold_action:
        action: repeat
      type: button
    left:
      icon: mdi:chevron-left
      tap_action:
        action: key
        key: LEFT
      hold_action:
        action: repeat
      type: button
    right:
      icon: mdi:chevron-right
      tap_action:
        action: key
        key: RIGHT
      hold_action:
        action: repeat
      type: button
    icon: ok
    styles: |-
      :host {
        width: 230px;      
      }
      .circlepad {
        border: 1px solid #444;
        background: radial-gradient(circle at top left, #202020 15%, #303030 100%);
        --icon-color: rgba(128,128,128,0.5);
      }

      #center::part(button) {
        background: radial-gradient(circle at top left, #303030 15%, #101010 100%);
        border: 1px solid rgba(0, 0, 0, 0.5);
      }
      #center::part(icon) {
       color: rgba(128,128,128, 0.8);
        --size: 46px;
      }

      #left,
      #right {
        width: 100%;
      }
  - type: button
    name: back
    tap_action:
      action: key
      key: BACK
    icon: mdi:arrow-u-left-top
  - type: button
    name: channel_up
    tap_action:
      action: key
      key: CHANNEL_UP
    icon: mdi:chevron-up
  - type: button
    name: channel_down
    tap_action:
      action: key
      key: CHANNEL_DOWN
    icon: mdi:chevron-down
  - type: button
    name: volume_up
    tap_action:
      action: key
      key: VOLUME_UP
    hold_action:
      action: repeat
    icon: mdi:plus
  - type: button
    name: volume_down
    tap_action:
      action: key
      key: VOLUME_DOWN
    hold_action:
      action: repeat
    icon: mdi:minus
  - type: button
    name: volume_mute
    tap_action:
      action: key
      key: MUTE
    icon: mdi:volume-mute
styles: |-
  #power::part(icon) {
  color: rgb(229, 9, 20);
  }
  #menu::part(icon) {
  color: rgb(229, 9, 20);
  }  
  #netflix::part(icon) {
  color: rgb(229, 9, 20);
  }
  #prime::part(icon) {
  color: rgb(0, 165, 222);
  }
custom_icons:
  - name: ok
    path: >-
      M7 7A2 2 0 005 9V15A2 2 0 007 17H9A2 2 0 0011 15V9A2 2 0 009 7H7M7
      9H9V15H7V9ZM13 7V17H15V13.7L17 17H19L16 12 19 7H17L15 10.3V7H13Z
haptics: true
card_mod:
  style: |
    ha-card {
      margin-left: 67px;
      width: 250px;
    }
keyboard_id: remote.livebox_salon
grid_options:
  columns: 6
  rows: 1
```

To trigger additional commands with the remote entity :
```yaml
service: remote.send_command
data:
  num_repeats: 1
  delay_secs: 0.4
  hold_secs: 0
  command: UP
target:
  entity_id: remote.livebox_salon
```