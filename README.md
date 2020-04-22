# liveboxtvuhd

Ce module permet de contrôler le décodeur TV UHD 4K Orange depuis Home Assistant (https://www.home-assistant.io/). 

Développé et testé pour le décodeur TV UHD 4K Orange Fibre.


## Installation

1. Télécharger le dossier **liveboxtvuhd** et placer le placer dans le répertoire **custom_compoment** de Home Assistant.

2. Editez le fichier **configuration.yaml** et ajouter un media_player.


```yaml
media_player:
  - platform: liveboxtvuhd
    name: Livebox
    host: 192.168.1.2
    scan_interval: 30
```

## Exemples
Avec mini-media-player:

![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/liveboxtvuhd.PNG)

Avec le media-player standard

![Example](https://github.com/AkA57/liveboxtvuhd/blob/master/liveboxtvuhd2.PNG)

