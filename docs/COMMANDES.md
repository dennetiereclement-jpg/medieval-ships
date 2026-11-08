# Guide des commandes administrateur — `/ship`

Toutes les commandes `/ship` demandent le niveau de permission défini par
`adminPermissionLevel` dans `config/medievalships.json` (2 par défaut, comme `/tp`).

## Quel navire est visé ?

Toutes les commandes marchent de la même façon pour tous les vaisseaux (galère, galion, vaisseau de
guerre, aéronefs, Nautilus…). Les commandes qui agissent sur « le navire ciblé » le choisissent dans cet ordre :

0. le navire **au nom duquel** la commande s'exécute : `/ship as <navire> …` (voir
   [Scénarios de quêtes / PNJ](#scénarios-de-quêtes--pnj)), `/execute as @e[name="La Sirène"] run ship …`,
   ou une commande d'arrivée d'escale (`/ship route onarrive`) ;
1. le navire sur lequel vous êtes **assis** ;
2. le navire sur le **pont** duquel vous vous tenez ;
3. le navire que vous **regardez** (jusqu'à 64 blocs) ;
4. le navire le plus **proche** dans un rayon de 32 blocs.

Depuis la console ou un bloc de commande, seuls les points 0 et 4 s'appliquent (position de la source,
utilisable avec `/execute positioned ... run ship ...`). Pour un script (PNJ Easy NPC, bloc de commande,
fonction), préférez toujours `/ship as <navire> …` avec le **nom** du navire (`/ship name`) : voir plus bas.

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
| `/ship spawn <type> <x> <y> <z> [<cap>]` | Met le vaisseau à l'eau (ou en l'air) **à ce point**, proue vers `<cap>` (degrés Minecraft : 0 = sud, 90 = ouest, 180 = nord, -90 = est ; sans cap : la direction de la source). `~` accepté. Équivaut à `/execute positioned … rotated … run ship spawn <type>`. |
| `/ship spawn <type> [<x> <y> <z> [<cap>]] route <itinéraire> [wait\|hold\|go] [named <nom>]` | Met le vaisseau **sur un itinéraire**, à sa **première escale** (sans coordonnées), tourné vers le point suivant (ou le cap de l'escale), déjà affecté à l'itinéraire et **amarré** : il attend le temps de l'escale, ou l'**ordre de départ** (`wait` / `hold` : `/ship route depart`), ou part tout de suite (`go`). `named <nom>` lui donne son nom (pour `/ship as <nom>`). Voir [Scénarios de quêtes / PNJ](#scénarios-de-quêtes--pnj). |
| `/ship remove` | Supprime le navire ciblé (les passagers sont débarqués sur place). |
| `/ship disembark [<x> <y> <z>]` | Fait **débarquer tous les joueurs à bord** du navire ciblé (assis ou debout sur le pont / dans les pièces) : sur le **quai ou le rivage** le plus proche de la coque (bloc solide avec deux blocs libres au-dessus, hors de l'eau, à peu près à la hauteur du pont ; un aéronef amarré au-dessus du sol les pose dessous), ou au point donné. En pleine mer sans quai : personne n'est déposé (échec de la commande), donnez un point. Les PNJ (capitaine) restent à bord. |
| `/ship as <navire> <commande /ship…>` | Exécute n'importe quelle commande `/ship` **sur ce navire** : `<navire>` est son **nom** (`"La Sirène"`, entre guillemets s'il a des espaces), son **UUID** (ou ses 6 premiers caractères au moins), un **type** (`galley` : le plus proche de ce type) ou `nearest` (le ciblage habituel). Ex. `/ship as "La Sirène" route depart`. |
| `/ship test <navire> docked\|holding\|sailing\|finished\|empty` | Interroge un navire : amarré à une escale (`docked`, aussi vrai au terminus), amarré **en attente de l'ordre de départ** (`holding`), en route (`sailing`), arrivé au bout d'un itinéraire `once`/`return` (`finished`), **personne à bord** (`empty`). Résultat 1 = oui, 0 = non (`/execute store result score … run ship test …`). |
| `/ship test <navire> at <n°>` | Le navire est-il amarré à l'escale n° (numérotation de `route info`) ? |
| `/ship test <navire> aboard <joueurs>` | **Tous** les joueurs donnés sont-ils à bord ? Résultat : leur nombre (0 si l'un d'eux manque). Ex. `aboard @a`, `aboard Alice`. |
| `/execute if\|unless ship <navire> <condition> run …` | Les mêmes conditions **directement dans `/execute`** : `/execute if ship "La Sirène" aboard @a run ship as "La Sirène" route depart`. |
| `/ship list` | Liste les navires chargés (nom, position, début d'UUID, itinéraire, « attend l'ordre de départ »), et les navires automatiques connus mais non chargés. |
| `/ship info` | Vitesse, cap, barre, allure, pilote automatique, itinéraire, attente (ou « sur ordre »), passagers, joueurs à bord. |
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
| `/ship route depart` | Fait partir immédiatement un navire qui attend à une escale (escale minutée **ou** escale `hold` : c'est l'**ordre de départ**). Au terminus d'un itinéraire qui finit par `despawn`, c'est l'ordre de disparaître. |

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
  bord et autour lisent « destination inaccessible, le pilote automatique rend la main » (ou, s'il
  s'est arrêté à moins de 12 blocs du point, « arrivé au plus près de la destination »).

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
| `/ship route create <nom> [pingpong\|loop\|once\|return]` | Crée un itinéraire. `pingpong` (défaut) = aller-retour sans fin, `loop` = boucle, `once` = aller simple (le navire reste au terminus, ou disparaît : voir `end`), `return` = **un seul aller-retour** : va jusqu'au dernier point, y attend le temps de l'escale, revient au premier point et s'y arrête (puis `end`). |
| `/ship route addpoint <nom>` | Ajoute un point de passage à votre position. |
| `/ship route addstop <nom> [secondes] [nom de l'escale]` | Ajoute une escale (attente par défaut : `aiDefaultWaitSeconds`, 300 s). Ex. `/ship route addstop ferry 300 Port de Valombre` |
| `/ship route addstop <nom> hold [nom de l'escale]` | Ajoute une escale **« sur ordre »** : le navire y attend **indéfiniment**, jusqu'à `/ship route depart` (un PNJ, un bloc de commande). Ex. `/ship route addstop traversee hold Quai du village` |
| `/ship route create <nom> [mode] air` | Itinéraire **aérien** (dirigeable), voir plus bas. |
| `/ship route removepoint <nom> <n°>` | Supprime le point n° (numérotation de `info`). |
| `/ship route mode <nom> <pingpong\|loop\|once\|return>` | Change le mode. |
| `/ship route end <nom> <stay\|despawn\|despawn_item>` | **Fin du voyage** d'un itinéraire `once` ou `return` : `stay` (défaut) le navire reste amarré au terminus ; `despawn` il attend le temps de la dernière escale (ou l'ordre de départ si elle est `hold`), **débarque les joueurs** sur le quai le plus proche (comme `/ship disembark`) et **disparaît** ; `despawn_item` pareil, en **laissant son objet** sur place. Sans effet en `pingpong` / `loop`. |
| `/ship route onarrive <nom> <n°> <commande>` | **Commande d'arrivée** : quand un navire arrive à l'escale n°, le serveur exécute la commande (sans `/` initial ou avec, au choix) **au nom du navire** : `@s` est le navire, `~ ~ ~` sa position, `/ship …` sans sélecteur le vise. Ex. `/ship route onarrive traversee 2 tellraw @a[distance=..40] "Le navire est au port !"`. Sans commande : efface celle de l'escale. **Sécurité** : voir ci-dessous. |
| `/ship route info <nom>` | Liste les points (escales `hold`, commandes d'arrivée, fin du voyage). |
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
| `/ship route edit <nom> <n°> wait hold` | L'escale devient une escale **« sur ordre »** (attente jusqu'à `/ship route depart`). Vaut aussi pour les itinéraires maritimes. |
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

## Scénarios de quêtes / PNJ

Tout ce qu'il faut pour qu'un **PNJ (Easy NPC)**, un **bloc de commande** ou une **fonction** fasse
voyager des joueurs **sans toucher au Java** : un vaisseau est créé sur un itinéraire, attend au quai que
les joueurs montent, part sur ordre, navigue seul, arrive au port, débarque tout le monde, puis repart ou
disparaît selon la configuration de l'itinéraire. Les pièces :

* **Escale « sur ordre »** (`addstop <nom> hold …`, ou `edit <nom> <n°> wait hold`) : le navire y attend
  indéfiniment ; `/ship route depart` est l'ordre de départ.
* **Apparition sur l'itinéraire** : `/ship spawn <type> route <nom> [wait|hold|go] [named <nom du navire>]`
  met le vaisseau à la première escale, déjà affecté à l'itinéraire, amarré ; `wait` le retient jusqu'à
  l'ordre quel que soit le temps de l'escale, `go` le fait partir tout de suite. Avec `<x> <y> <z> [<cap>]`
  avant `route`, il apparaît à ce point et rejoint l'itinéraire (amarré si une escale est à portée).
* **Adresser un navire par son nom** : `/ship as "<nom>" <commande>` pour toute commande `/ship`,
  `/ship test "<nom>" …` et `/execute if|unless ship "<nom>" … run …` pour les conditions. Le nom vient de
  `named …` à l'apparition ou de `/ship name`. Un UUID (ou son début), un type ou `nearest` conviennent aussi.
* **Fin du voyage** d'un itinéraire `once` ou `return` : `/ship route end <nom> stay|despawn|despawn_item`.
* **Commandes d'arrivée** : `/ship route onarrive <nom> <n°> <commande>`.
* **Débarquement** : `/ship disembark [<x> <y> <z>]` (tous les joueurs à bord, sur le quai le plus proche ou au point).
* **Conditions** : `/ship test <navire> aboard <joueurs>` (tous à bord ?), `at <n°>`, `docked`, `holding`,
  `sailing`, `finished`, `empty`, utilisables avec `/execute if|unless ship …` ou
  `/execute store result score … run ship test …`.

Tout cela vaut pour **tous les vaisseaux** : navires (itinéraires maritimes), aéronefs (itinéraires `air`,
y compris la montgolfière) et le Nautilus (itinéraires sous-marins). Les itinéraires, leurs escales `hold`,
leurs commandes d'arrivée et leur fin sont enregistrés avec le monde ; un navire amarré « sur ordre » le
reste après un redémarrage.

### Exemple complet : la traversée du village au port

Préparation (une fois, par un administrateur ; `#` = commentaire) :

```
# l'itinéraire : aller simple, le navire disparaît au bout
/ship route create traversee once
# debout sur l'eau (ou le quai) du village, là où doit se trouver le milieu du navire :
/ship route addstop traversee hold Quai du village
# éventuellement des points de passage pour contourner un cap :
/ship route addpoint traversee
# au port d'arrivée : 60 s d'escale pour débarquer, puis le navire disparaît
/ship route addstop traversee 60 Port de Valombre
/ship route end traversee despawn
# à l'arrivée au port (escale n° 2), un message aux joueurs autour, puis tout le monde à terre
/ship route onarrive traversee 2 tellraw @a[distance=..40] {"text":"Terre ! Le Faucon accoste au port de Valombre.","color":"aqua"}
```

Une seule commande par escale : pour en enchaîner plusieurs, faites exécuter une **fonction**
(`/ship route onarrive traversee 2 function maquete:arrivee_port`) dont le contenu est, par exemple :

```
tellraw @a[distance=..40] "Terre ! Le Faucon accoste au port de Valombre."
ship disembark
```

Le scénario joué (commandes du PNJ Easy NPC, de blocs de commande ou d'une fonction) :

```
# 1. le PNJ du village fait apparaître le navire au quai, amarré, en attente de l'ordre, et le nomme
/ship spawn galley route traversee wait named Le Faucon
# 2. les joueurs montent à bord (clic droit sur la coque, enjamber depuis le quai, s'asseoir sur un banc…)
#    le PNJ peut vérifier qu'ils y sont tous avant de donner l'ordre :
/execute if ship "Le Faucon" aboard @a[tag=quete_valombre] run ship as "Le Faucon" route depart
#    (ou sans condition : /ship as "Le Faucon" route depart)
# 3. le navire navigue seul jusqu'au port avec ses passagers (pilote automatique : évitement, ralentissement, arrêt)
# 4. à l'arrivée, la commande d'arrivée s'exécute ; un PNJ du port peut aussi attendre l'escale :
/execute if ship "Le Faucon" at 2 run tellraw @a[distance=..40] "Bienvenue à Valombre !"
# 5. les joueurs débarquent sur le quai (d'eux-mêmes, ou tous à la fois) :
/ship as "Le Faucon" disembark
# 6. 60 s après l'arrivée (ou dès /ship as "Le Faucon" route depart si l'escale était « hold »),
#    le navire débarque ceux qui restent et disparaît (end despawn). Pour qu'il reparte à vide vers le
#    village et y reste : /ship route mode traversee return (et end stay) ; pour un ferry permanent : pingpong.
```

Pour rejouer la quête, le PNJ relance simplement l'étape 1 : l'itinéraire est conservé. Si un navire
du même nom est encore au quai, `/ship spawn … route …` refuse (« pas assez d'eau libre ») : supprimez-le
(`/ship as "Le Faucon" remove`) ou laissez-le disparaître.

**Sécurité des commandes d'arrivée** : seules les commandes `/ship` (niveau `adminPermissionLevel`, 2 par
défaut) permettent d'en définir, et elles s'exécutent **avec ce même niveau de permission** (jamais plus :
celui qui peut en écrire une pouvait déjà la lancer lui-même), au nom du navire (`@s`), avec leur sortie
dans le journal du serveur et, comme pour les blocs de commande, envoyée aux opérateurs si la règle de jeu
`commandBlockOutput` est active. Elles sont enregistrées en clair avec l'itinéraire (`/ship route info`
les affiche) et ne s'exécutent qu'à l'arrivée à une **escale** (pas pour une destination `goto`). Si
`adminPermissionLevel` vaut 0 ou 1, ces commandes n'ont donc pas le niveau d'un opérateur : `tellraw`,
`setblock`, `give`… (niveau 2) échoueraient — c'est voulu.

## Pont-levis automatique — `/pontlevis` (1.24.0)

Même niveau de permission que `/ship` ; `/drawbridge` est un alias. Le guide complet (principe, installation pas à
pas, détection, gabarit, sécurités, configuration, limites) est dans [PONT_LEVIS.md](PONT_LEVIS.md).

| Commande | Effet |
|---|---|
| `/pontlevis liste` | Les ponts définis, leur état. |
| `/pontlevis creer <id>` | Crée un pont (dans votre dimension). |
| `/pontlevis <id> supprimer` (ou `/pontlevis supprimer <id>`) | Supprime un pont (ses blocs d'origine sont remis s'ils étaient levés). |
| `/pontlevis <id> vantail <A\|B> pos1\|pos2 [<x y z>]` | Un coin de la sélection d'un vantail : le bloc visé, ou des coordonnées. |
| `/pontlevis <id> vantail <A\|B> charniere auto [bas\|haut] \| <x y z>` | Pivot du vantail : arête côté rive (défaut : basse), ou un point de la ligne de charnière. |
| `/pontlevis <id> axe x\|z\|auto\|<dx dz>` | Sens de circulation des bateaux sous le pont. |
| `/pontlevis <id> chenal largeur <blocs>\|auto`, `chenal centre [<x y z>\|auto]` | Largeur navigable entre les tours, centre du chenal. |
| `/pontlevis <id> eau <y>\|auto` | Niveau de l'eau. |
| `/pontlevis <id> approche\|hysteresis\|marge\|arret <blocs>`, `angle <degrés>`, `duree\|delai\|securite <secondes>` | Réglages du pont. |
| `/pontlevis <id> chaines on\|off\|auto\|<hauteur>` | Mécanisme dessiné au-dessus des charnières : poutre de treuil d'une tour à l'autre, deux tambours par vantail, chaînes à vrais maillons jusqu'aux coins du bout libre (hauteur de la poutre automatique : longueur du vantail + 1,5). `off` masque poutre, tambours et chaînes ; l'axe de charnière et ses paliers restent. |
| `/pontlevis <id> apercu on\|off` | Sélections, charnières, volume balayé, barrières, zones d'approche, passage, hauteur libre, dessinés pour vous. |
| `/pontlevis <id> verifier` | Analyse : blocs, charnières, chenal, eau, hauteur libre, volume balayé contre les blocs fixes. |
| `/pontlevis <id> convertir` | Met le pont en service (ses blocs restent en place tant qu'il est fermé). |
| `/pontlevis <id> etat` | État complet : cycle, angle, attente, réglages, navires pris en compte et leur verdict. |
| `/pontlevis <id> tester <navire>` | Mesure un navire (hauteur, largeur, occupants, verdict, position dans les zones). |
| `/pontlevis <id> debug on\|off` | Diagnostic continu dans la barre d'action. |
| `/pontlevis <id> auto on\|off` | Active ou suspend l'automatisme. |
| `/pontlevis <id> ouvrir`, `fermer` | Manœuvre manuelle, sécurités respectées. |
| `/pontlevis <id> demande <clé> [secondes]`, `demande annuler <clé>` | Demande scriptée d'ouverture (quêtes, PNJ, blocs de commande). |
| `/pontlevis <id> restaurer` | Remet les blocs d'origine et rend la main (seule la zone mobile est touchée). |

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
ralenti, croisière, plein régime, marche arrière, « bridé à la limite » quand une limite
d'administrateur le retient) et l'**allure**, l'état du **pilote automatique**
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
