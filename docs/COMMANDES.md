# Guide des commandes administrateur — `/ship`

Toutes les commandes `/ship` demandent le niveau de permission défini par
`adminPermissionLevel` dans `config/medievalships.json` (2 par défaut, comme `/tp`).

## Quel navire est visé ?

Toutes les commandes marchent de la même façon pour la galère et pour le grand galion.
Les commandes qui agissent sur « le navire ciblé » le choisissent dans cet ordre :

1. le navire sur lequel vous êtes **assis** ;
2. le navire sur le **pont** duquel vous vous tenez ;
3. le navire que vous **regardez** (jusqu'à 64 blocs) ;
4. le navire le plus **proche** dans un rayon de 32 blocs.

Depuis la console ou un bloc de commande, seul le point 4 s'applique (position de la source,
utilisable avec `/execute positioned ... run ship ...`).

## Navires

| Commande | Effet |
|---|---|
| `/ship give [joueurs]` | Donne l'objet *Galère médiévale* (à vous par défaut) — inchangé. |
| `/ship give galley [joueurs]` | Donne l'objet *Galère médiévale*. |
| `/ship give galleon [joueurs]` | Donne l'objet *Grand galion*. |
| `/ship spawn` | Met une galère à l'eau à votre position, proue dans votre direction — inchangé. Il faut environ 24 × 6 blocs d'eau profonde d'au moins 2 blocs. |
| `/ship spawn galley` | Identique à `/ship spawn`. |
| `/ship spawn galleon` | Met un grand galion à l'eau à votre position, proue dans votre direction. Il faut environ 40 × 10 blocs d'eau libre (2 blocs de profondeur minimum, 3 conseillés) et rien au-dessus. |
| `/ship remove` | Supprime le navire ciblé (les passagers sont débarqués sur place). |
| `/ship list` | Liste les navires chargés, et les navires automatiques connus mais non chargés. |
| `/ship info` | Vitesse, cap, barre, allure, pilote automatique, itinéraire, passagers. |
| `/ship name <nom>` | Donne un nom au navire (utilisé dans les annonces : « *La Sirène* part vers… »). |
| `/ship speed <lente\|normale\|rapide>` | Change l'allure du navire. |
| `/ship speed <blocs/s>` | Impose une vitesse maximale à ce navire (ex. `/ship speed 4`). |
| `/ship speed reset` | Revient aux allures de la configuration. |
| `/ship unstuck` | Déplace le navire vers l'eau libre la plus proche (24 blocs max). |
| `/ship captain add` | Installe un PNJ « Capitaine » (villageois immobile et invulnérable) à la barre. |
| `/ship captain remove` | Retire le capitaine PNJ. |
| `/ship reload` | Recharge `config/medievalships.json`. |

**Récupérer un navire en jeu** : un administrateur **accroupi** fait un **clic gauche** sur le
navire. Le navire disparaît et l'objet est rendu (en créatif, seulement si vous ne l'avez pas déjà).

## Pilote automatique

| Commande | Effet |
|---|---|
| `/ship ai enable` | Active le pilote automatique sur le dernier itinéraire assigné. |
| `/ship ai disable` | Désactive le pilote : le navire laisse filer sa vitesse et s'arrête. |
| `/ship route assign <itinéraire>` | Assigne l'itinéraire au navire ciblé (galère ou galion) et lance la navigation automatique. |
| `/ship route start <itinéraire>` | Identique à `assign` (commande d'origine, conservée). |
| `/ship route stop` | Identique à `/ship ai disable`. |
| `/ship route depart` | Fait partir immédiatement un navire qui attend à une escale. |

Quand le pilote automatique est actif, aucun joueur ne peut prendre la barre.

## Itinéraires

Un itinéraire est une liste de points enregistrés à **votre position actuelle**.
Il existe deux sortes de points :

* **point de passage** (`addpoint`) : le navire passe à proximité sans s'arrêter ;
* **escale** (`addstop`) : le navire ralentit, s'arrête au point exact, attend, puis repart.

| Commande | Effet |
|---|---|
| `/ship route create <nom> [pingpong\|loop\|once]` | Crée un itinéraire. `pingpong` (défaut) = aller-retour, `loop` = boucle, `once` = aller simple. |
| `/ship route addpoint <nom>` | Ajoute un point de passage à votre position. |
| `/ship route addstop <nom> [secondes] [nom de l'escale]` | Ajoute une escale (attente par défaut : `aiDefaultWaitSeconds`, 300 s). Ex. `/ship route addstop ferry 300 Port de Valombre` |
| `/ship route removepoint <nom> <n°>` | Supprime le point n° (numérotation de `info`). |
| `/ship route mode <nom> <pingpong\|loop\|once>` | Change le mode. |
| `/ship route info <nom>` | Liste les points. |
| `/ship route show <nom>` | Affiche le tracé en particules (escales en vert). |
| `/ship route list` | Liste les itinéraires. |
| `/ship route delete <nom>` | Supprime l'itinéraire. |

Les itinéraires sont enregistrés dans la sauvegarde du monde (`data/medievalships.dat`) et
survivent aux redémarrages.

## Commandes de pilotage (joueurs)

| Action | Touche (AZERTY) |
|---|---|
| Prendre la barre | clic droit sur la barre/le tabouret à la poupe |
| S'asseoir | clic droit sur un banc |
| Monter à bord depuis l'eau ou le quai | clic droit sur la coque (ou enjamber le bastingage) |
| Ramer en avant | Z |
| Freiner / reculer | S |
| Barre à bâbord / tribord | Q / D |
| Allure supérieure / inférieure | Espace / Ctrl |
| Quitter la barre ou le banc | Maj |

Les touches suivent les commandes de déplacement du joueur : elles fonctionnent avec n'importe
quelle disposition de clavier.
