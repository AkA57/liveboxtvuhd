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

Edit `configuration.yaml` and add `liveboxtvuhd` as a new `media_player`

```yaml
media_player:
  - platform: liveboxtvuhd
    name: Livebox
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

(Optional) add `remote` entity to have additional commands, with the same parameters : 
```yaml
remote:
  - platform: liveboxtvuhd
    name: Livebox remote
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
With [mini-media-player](https://github.com/kalkih/mini-media-player):

![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example4.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example5.png)
```yaml
type: 'custom:mini-media-player'
entity: media_player.livebox
artwork: full-cover
volume_stateless: true
```


With standard media-player 

![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example2.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example3.png)
![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/screenshot/example6.png)

To trigger additional commands with the remote entity :
```yaml
service: remote.send_command
data:
  num_repeats: 1
  delay_secs: 0.4
  hold_secs: 0
  command: UP
target:
  entity_id: remote.livebox_remote
```