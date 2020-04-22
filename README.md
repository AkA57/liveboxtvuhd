# liveboxtvuhd

This library is intended for controlling an Orange Livebox TV UHD from Home Assistant 
appliance.

## Installation
1. Download and put "liveboxtvuhd" under your custom_compoment directory
2. Add liveboxtvuhd to your configuration.yaml

```yaml
media_player:
  - platform: liveboxtvuhd
    name: Livebox
    host: 192.168.1.2
    scan_interval: 30
```
