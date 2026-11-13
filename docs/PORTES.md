# Les dix portes animées (1.31.0)

Dix portes médiévales à poser dans vos murs, châteaux, prisons, entrepôts et villes : de vrais battants qui
tournent sur leurs charnières, des collisions qui suivent la porte, la redstone, des leviers liés à distance, des
accès (verrouillée, quête...) et des commandes `/porte` pour les blocs de commande, les PNJ et les quêtes.

Rien n'est généré dans le monde : aucune porte n'apparaît seule, aucun village n'est modifié, les portes vanilla ne
changent pas. Chaque porte n'a **aucune entité** : un bloc contrôleur (avec ses données) et des blocs invisibles pour
les autres cases de l'ouverture ; tout est dessiné par le contrôleur.

## Les dix portes

| Objet (`/give @p medievalships:<id>`) | Nom | Ouverture (haut x large) | Battants | Durée | Son |
|---|---|---|---|---|---|
| `porte_chene` | Porte en chêne | 2 x 1 | 1 | 0,5 s | bois |
| `porte_prison` | Porte de prison | 2 x 1 | 1 (pêne animé) | 0,5 s | fer |
| `porte_vapeur` | Porte à vapeur | 2 x 1 | 1 | 0,5 s | fer + piston, vapeur |
| `porte_grange` | Porte de grange | 4 x 2 | 2 | 1 s | bois (plus grave) |
| `porte_forteresse` | Porte de forteresse | 4 x 2 | 2 | 1 s | bois (plus grave) |
| `porte_industrielle` | Porte industrielle | 4 x 2 | 2 | 1 s | fer + piston, vapeur |
| `porte_marchande` | Porte marchande | 4 x 2 | 2 | 1 s | bois (plus grave) |
| `porte_chateau` | Porte de château | 6 x 4 | 2 | 3 s | bois (grave, lourd) |
| `porte_vapeur_grande` | Grande porte à vapeur | 6 x 4 | 2 | 3 s | fer + piston, vapeur |
| `porte_entrepot` | Porte d'entrepôt | 6 x 4 | 2 | 3 s | bois (grave, lourd) |

Elles sont dans l'onglet créatif **« Portes »**. Les engrenages, pênes et pistons des modèles ne bougent que pendant
le mouvement ; les fenêtres, hublots et lanternes sont éclairés. Les portes à vapeur lâchent quelques nuages au début
et à la fin du mouvement (rien de permanent).

## Poser une porte

* Visez le sol (ou la case) où doit se trouver le **bas de l'ouverture** et faites clic droit avec l'objet.
* La **face avant** de la porte regarde vers vous ; vue de face, l'ouverture est centrée sur la case visée :
  porte de 1 de large = la case visée ; 2 de large = la case visée et celle à sa droite ; 4 de large = de la case à
  gauche de la case visée jusqu'à deux cases à sa droite.
* Toutes les cases de l'ouverture doivent être libres (air, herbe, neige...), sans personne dedans ; sinon rien n'est
  posé et un message dit quel bloc gêne et où.
* Par défaut la porte **s'ouvre vers l'arrière** (loin de celui qui l'a posée) ; `/porte sens ... avant` l'inverse.
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

**Collisions.** Fermée, chaque case est une dalle fine au milieu de l'épaisseur (les projectiles s'y arrêtent aussi) ;
ouverte, plus rien ne bloque dans l'ouverture (pas de bloc invisible). Le contour de visée reste là pour pouvoir
cliquer et refermer. La porte bloque jusqu'à mi-ouverture ; en se fermant, le passage reste libre jusqu'à la fin.

**Jamais de fermeture dangereuse.** Si un joueur, un mob ou un véhicule se trouve dans l'ouverture ou dans la zone que
balaient les battants, la porte ne se ferme pas ; s'il y entre pendant la fermeture, elle se rouvre, puis réessaie
deux secondes plus tard.

Les mobs ne traversent qu'une porte ouverte (fermée, c'est un mur pour eux).

## Accès

`/porte acces <porte> <mode>` :

| Mode | Clic | Redstone collée | Leviers liés | Commandes |
|---|---|---|---|---|
| `libre` (défaut) | oui | oui | oui | oui |
| `verrouillee` | **non** (son de coffre verrouillé) | non | oui | oui |
| `levier` | non (« s'ouvre avec un levier ») | oui | oui | oui |
| `admin` | non | non | non | oui |
| `quete <tag>` | seulement les joueurs portant le tag | oui | oui | oui |

* `/porte verrouiller` = accès `verrouillee` et ferme la porte si une main ou une commande l'avait ouverte ;
  `/porte deverrouiller` = accès `libre`.
* Le **tag** est un tag de commande vanilla : votre système de quêtes ou votre PNJ le donne avec
  `/tag @p add <tag>` et le retire avec `/tag @p remove <tag>`. Il n'y a pas de système de clés.
* Réglages par porte en plus de l'accès : `/porte manuel <porte> oui|non` (clic permis ou non),
  `/porte redstone <porte> oui|non` (redstone collée **et** leviers liés pris en compte ou non),
  `/porte fermeture <porte> <secondes>` (se referme seule après une ouverture à la main ou par `/porte ouvrir` ;
  `0` = jamais, défaut).
* Une porte qui n'est pas `libre` est **incassable en survie** sauf pour les administrateurs (et en créatif).
  **Toutes** les portes résistent aux explosions (comme l'obsidienne) et ne peuvent pas être poussées par un piston.

## Commandes `/porte` (alias `/door`)

Réservées aux administrateurs (même niveau que `/ship` et `/pontlevis`, `adminPermissionLevel`, 2 par défaut :
opérateurs, blocs de commande, fonctions). Messages en français.

La **porte visée** se donne juste après l'action, de trois façons :

* rien : la porte que vous regardez (16 blocs au plus ; joueur seulement) — `ici` veut dire la même chose ;
* son **nom** (donné par `/porte nommer`) : marche de partout, même si la porte est loin ;
* les **coordonnées** de n'importe laquelle de ses cases : `x y z`.

| Commande | Effet |
|---|---|
| `/porte ouvrir [porte] [secondes]` | ouvre (avec une durée : se referme après, si rien d'autre ne la tient) |
| `/porte fermer [porte]` | ferme (dit ce qui la maintient ouverte s'il y a lieu) |
| `/porte basculer [porte]` | ouvre si fermée, ferme si ouverte |
| `/porte verrouiller [porte]`, `/porte deverrouiller [porte]` | accès `verrouillee` / `libre` |
| `/porte acces [porte] libre\|verrouillee\|levier\|admin\|quete <tag>` | mode d'accès |
| `/porte manuel [porte] oui\|non` | ouverture à la main permise ou non |
| `/porte redstone [porte] oui\|non` | redstone et leviers liés pris en compte ou non |
| `/porte fermeture [porte] <secondes>` | fermeture automatique (0 = jamais) |
| `/porte sens [porte] arriere\|avant` | côté vers lequel tournent les battants |
| `/porte levier lier [porte] <x y z>` | lie un levier / bouton / plaque (8 au plus, 32 blocs au plus) |
| `/porte levier delier [porte] <x y z>\|tous` | délie un levier, ou tous |
| `/porte levier liste [porte]` | leviers liés et leur état |
| `/porte nommer [porte] <nom>` | donne un nom (`aucun` l'enlève) ; un nom = une seule porte |
| `/porte info [porte]` | type, position, état, accès, réglages, demandes en cours |
| `/porte liste` | toutes les portes connues (les nommées d'abord) |
| `/porte supprimer [porte]` | retire toute la porte, sans objet ni case fantôme |
| `/porte poser <id> [x y z] [nord\|sud\|est\|ouest]` | pose une porte comme l'objet le ferait |

Noms : une lettre puis lettres, chiffres, `_ . -` (32 au plus), en minuscules ; certains mots de la commande sont
interdits (`ici`, `libre`, `oui`, `tous`...).

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
système d'événements) :

```
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
* `doorRenderDistance` (64 blocs) : au-delà, la porte n'est plus dessinée.

## Performances

* Au repos, une porte ne coûte rien : son ticker sort immédiatement. Il ne travaille que pendant un mouvement (les
  collisions à mi-course et à la fin, la recherche d'entités **seulement pendant la fermeture**), pendant une minuterie
  (ouverture minutée, fermeture automatique, nouvel essai après une fermeture empêchée), et tous les 4 ticks si des
  leviers sont liés (leur bloc n'est lu que si son chunk est chargé : **aucun chunk n'est chargé ni forcé**).
* Les clients calculent eux-mêmes le mouvement entre deux ticks à partir de l'état envoyé au début du mouvement
  (cible, tick de départ, progression de départ) : **aucun paquet par tick**.
* Le cadre est un maillage statique cuit une fois ; les battants et pièces mobiles sont cuits aussi et seulement
  tournés / déplacés au dessin ; la porte n'est pas dessinée hors de la vue ni au-delà de `doorRenderDistance`.

## Pour les créateurs de modèles

Modèle `assets/medievalships/models/entity/<id>.bbmodel`, texture propre `textures/entity/<id>.png`, icône
`textures/item/<id>.png` (générateurs `tools/doors/`). Repère : origine au milieu du bas de l'ouverture, au milieu de
l'épaisseur ; x vers la droite vue de face, y vers le haut, +z = face avant. Os : `frame` (fixe), `leaf_l`, `leaf_r`
(pivot sur la charnière, lu dans le modèle), `gear_a_*` (sens horaire vu de face), `gear_b_*` (anti-horaire),
`bolt_*` (glissent de 0,25 bloc le long de x, en s'éloignant du milieu de leur battant, pendant le premier cinquième de
l'ouverture), `piston_*` (montent de 0,25 bloc avec l'ouverture), cubes `glow*` en pleine lumière, os `detail`
masqués de loin. Les modèles et textures se rechargent avec les packs de ressources (F3+T) ; un modèle absent n'est
simplement pas dessiné (la porte fonctionne quand même).

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
* Testé : JUnit (types, empreinte et orientation, chronologie des collisions, courbe, accès, OU logique) ; les tests en
  jeu (`DoorGameTest` : pose des trois tailles, refus, quatre orientations, clic, redstone, levier lié, animation vue du
  client, collisions, commandes, verrouillage, quête, anti-écrasement, suppression, redémarrage, serveur dédié) tournent
  dans l'intégration continue ; voir le rapport de la CI pour leur résultat.
