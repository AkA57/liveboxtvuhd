# Livebox TV UHD

This is a custom component to allow control of Livebox TV UHD in [Homeassistant](https://home-assistant.io).

- Power On/Off
- Play/Pause
- Next/Previous (Track)
- Volume
- Channel source
- Retrieval for displaying in home assistant of:
  - Channel name
  - Show
  - Show background image
  - Show time

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
    scan_interval: 30
```

Name|Required|Description
--|--|--
`name`|no|Friendly name
`host`|yes|Host or ip address 
`scan_interval`|no|Time between scan in seconds

## Examples
With mini-media-player:

![Example](https://github.com/AkA57/liveboxtvuhd/blob/dev/screenshot/example.png)

With standard media-player 

![Example](https://github.com/AkA57/liveboxtvuhd/blob/dev/screenshot/example2.png)

