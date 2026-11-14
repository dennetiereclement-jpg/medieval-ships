# Les dix portes animées (1.31.0, clés 1.32.0)

Dix portes médiévales à poser dans vos murs, châteaux, prisons, entrepôts et villes : de vrais battants qui
tournent sur leurs charnières, des collisions qui suivent la porte, la redstone, des leviers liés à distance, des
accès (verrouillée, quête, **à clé**...), des **clés** et un **passe-partout** pour l'administrateur, une **fermeture
automatique au bout d'une minute**, et des commandes `/porte` pour les blocs de commande, les PNJ et les quêtes.

Rien n'est généré dans le monde : aucune porte n'apparaît seule, aucun village n'est modifié, les portes vanilla ne
changent pas. Chaque porte n'a **aucune entité** : un bloc contrôleur (avec ses données) et des blocs invisibles pour
les autres cases de l'ouverture ; tout est dessiné par le contrôleur.

## Les dix portes

| Objet (`/give @p medievalships:<id>`) | Nom | Ouverture (haut x large) | Battants | Durée | Son |
|---|---|---|---|---|---|
| `porte_chene` | Porte en chêne | 2 x 1 | 1 | 0,6 s | bois |
| `porte_prison` | Porte de prison | 2 x 1 | 1 (pêne animé) | 0,6 s | fer |
| `porte_vapeur` | Porte à vapeur | 2 x 1 | 1 | 0,6 s | fer + piston, vapeur |
| `porte_grange` | Porte de grange | 4 x 2 | 2 | 1,2 s | bois (plus grave) |
| `porte_forteresse` | Porte de forteresse | 4 x 2 | 2 | 1,2 s | bois (plus grave) |
| `porte_industrielle` | Porte industrielle | 4 x 2 | 2 | 1,2 s | fer + piston, vapeur |
| `porte_marchande` | Porte marchande | 4 x 2 | 2 | 1,2 s | bois (plus grave) |
| `porte_chateau` | Porte de château | 6 x 4 | 2 | 3,5 s | bois (grave, lourd, grincements) |
| `porte_vapeur_grande` | Grande porte à vapeur | 6 x 4 | 2 | 3,5 s | fer + piston, vapeur, engrenages |
| `porte_entrepot` | Porte d'entrepôt | 6 x 4 | 2 | 3,5 s | bois (grave, lourd, grincements) |

Elles sont dans l'onglet créatif **« Portes »**, avec la **clé** (`medievalships:cle`) et le **passe-partout**
(`medievalships:cle_universelle`). Les fenêtres, hublots et lanternes des modèles sont éclairés.

### L'animation (1.32.0)

Chaque mouvement se déroule en deux temps, calculé image par image par chaque client (aucun paquet par tick) :

1. **le déverrouillage** (environ 15 % de la durée) : les pênes reculent, les anneaux et poignées tournent (sens
   horaire vu de face, en miroir sur le battant droit, 30° au plus ; le volant de la porte à vapeur tourne davantage),
   les battants attendent ;
2. **les battants** : départ lent, accélération puis ralentissement (l'inertie d'un battant lourd, pas un mouvement
   régulier) ; en fin d'ouverture ils dépassent un peu la butée et reviennent se tasser ; en fin de fermeture ils
   claquent contre le cadre, rebondissent légèrement, puis les pênes se referment. Sur les portes doubles, le second
   battant part avec un léger décalage (et se ferme le premier, l'autre venant se rabattre dessus).

Les engrenages tournent **à la vitesse des battants** (immobiles pendant le déverrouillage, rapides au milieu du
mouvement) et les tiges de piston suivent leur battant. Une porte qui change de sens en plein mouvement repart de là où
elle est, sans saut.

Sons : un déclic au déverrouillage, le son de la porte quand les battants partent, le claquement à la fermeture (plus
doux pour le premier battant d'une porte double), un déclic quand elle est reverrouillée ; les **grandes portes**
grincent (bois) ou cliquettent et grondent (vapeur) toutes les 0,8 s environ pendant que leurs battants bougent ; les
portes à vapeur lâchent une bouffée de vapeur et un sifflement au démarrage (et une petite bouffée à l'arrêt). Rien
n'est joué en boucle ni à chaque tick.

## Poser une porte

* Visez le sol (ou la case) où doit se trouver le **bas de l'ouverture** et faites clic droit avec l'objet.
* La **face avant** de la porte regarde vers vous ; vue de face, l'ouverture est centrée sur la case visée :
  porte de 1 de large = la case visée ; 2 de large = la case visée et celle à sa droite ; 4 de large = de la case à
  gauche de la case visée jusqu'à deux cases à sa droite.
* Toutes les cases de l'ouverture doivent être libres (air, herbe, neige...), sans personne dedans ; sinon rien n'est
  posé et un message dit quel bloc gêne et où.
* Par défaut la porte **s'ouvre vers l'arrière** (loin de celui qui l'a posée) ; `/porte sens ... avant` l'inverse,
  mais c'est **déconseillé** : les dix modèles ont un cadre à feuillure conçu pour l'ouverture vers l'arrière, et vers
  l'avant les battants frottent / traversent visuellement le cadre (le fonctionnement et les collisions restent
  justes). Pour qu'une porte s'ouvre de l'autre côté, posez-la plutôt dans l'autre sens.
* Un administrateur peut aussi la poser par commande : `/porte poser porte_chateau 120 64 -40 sud` (la position est
  la case visée, l'orientation le côté vers lequel regarde la face avant).

Casser **n'importe quelle case** casse toute la porte et rend un seul objet (rien en créatif). Aucune case ne reste
orpheline : une case sans contrôleur disparaît d'elle-même.

## Ouvrir et fermer

* **Clic droit** sur n'importe quelle case (les mêmes règles d'accès partout).
* **Redstone** sur n'importe quelle case : levier ou bouton collé à la porte (posé sur le bloc voisin, contre la
  porte), fil de redstone, bloc de redstone...
* **Leviers liés à distance** : jusqu'à 8 leviers, boutons ou plaques de pression, à 32 blocs au plus de la porte
  (`/porte levier lier`).
* **Commandes** `/porte ouvrir`, `fermer`, `basculer`.

La porte reste ouverte **tant qu'un mécanisme la demande** (OU logique : main, redstone, levier lié, commande
minutée), puis se ferme. Un clic sur une porte tenue ouverte par la redstone affiche « La porte reste ouverte : la
redstone la maintient. »

### Fermeture automatique (1 minute)

Depuis la 1.32.0, **toute porte ouverte au clic, à la clé ou par `/porte ouvrir` sans durée se referme seule au bout
de 60 secondes** (si personne ne se trouve dans le passage : sinon elle attend et réessaie).

* `/porte fermeture <porte> <secondes>` change ce délai pour cette porte (1 à 3600) ; `0` = ne se referme jamais seule.
* Une porte **tenue par la redstone ou un levier lié** reste ouverte tant que le signal est là (quel que soit ce
  délai), puis se referme quand il disparaît.
* `/porte ouvrir <porte> <secondes>` garde sa propre durée.
* Les portes posées en 1.31.0 (fermeture « jamais », l'ancien défaut) passent à 60 s au chargement ; celles dont un
  administrateur avait réglé une autre durée la gardent. Pour qu'une porte reste ouverte indéfiniment (une porte de
  ville ouverte le jour, une salle après un boss), réglez `/porte fermeture <porte> 0` une fois pour toutes.

**Collisions.** Fermée, chaque case est une dalle fine au milieu de l'épaisseur (les projectiles s'y arrêtent aussi) ;
ouverte, plus rien ne bloque dans l'ouverture (pas de bloc invisible). Le contour de visée reste là pour pouvoir
cliquer et refermer. La porte bloque jusqu'à ce que **ses battants soient à mi-ouverture** (le serveur suit la même
courbe que l'animation) ; en se fermant, le passage reste libre jusqu'à ce que les battants soient fermés et immobiles.

**Jamais de fermeture dangereuse.** Si un joueur, un mob ou un véhicule se trouve dans l'ouverture ou dans la zone que
balaient les battants, la porte ne se ferme pas ; s'il y entre pendant la fermeture, elle se rouvre, puis réessaie
deux secondes plus tard. C'est aussi vrai pour la fermeture automatique.

Les mobs ne traversent qu'une porte ouverte (fermée, c'est un mur pour eux).

## Accès

`/porte acces <porte> <mode>` :

| Mode | Clic | Redstone collée | Leviers liés | Commandes |
|---|---|---|---|---|
| `libre` (défaut) | oui | oui | oui | oui |
| `cle` (1.32.0) | seulement avec **une clé de sa serrure** (ou le passe-partout d'un administrateur) | **non** | oui | oui |
| `verrouillee` | **non** (son de coffre verrouillé) | non | oui | oui |
| `levier` | non (« s'ouvre avec un levier ») | oui | oui | oui |
| `admin` | non | non | non | oui |
| `quete <tag>` | seulement les joueurs portant le tag | oui | oui | oui |

* `/porte verrouiller` = accès `verrouillee` et ferme la porte si une main ou une commande l'avait ouverte ;
  `/porte deverrouiller` = accès `libre`.
* La redstone collée est ignorée en accès `cle` : sinon n'importe qui ouvrirait une maison en posant un bouton contre
  sa porte. Les leviers **liés** (par un administrateur) restent pris en compte.
* Le **tag** est un tag de commande vanilla : votre système de quêtes ou votre PNJ le donne avec
  `/tag @p add <tag>` et le retire avec `/tag @p remove <tag>`.
* Le **passe-partout** ouvre toutes les portes quel que soit leur accès, mais seulement pour un administrateur (voir
  plus bas).
* Réglages par porte en plus de l'accès : `/porte manuel <porte> oui|non` (clic permis ou non, clés comprises),
  `/porte redstone <porte> oui|non` (redstone collée **et** leviers liés pris en compte ou non),
  `/porte fermeture <porte> <secondes>` (voir plus haut).
* Une porte qui n'est pas `libre` (donc aussi une porte à clé) est **incassable en survie** sauf pour les
  administrateurs (et en créatif). **Toutes** les portes résistent aux explosions (comme l'obsidienne) et ne peuvent
  pas être poussées par un piston.

## Clés et passe-partout (1.32.0)

### Le principe

* Chaque porte peut avoir une **serrure** : un identifiant tiré au hasard, gardé dans la porte (il n'est jamais envoyé
  aux joueurs).
* Une **clé** (`medievalships:cle`) est **vierge** jusqu'à ce qu'un administrateur la lie à une serrure. Une clé liée
  affiche dans son infobulle **« Ouvre : maison_12 »** (le nom de la porte, ou ses coordonnées `x y z` si elle n'en a
  pas) ; F3+H affiche aussi l'identifiant de la serrure. **Renommée à l'enclume, elle reste valable.**
* Une porte en accès **`cle`** ne s'ouvre (et ne se ferme) au clic que pour un joueur qui a **une clé de cette
  serrure n'importe où dans son inventaire** (main, seconde main, inventaire, emplacements d'armure) : pas besoin de la
  tenir en main. Sinon : **« Vous n'avez pas la clé de cette porte. »** et le son du coffre verrouillé. La clé d'une
  autre porte ne marche pas. L'inventaire n'est regardé qu'au moment du clic (rien ne tourne en permanence).
* Une porte en accès `cle` sans aucune clé distribuée ne s'ouvre au clic que pour l'administrateur et son passe-partout.
* Aucune recette ne fabrique ni ne copie une clé : seul un administrateur en crée (en jeu, ou par commande). Une clé
  ne s'empile pas.
* Le **passe-partout** (`medievalships:cle_universelle`, doré, brillant) ouvre **toutes** les portes, quel que soit
  leur accès (`cle`, `verrouillee`, `levier`, `admin`, `quete`, et même `manuel non`), mais **seulement entre les mains
  d'un administrateur** (n'importe où dans son inventaire, comme une clé) : « Passe-partout : porte ouverte. ». Un
  joueur qui n'est pas administrateur et qui l'aurait récupéré : **« Ce passe-partout ne vous obéit pas. »**

### Les gestes en jeu (administrateurs : `adminPermissionLevel`, opérateurs par défaut)

| Geste | Effet |
|---|---|
| **Clic droit** sur une porte avec une **clé vierge** en main | la clé est liée à la serrure de cette porte (créée si la porte n'en avait pas) et la porte passe en accès `cle` |
| Refaire avec une **autre clé vierge** | un **double** (même serrure) |
| **Accroupi + clic droit** sur une autre porte avec une **clé déjà liée** | cette porte prend **la même serrure** (une seule clé pour la porte de devant et celle de derrière) ; si elle avait déjà une serrure, ses anciennes clés ne l'ouvrent plus |
| **Accroupi + clic droit** avec le **passe-partout** | bascule la porte entre `libre` (tout le monde l'ouvre) et `cle` (seuls les détenteurs de sa clé et le passe-partout) ; depuis un autre accès (verrouillée, quête...), elle passe en `cle` |
| Clic droit avec une clé liée ou le passe-partout (debout) | un clic ordinaire : la porte s'ouvre ou se ferme si la clé est la bonne |

Chaque geste répond par un message dans la barre d'action. Un joueur qui n'est pas administrateur ne peut lier aucune
clé (« Seul un administrateur peut lier une clé à une porte. ») ; accroupi avec **sa** clé, il ouvre simplement sa
porte.

### Les commandes des clés

| Commande | Effet |
|---|---|
| `/porte acces [porte] cle` | accès à clé (crée la serrure si la porte n'en a pas) |
| `/porte cle donner <joueurs> [porte]` | donne à chaque joueur une clé liée à la porte (dans l'inventaire, ou à ses pieds s'il est plein) ; une porte `libre` passe en accès `cle` |
| `/porte serrure changer [porte]` | nouvelle serrure : **les anciennes clés n'ouvrent plus** cette porte |
| `/porte serrure info [porte]` | accès, identifiant de la serrure, libellé que portent ses clés |

### Exemples

**Maison d'un joueur, à la main** : l'administrateur nomme la porte (`/porte nommer maison_12` en la regardant), prend
une clé vierge (onglet « Portes »), fait clic droit sur la porte, et donne la clé au joueur. S'il y a une porte de
derrière : accroupi + clic droit dessus avec une clé déjà liée à `maison_12`, et la même clé ouvre les deux. Les autres
joueurs lisent « Vous n'avez pas la clé de cette porte. ».

**Achat d'une maison auprès d'un PNJ (Easy NPC, action « commande »)** : une fois la porte préparée
(`/porte nommer ... maison_12`, `/porte acces maison_12 cle`), l'action du PNJ après paiement :

```
porte cle donner @p maison_12
```

(comme pour les autres commandes `/porte`, l'action doit s'exécuter avec un niveau de permission suffisant : voir plus
bas). Quand la maison change de propriétaire : `porte serrure changer maison_12`, puis une nouvelle clé au nouveau
propriétaire.

**Récompense de quête** : la clé du donjon donnée à la fin de la quête par l'action de récompense :

```
porte cle donner @p donjon
```

(variante sans objet : l'accès `quete <tag>` décrit plus haut).

**Porte que tout le monde ouvre / porte que seul l'administrateur ouvre** : `libre` pour la première ; pour la
seconde, accroupi + clic droit avec le passe-partout (accès `cle` sans clé distribuée), ou `/porte acces <porte> admin`
si même l'administrateur doit passer par les commandes.

**Clé perdue ou volée** : `/porte serrure changer maison_12` puis `/porte cle donner <joueur> maison_12`. Les autres
portes qui partageaient l'ancienne serrure la gardent : changez-la aussi sur elles (ou refaites le partage, accroupi
avec la nouvelle clé).

## Commandes `/porte` (alias `/door`)

Réservées aux administrateurs (même niveau que `/ship` et `/pontlevis`, `adminPermissionLevel`, 2 par défaut :
opérateurs, blocs de commande, fonctions). Messages en français.

La **porte visée** se donne juste après l'action, de trois façons :

* rien : la porte que vous regardez (16 blocs au plus ; joueur seulement) — `ici` veut dire la même chose ;
* son **nom** (donné par `/porte nommer`) : marche de partout, même si la porte est loin ;
* les **coordonnées** de n'importe laquelle de ses cases : `x y z`.

| Commande | Effet |
|---|---|
| `/porte ouvrir [porte] [secondes]` | ouvre (avec une durée : se referme après, si rien d'autre ne la tient ; sans durée : fermeture automatique de la porte, 60 s par défaut) |
| `/porte fermer [porte]` | ferme (dit ce qui la maintient ouverte s'il y a lieu) |
| `/porte basculer [porte]` | ouvre si fermée, ferme si ouverte |
| `/porte verrouiller [porte]`, `/porte deverrouiller [porte]` | accès `verrouillee` / `libre` |
| `/porte acces [porte] libre\|cle\|verrouillee\|levier\|admin\|quete <tag>` | mode d'accès |
| `/porte cle donner <joueurs> [porte]` | donne une clé liée à la porte |
| `/porte serrure changer [porte]` | nouvelle serrure (les anciennes clés ne l'ouvrent plus) |
| `/porte serrure info [porte]` | serrure et accès de la porte |
| `/porte manuel [porte] oui\|non` | ouverture à la main permise ou non |
| `/porte redstone [porte] oui\|non` | redstone et leviers liés pris en compte ou non |
| `/porte fermeture [porte] <secondes>` | fermeture automatique (60 par défaut, 0 = jamais) |
| `/porte sens [porte] arriere\|avant` | côté vers lequel tournent les battants (`avant` déconseillé : les battants frottent le cadre) |
| `/porte levier lier [porte] <x y z>` | lie un levier / bouton / plaque (8 au plus, 32 blocs au plus) |
| `/porte levier delier [porte] <x y z>\|tous` | délie un levier, ou tous |
| `/porte levier liste [porte]` | leviers liés et leur état |
| `/porte nommer [porte] <nom>` | donne un nom (`aucun` l'enlève) ; un nom = une seule porte |
| `/porte info [porte]` | type, position, état, accès, serrure, réglages, demandes en cours |
| `/porte liste` | toutes les portes connues (les nommées d'abord) |
| `/porte supprimer [porte]` | retire toute la porte, sans objet ni case fantôme |
| `/porte poser <id> [x y z] [nord\|sud\|est\|ouest]` | pose une porte comme l'objet le ferait |

Noms : une lettre puis lettres, chiffres, `_ . -` (32 au plus), en minuscules ; certains mots de la commande sont
interdits (`ici`, `libre`, `cle`, `oui`, `tous`...).

### Exemples

**Bloc de commande** (un bouton sur le bloc de commande ouvre le pont du château 30 secondes) :

```
porte ouvrir pont_chateau 30
```

**Porte de donjon fermée jusqu'à la fin d'une quête** (une fois pour toutes) :

```
porte nommer 120 64 -40 donjon
porte acces donjon quete donjon_ouvert
```

puis, quand le joueur termine la quête, l'action de récompense de votre système de quêtes :

```
tag @p add donjon_ouvert
```

le joueur peut alors ouvrir la porte à la main ; les autres non.

**PNJ (Easy NPC, action « commande »)** : un garde qui ouvre la porte de la ville pendant 20 secondes quand on lui
parle :

```
porte ouvrir porte_ville 20
```

L'action doit s'exécuter avec un niveau de permission suffisant (niveau 2 par défaut, voir `adminPermissionLevel`) :
réglez l'action pour qu'elle s'exécute « en tant que serveur » / avec les droits d'opérateur selon votre mod de PNJ.

**Boss** : la salle se ferme à l'arrivée du boss et se rouvre à sa mort (fonctions ou blocs de commande de votre
système d'événements). La porte doit rester ouverte après le boss : sa fermeture automatique est coupée une fois pour
toutes :

```
porte fermeture salle_boss 0
...
porte acces salle_boss admin
porte fermer salle_boss
...
porte ouvrir salle_boss
porte acces salle_boss libre
```

**Herse de prison commandée par un levier dans la salle des gardes** :

```
porte acces cellule_1 levier
porte levier lier cellule_1 130 65 -52
```

## Réglages du serveur

Dans `config/medievalships.json`, section `server` (lus aussi par chaque client dans son propre fichier, comme pour
les tentes) :

* `doorDetailDistance` (32 blocs) : au-delà, les petits détails des modèles (os `detail`) ne sont plus dessinés ;
* `doorRenderDistance` (64 blocs) : au-delà, la porte n'est plus dessinée ;
* `adminPermissionLevel` (2) : qui est administrateur pour les commandes, les gestes des clés et le passe-partout.

## Performances

* Au repos, une porte ne coûte rien : son ticker sort immédiatement. Il ne travaille que pendant un mouvement (les
  collisions, les sons du mouvement, la recherche d'entités **seulement pendant la fermeture**), pendant une minuterie
  (ouverture minutée, fermeture automatique, nouvel essai après une fermeture empêchée), et tous les 4 ticks si des
  leviers sont liés (leur bloc n'est lu que si son chunk est chargé : **aucun chunk n'est chargé ni forcé**).
* Les clés ne coûtent rien hors des clics : l'inventaire du joueur n'est parcouru qu'au clic sur une porte qui le
  refuserait sans clé.
* Les clients calculent eux-mêmes le mouvement entre deux ticks à partir de l'état envoyé au début du mouvement
  (cible, tick de départ, progression de départ) : **aucun paquet par tick**.
* Le cadre est un maillage statique cuit une fois ; les battants et pièces mobiles sont cuits aussi et seulement
  tournés / déplacés au dessin ; la porte n'est pas dessinée hors de la vue ni au-delà de `doorRenderDistance`.
* Une face vue de dos est écartée avant d'être envoyée à la carte graphique quand l'envers de son cube la cache
  (comme pour les tentes), pour le cadre comme pour les battants qui tournent. Les modèles 1.32.0 n'ont plus de faces
  superposées (dans aucun sens) : plus de scintillement (z-fighting).

## Pour les créateurs de modèles

Modèle `assets/medievalships/models/entity/<id>.bbmodel`, texture propre `textures/entity/<id>.png`, icône
`textures/item/<id>.png` (générateurs `tools/doors/` ; icônes des clés : `tools/keys/generate_key_icons.py`). Repère :
origine au milieu du bas de l'ouverture, au milieu de l'épaisseur ; x vers la droite vue de face, y vers le haut,
+z = face avant. Os : `frame` (fixe), `leaf_l`, `leaf_r` (pivot sur la charnière, lu dans le modèle), `gear_a_*` (sens
horaire vu de face), `gear_b_*` (anti-horaire), qui tournent avec leur battant (ceux du cadre avec la moyenne des deux),
`bolt_*` (glissent de 0,25 bloc le long de x, en s'éloignant du milieu de leur battant, pendant le déverrouillage : les
15 premiers % du mouvement), `piston_*` (montent de 0,25 bloc avec leur battant), `handle_*` (anneaux, poignées,
volants : tournent autour de l'axe z de leur pivot, sens horaire vu de face sous `leaf_l` (et `frame`), anti-horaire
sous `leaf_r` (en miroir), 30° pendant le déverrouillage puis
reviennent ; 180° sur les portes à vapeur ; `ring_*`, `poignee_*`, `anneau_*` sont lus de même), cubes `glow*` en
pleine lumière, os `detail` masqués de loin. Une face dont le cube a la face opposée n'est pas dessinée vue de dos ;
une face sans face opposée (retirée parce qu'un cube voisin la cache) est dessinée des deux côtés. Pas de faces
superposées : deux faces dans le même plan scintillent, quel que soit leur sens. Les modèles et textures se rechargent
avec les packs de ressources (F3+T) ; un modèle absent n'est simplement pas dessiné (la porte fonctionne quand même).

## Limites (honnêtes)

* Les portes ne se posent pas sur un navire en mouvement (ce sont des blocs du monde).
* Une porte n'est pas « étanche » : l'eau ne la traverse pas (blocs pleins pour l'eau), mais rien n'est fait pour la
  lumière (elle passe comme à travers une porte vanilla).
* `/porte liste` ne connaît que les portes posées avec l'objet ou `/porte poser`, et celles dont le chunk a été chargé
  depuis ; une porte retirée par un outil externe qui ne prévient pas le jeu reste dans la liste jusqu'à ce qu'une
  commande la vise (elle est alors retirée).
* Une commande visant une porte **nommée** loin de tout joueur lit son chunk pour l'occasion (sans le garder chargé) :
  la porte change d'état et l'aura pris quand quelqu'un arrivera.
* Les mobs ne savent pas ouvrir ces portes (pas d'IA de villageois pour elles).
* Le sens des pênes (`bolt_*`) suit la règle ci-dessus ; si un modèle les veut dans l'autre sens, c'est au modèle de
  placer ses pênes en conséquence.
* Clés : une clé rangée dans un sac (bundle) ou une boîte de Shulker n'est pas vue (seul l'inventaire du joueur
  compte). Le libellé « Ouvre : ... » est celui de la porte au moment où la clé a été liée (renommer la porte ensuite
  ne change pas les clés déjà faites ; elles ouvrent toujours). `/porte serrure changer` ne change que la porte visée,
  pas les autres portes qui partageaient sa serrure. Un joueur en mode **aventure** qui s'accroupit avec une clé en main
  n'ouvre rien (le jeu n'utilise pas les objets en aventure) : debout, ou la clé dans l'inventaire, ça marche.
  En créatif, un joueur peut obtenir n'importe quel objet : le mode créatif est réservé aux administrateurs.
* Une porte de la 1.31.0 dont un administrateur avait explicitement réglé `/porte fermeture ... 0` ne se distingue pas
  du défaut de l'époque : elle passe aussi à 60 s (refaire `/porte fermeture <porte> 0`).
* Testé : JUnit (types, empreinte et orientation, chronologie des collisions sur la courbe, courbe d'animation
  (bornes, phases, inertie, dépassement et rebond, décalage du second battant, engrenages, demi-tour sans saut, sons),
  accès, clés (liée, vierge, autre serrure, passe-partout, administrateur ou non, gestes), fermeture automatique et
  migration des portes 1.31.0, OU logique) ; les tests en jeu (`DoorGameTest` : pose des trois tailles, refus, quatre
  orientations, clic, redstone, levier lié, animation vue du client et photos de la grande porte au quart, à mi-course et
  aux trois quarts, collisions, commandes, verrouillage, quête, clés, passe-partout, serrure partagée et changée,
  fermeture automatique, anti-écrasement, suppression, redémarrage (serrures et clés gardées), serveur dédié) tournent
  dans l'intégration continue ; voir le rapport de la CI pour leur résultat. Le refus du passe-partout à un
  non-administrateur y est simulé en relevant le niveau d'administrateur le temps du clic.
