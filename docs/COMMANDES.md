# Guide des commandes administrateur — `/ship`

Toutes les commandes `/ship` demandent le niveau de permission défini par
`adminPermissionLevel` dans `config/medievalships.json` (2 par défaut, comme `/tp`).

## Quel navire est visé ?

Toutes les commandes marchent de la même façon pour la galère, le grand galion et le grand vaisseau de guerre.
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
| `/ship give warship [joueurs]` | Donne l'objet *Grand vaisseau de guerre*. |
| `/ship spawn warship` | Met un grand vaisseau de guerre à l'eau à votre position, proue dans votre direction. Il faut environ 60 × 15 blocs d'eau libre (2 blocs de profondeur minimum, 3 conseillés). |
| `/ship spawn galleon` | Met un grand galion à l'eau à votre position, proue dans votre direction. Il faut environ 40 × 10 blocs d'eau libre (2 blocs de profondeur minimum, 3 conseillés) et rien au-dessus. |
| `/ship give medieval_galley [joueurs]` | Donne l'objet *Galère médiévale rouge*. |
| `/ship spawn medieval_galley` | Met une galère rouge à l'eau à votre position (environ 32 × 12 blocs d'eau libre, 2 de profondeur). |
| `/ship give steam_paddleboat [joueurs]` | Donne l'objet *Bateau à roue à vapeur*. |
| `/ship spawn steam_paddleboat` | Met un bateau à roue à vapeur à l'eau (environ 26 × 16 blocs d'eau libre, une roue de chaque côté ; 2 de profondeur). |
| `/ship give elven_sailboat [joueurs]` | Donne l'objet *Voilier elfique*. |
| `/ship spawn elven_sailboat` | Met un voilier elfique à l'eau (environ 34 × 12 blocs d'eau libre, 2 de profondeur). |
| `/ship give steampunk_airship [joueurs]` | Donne l'objet *Dirigeable steampunk* (clic droit sur le sol, l'eau ou un toit : il apparaît au-dessus, s'il y a la place pour tout le dirigeable). |
| `/ship spawn steampunk_airship` | Fait apparaître un dirigeable au-dessus de votre position (environ 27 blocs de long, 9 de large, 18 de haut d'espace libre ; jamais dans une montagne ou un bâtiment). |
| `/ship give grand_warship`, `/ship spawn grand_warship` | Autre nom du grand vaisseau de guerre (`warship`, identifiant inchangé). |
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

### Placer un vaisseau avec son objet : aperçu et permissions

* **Aperçu** : tant que vous tenez l'objet d'un vaisseau en main, une **silhouette translucide** du
  vaisseau apparaît là où un clic droit le placerait, la proue dans la direction où vous regardez :
  **verte** s'il y a la place, **rouge** sinon, **grise** si le serveur ne vous autorise pas à placer ce
  vaisseau (la barre d'action le rappelle : « Clic droit : placer ici » / « Pas assez d'espace libre
  ici » / « Placement non autorisé »). C'est exactement le calcul du serveur, à partir du même point
  (le milieu de la face du bloc visé) et du même cap (arrondi à 2°), avec le même contrôle d'espace
  (relief, bâtiments, autres coques) et le plafond d'altitude du serveur : là où c'est vert, le
  vaisseau est posé à cet endroit précis ; là où c'est rouge, rien n'est placé et l'objet n'est pas
  consommé. Un navire se pose
  sur l'eau (visez l'eau), un aéronef au-dessus de ce que vous visez (sol, eau, toit). L'aperçu ne
  dessine que la coque et l'extérieur (pas les pièces ni le mobilier) et n'est calculé que pour vous.
* **Qui peut placer** (section `server` de `config/medievalships.json`, `/ship reload` pour appliquer) :

| Clé | Défaut | Effet |
|---|---|---|
| `placeRequiresAdmin` | `false` | `true` : seuls les administrateurs (niveau `adminPermissionLevel`) et les joueurs de `placeAllowedPlayers` placent un vaisseau, quel qu'il soit. |
| `placeAdminOnly` | `[]` | Vaisseaux réservés aux administrateurs même si `placeRequiresAdmin` est `false`, ex. `["sky_leviathan", "grand_warship"]` (identifiants ou alias, majuscules indifférentes ; un nom qui ne désigne aucun vaisseau est signalé dans le journal du serveur). |
| `placeAllowedPlayers` | `[]` | Joueurs non administrateurs autorisés malgré tout (pseudo ou UUID, majuscules indifférentes), ex. `["Capitaine_Nemo"]`. |

  Un joueur refusé reçoit « Seuls les administrateurs et les joueurs autorisés peuvent… » et garde son
  objet ; sa silhouette est grise. Le serveur envoie ces règles aux joueurs à la connexion et après
  `/ship reload`. `/ship give` et `/ship spawn` restent réservés aux administrateurs, comme tout `/ship`.
  Récupérer un navire (accroupi + clic gauche) est réservé aux administrateurs. Aucun vaisseau
  n'apparaît naturellement dans le monde et le mod n'ajoute aucune structure.

## Pilote automatique

| Commande | Effet |
|---|---|
| `/ship ai enable` | Active le pilote automatique sur le dernier itinéraire assigné. |
| `/ship ai disable` | Désactive le pilote : le navire laisse filer sa vitesse et s'arrête. |
| `/ship route assign <itinéraire>` | Assigne l'itinéraire au navire ciblé (galère, galion ou vaisseau de guerre) et lance la navigation automatique. |
| `/ship route start <itinéraire>` | Identique à `assign` (commande d'origine, conservée). |
| `/ship route stop` | Identique à `/ship ai disable`. |
| `/ship route depart` | Fait partir immédiatement un navire qui attend à une escale. |

Quand le pilote automatique est actif sur un itinéraire, aucun joueur ne peut prendre la barre
(sauf pour une **destination** donnée avec `goto`, voir ci-dessous).

## Destinations (aller à un point)

En plus des itinéraires, on peut envoyer un vaisseau **à un point** : le pilote automatique habituel
s'en charge (évitement des obstacles, altitude de croisière au-dessus du relief et des bâtiments pour
un aéronef, qui monte au-dessus de ce qui barre la route, ralentit à l'approche, s'arrête sur le
point et tient sa position ; un aéronef redescend alors à sa garde d'atterrissage `aiLandingClearance`
au-dessus du sol). La destination est un itinéraire d'un seul point propre au vaisseau
(`goto-<début de son UUID>`, visible dans `/ship route list` ; les noms commençant par `goto-` sont
réservés : `/ship route create` les refuse et `/ship route assign` ne donne pas la destination d'un
vaisseau à un autre), enregistré avec le monde.

* Donnée par un **administrateur** (`/ship goto`), elle est menée comme un ferry : chunks du trajet
  gardés chargés, trajet repris après un redémarrage, jusqu'à l'arrivée.
* Donnée par un **joueur** (`/pilote goto`), elle ne charge aucun chunk : ce sont les joueurs à bord
  qui chargent ceux où ils se trouvent. Elle est annulée si plus personne n'est à bord pendant 10 s
  (on ne peut donc pas envoyer au loin, à vide, le vaisseau d'un autre) ; après un redémarrage, elle
  reprend quand les joueurs reviennent à bord.
* **Un navire ne va que sur l'eau** : un point à terre est ramené à l'eau libre la plus proche (assez
  large pour la coque, au niveau de l'eau où il flotte, à 32 blocs au plus), sinon la destination est
  refusée. Si les chunks du point ne sont pas chargés, il ne peut pas être vérifié : il est accepté.
* **Destination inaccessible** : si le pilote automatique se déclare bloqué (aucun progrès pendant
  50 s, ou échecs répétés), la destination est abandonnée, ses chunks sont libérés et les joueurs à
  bord et autour lisent « destination inaccessible, le pilote automatique rend la main ».

| Commande | Effet |
|---|---|
| `/ship goto <x> <y> <z>` | Envoie le vaisseau ciblé à ce point (`~` accepté : `/ship goto ~200 ~ ~-50`). Pour un aéronef, `y` est la hauteur de son **pont** à l'arrivée (sous le sol : il se pose à sa garde au-dessus) ; un navire reste sur l'eau (seuls `x` et `z` comptent ; à terre, voir ci-dessus). |
| `/ship goto destination <nom>` | Vers une destination enregistrée. |
| `/ship goto visee` | Vers le bloc que vous visez (dans la distance de vue du serveur, 512 blocs au plus ; aucun chunk n'est chargé pour cela) : un aéronef s'y pose. |
| `/ship goto stop` | Annule la destination : un aéronef s'arrête en vol stationnaire, un navire file sur son erre. |
| `/ship destination add <nom>` | Enregistre votre position comme destination (pour un aéronef : hauteur du pont). |
| `/ship destination remove <nom>` | Supprime une destination. |
| `/ship destination list` | Liste les destinations (distance depuis vous). |

Le Nautilus n'accepte pas de destination directe : il suit des itinéraires sous-marins (voir
[NAUTILUS.md](NAUTILUS.md)).

### Pour les joueurs : `/pilote`

Si `playerDestinations` vaut `true` (défaut), **tout joueur à bord** (à la barre, sur le pont ou dans une
cabine) peut donner une destination au vaisseau sur lequel il se trouve :

| Commande | Effet |
|---|---|
| `/pilote goto <x> <y> <z>` | Le pilote automatique prend la barre et emmène le vaisseau à ce point. |
| `/pilote goto destination <nom>` | Vers une destination enregistrée par un administrateur. |
| `/pilote goto visee` | Vers le bloc visé (un aéronef s'y pose). |
| `/pilote stop` | Annule la destination. |
| `/pilote destinations` | Liste les destinations enregistrées. |

**Reprendre la main** : clic droit sur la barre (ou `/pilote stop`) — la destination est annulée et
vous tenez la barre. Garde-fous : un vaisseau affecté à l'itinéraire d'un administrateur (un ferry),
qu'il le suive ou qu'il soit arrêté par `/ship ai disable`, ne peut pas être dérouté par un joueur
(son affectation est gardée) ; si un autre joueur tient la barre, lui seul choisit la destination ;
la destination est au plus à `playerDestinationMaxDistance` blocs (1000 par défaut) pour un joueur
qui n'est pas administrateur ; le trajet ne charge aucun chunk et s'arrête si plus personne n'est à
bord pendant 10 s. `playerDestinations: false` réserve `/pilote` aux administrateurs.

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
| `/ship route create <nom> [mode] air` | Itinéraire **aérien** (dirigeable), voir plus bas. |
| `/ship route removepoint <nom> <n°>` | Supprime le point n° (numérotation de `info`). |
| `/ship route mode <nom> <pingpong\|loop\|once>` | Change le mode. |
| `/ship route info <nom>` | Liste les points. |
| `/ship route show <nom>` | Affiche le tracé en particules (escales en vert). |
| `/ship route list` | Liste les itinéraires. |
| `/ship route delete <nom>` | Supprime l'itinéraire. |

Les itinéraires sont enregistrés dans la sauvegarde du monde (`data/medievalships.dat`) et
survivent aux redémarrages.

### Itinéraires aériens (dirigeable)

Un dirigeable ne suit que des **itinéraires aériens**, et un navire que des itinéraires
maritimes (`assign` refuse le mélange). Les points d'un itinéraire aérien sont en **3D** :
placez-vous **là où doit se trouver le pont de la nacelle** (en volant en créatif, ou debout sur
le quai du port aérien) avant `addpoint` / `addstop`.

| Commande | Effet |
|---|---|
| `/ship route create <nom> air` ou `/ship route create <nom> <mode> air` | Crée un itinéraire aérien. Ex. `/ship route create capitale_ville loop air` |
| `/ship route addpoint <nom>` / `addstop <nom> [secondes] [nom]` | Comme sur l'eau, mais la **hauteur** compte ; une escale retient aussi votre **orientation** : le dirigeable s'y tourne pendant l'attente. |
| `/ship route edit <nom> <n°> yaw <degrés>` ou `yaw here` | Cap à prendre pendant l'escale n°. |
| `/ship route edit <nom> <n°> speed <blocs/s>` | Vitesse sur le tronçon qui mène au point n°. |
| `/ship route edit <nom> <n°> altitude <y>` | Hauteur (pont de la nacelle) du point n°. |
| `/ship route edit <nom> <n°> wait <secondes>` | Durée d'escale (0 = simple point de passage). |
| `/ship route edit <nom> <n°> clear` | Efface le cap et la vitesse du point. |

En route, le pilote automatique du dirigeable **décolle progressivement**, **monte** à la
hauteur du point suivant, mais toujours au moins `aiClearance` (5) blocs au-dessus du relief et
des bâtiments qu'il va survoler (il ralentit, ou s'arrête en vol stationnaire, le temps de
monter assez) ; il **anticipe les virages**, **ralentit** à l'approche d'une escale, **descend**
à sa hauteur dans les `aiApproachDistance` (26) derniers blocs, s'arrête, attend, se tourne vers
le cap de l'escale, puis repart. Il ne traverse jamais rien : s'il n'y a pas de passage sûr
(relief plus haut que le plafond `maxAltitude`), il s'arrête et prévient les administrateurs.

Exemple (Capitale → Tour de surveillance → Ville marchande → retour) :

```
/ship route create aerien_capitale loop air
# sur le quai du port aérien de la Capitale, tourné vers le large :
/ship route addstop aerien_capitale 120 Port aérien de la Capitale
# en vol au-dessus de la tour, à la hauteur voulue :
/ship route addpoint aerien_capitale
# sur la plate-forme de la ville marchande :
/ship route addstop aerien_capitale 120 Ville marchande
/ship route edit aerien_capitale 2 speed 6
# près du dirigeable :
/ship route assign aerien_capitale
```

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

**Dirigeable** : Z avancer, S ralentir puis reculer, Q / D tourner, **Espace monter**,
**Ctrl descendre** (relâchées : il garde son altitude, il ne tombe pas), Maj quitter le poste.
Ce sont les touches *Sauter* et *Sprinter* de Minecraft : elles se changent dans *Options →
Commandes* si un autre mod les utilise déjà.

**Tableau de bord du pilote** : en haut à gauche de l'écran, seulement pour le joueur à la barre
(les passagers et les autres joueurs ne voient rien) : nom du vaisseau, **vitesse** (blocs/s et
km/h, « en arrière »), pour un aéronef **altitude** du pont et hauteur sous la quille, **montée /
descente / palier**, pour le Nautilus la **profondeur**, l'état du **moteur** (vol stationnaire,
ralenti, croisière, plein régime, marche arrière) et l'**allure**, l'état du **pilote automatique**
et les touches. Quand le pilote automatique emmène le vaisseau vers une destination, le joueur resté
près de la barre voit « Pilote auto : en route vers … (… blocs) » et « Clic droit sur la barre :
reprendre la main » (en visant la barre : « Clic droit : reprendre la barre (annule la
destination) »). Une limite fixée par un administrateur (`/ship speed <n>`) s'affiche (« Limite : …
blocs/s »). Les touches indiquées sont celles de vos options (*Avancer*, *Reculer*, *Gauche*,
*Droite*, *Sauter*, *Sprinter*, *S'accroupir*), quel que soit le clavier. Le tableau se cache avec l'interface (F1) et sous l'écran de débogage (F3).
La barre d'action reste libre pour les messages (plongée, refus, annonces).

**Inclinaison en virage** : les aéronefs s'inclinent légèrement dans les virages (côté intérieur
vers le bas), d'autant plus qu'ils vont vite et tournent serré. C'est purement visuel : les
collisions, les ponts où l'on marche et le transport des passagers restent à plat, et l'angle est
limité pour que ni le pont ni les pièces ne paraissent à plus d'un demi-bloc de leur position réelle
(≈ 6° pour le dirigeable steampunk, ≈ 1° pour le Léviathan des Cieux, dont les pièces vont de la cale
au sommet du ballon). Réglable par vaisseau : `bankAngle` du bloc `flight` (0 = aucune inclinaison),
dans la configuration **du serveur**, envoyée aux joueurs.
