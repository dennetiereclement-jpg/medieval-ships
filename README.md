# Medieval Ships — galère médiévale navigable (Fabric 1.21.11)

![Aperçu du modèle](docs/preview.png)

Une grande galère médiévale (20 blocs, mât de 13 blocs, 16 rames) qui est une **véritable
entité navigable**, pas une construction en blocs :

* objet *Galère médiévale* dans l'inventaire créatif (onglet *Navires médiévaux* et *Outils*),
  clic droit sur l'eau pour la mettre à l'eau ;
* flottaison sur la surface de l'eau, inertie, accélération progressive, virages fluides avec
  perte de vitesse, collisions avec le terrain, les quais et les autres navires, impossible de
  naviguer sur la terre ;
* pilotage au poste de barre (Z/S/Q/D, Espace/Ctrl pour les trois allures, Maj pour quitter) ;
* 8 places assises + le barreur, **et marche libre sur le pont pendant la navigation** ;
* animations synchronisées : rames (selon la vitesse), voile au vent, voile carguée à l'arrêt,
  avirons de gouverne, drapeaux, roulis ;
* **pilote automatique PNJ** : itinéraires par points de passage et escales, aller-retour,
  attente des passagers, annonces de départ, évitement d'obstacles, ferries qui continuent sans
  joueur à proximité et reprennent après un redémarrage ;
* commandes `/ship` pour les administrateurs ;
* aucune dépendance autre que Fabric API (ni GeckoLib, ni Valkyrien Skies, ni Eureka).

## Installation

Serveur **et** clients : `medieval-ships-1.1.1.jar` + [Fabric API](https://modrinth.com/mod/fabric-api)
0.141.6+1.21.11 (ou plus récent pour 1.21.11), Fabric Loader ≥ 0.18, Java 21.

## Compilation

```
./gradlew build          # jar dans build/libs/
./gradlew test           # tests unitaires (physique, collisions, pilote auto, modèle)
./gradlew runClient      # client de développement
./gradlew runServer      # serveur dédié de développement
```

Les versions sont dans `gradle.properties` (Yarn `1.21.11+build.6`, Loom 1.14.10,
Fabric API 0.141.6+1.21.11). Si Gradle ne trouve pas une version, prenez la plus récente
pour 1.21.11 sur <https://fabricmc.net/develop>.

## Documentation

* [Guide des commandes administrateur](docs/COMMANDES.md)
* [Créer un ferry automatique](docs/FERRY.md)
* [Modèle Blockbench, textures et animations](docs/MODELE.md)
* [Architecture technique (marche sur le pont, collisions, IA, performances)](docs/ARCHITECTURE.md)
* [Tests effectués et non effectués](docs/TESTS.md)

## Configuration

`config/medievalships.json` (créé au premier lancement, rechargeable avec `/ship reload`) —
la configuration par défaut se trouve dans [`config/medievalships.json`](config/medievalships.json).

| Clé | Défaut | Rôle |
|---|---|---|
| `slowSpeed` / `normalSpeed` / `fastSpeed` | 2.5 / 5.5 / 8.5 | allures lente / normale / rapide (blocs/s) |
| `reverseSpeed` | 1.8 | vitesse en marche arrière |
| `acceleration`, `braking` | 0.9, 1.8 | blocs/s² |
| `waterDrag` | 0.18 | perte de vitesse par seconde en roue libre (plus bas = plus d'inertie) |
| `maxTurnRate`, `minTurnFactor` | 16, 0.3 | vitesse de rotation max (°/s), part disponible à l'arrêt |
| `helmRate`, `helmReturnRate`, `turnResponse`, `turnSpeedLoss` | | réactivité de la barre, inertie de rotation, ralentissement en virage |
| `waveRocking` | 1.0 | amplitude du roulis visuel (0 = désactivé) |
| `ai*` | | réglages du pilote automatique (rayons, anticipation, portée de détection, attente par défaut) |
| `announceDepartures`, `announceRadius` | true, 40 | annonces de départ / d'arrivée |
| `chunkLoadAutopilotShips`, `chunkLoadRadius` | true, 2 | garder chargés les chunks des ferries |
| `adminPermissionLevel` | 2 | niveau requis pour `/ship` et la récupération des navires |
| `placeRequiresAdmin` | false | réserver la mise à l'eau aux administrateurs |
| `furlSailWhenStopped` | true | carguer la voile à l'arrêt |

## Structure du projet

```
blockbench/galley.bbmodel        modèle éditable (texture intégrée, 6 animations)
config/medievalships.json        configuration par défaut
docs/                            documentation et aperçu
src/main/java/.../core           navigation en Java pur (testée)
src/main/java/...                entité, commandes, données, réseau, mixin
src/client/java/...              rendu, visée, transport du joueur sur le pont
src/test/java/...                tests JUnit
tools/                           générateur du modèle et rendu d'aperçu (Python)
```
