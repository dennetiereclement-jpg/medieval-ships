# Les dix portes animées (1.31.0, clés 1.32.0, animation et « 1 clé = 1 porte » 1.33.0)

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
| `porte_chene` | Porte en chêne | 2 x 1 | 1 | 0,8 s | bois |
| `porte_prison` | Porte de prison | 2 x 1 | 1 (pêne animé) | 0,8 s | fer |
| `porte_vapeur` | Porte à vapeur | 2 x 1 | 1 | 0,8 s | fer + piston, vapeur |
| `porte_grange` | Porte de grange | 4 x 2 | 2 | 1,4 s | bois (plus grave, un grincement) |
| `porte_forteresse` | Porte de forteresse | 4 x 2 | 2 | 1,4 s | bois (plus grave, un grincement) |
| `porte_industrielle` | Porte industrielle | 4 x 2 | 2 | 1,4 s | fer + piston, vapeur |
| `porte_marchande` | Porte marchande | 4 x 2 | 2 | 1,4 s | bois (plus grave, un grincement) |
| `porte_chateau` | Porte de château | 6 x 4 | 2 | 4 s | bois (grave, lourd, grincements, choc sourd) |
| `porte_vapeur_grande` | Grande porte à vapeur | 6 x 4 | 2 | 4 s | fer + piston, vapeur, engrenages |
| `porte_entrepot` | Porte d'entrepôt | 6 x 4 | 2 | 4 s | bois (grave, lourd, grincements, choc sourd) |

(Durée d'un mouvement complet, ouverture ou fermeture : 16, 28 et 80 ticks depuis la 1.33.0 ; 12, 24 et 70 avant.)

Elles sont dans l'onglet créatif **« Portes »**, avec la **clé** (`medievalships:cle`) et le **passe-partout**
(`medievalships:cle_universelle`). Les fenêtres, hublots et lanternes des modèles sont éclairés.

### L'animation (1.33.0)

Chaque mouvement est calculé image par image par chaque client (aucun paquet par tick), sur la même courbe que celle
du serveur (collisions, sons). Il se déroule ainsi :

1. **à l'ouverture, le déverrouillage** (19 % de la durée pour les petites portes, 16 % pour les moyennes, 11 % pour
   les grandes) : les anneaux et poignées tournent (sens horaire vu de face, en miroir sur le battant droit, 30° au
   plus ; le volant des portes à vapeur fait un demi-tour), puis les pênes glissent et le loquet se libère avec un
   claquement métallique ; les battants attendent ;
2. **la poussée, puis l'élan** : les battants partent d'une poussée (leur vitesse monte vite), puis glissent sur leur
   élan en ralentissant jusqu'à la butée, qu'ils atteignent à vitesse nulle : **ni dépassement, ni rebond, ni
   tremblement**. Plus la porte est lourde, plus elle démarre lentement et plus elle glisse longtemps : la petite porte,
   légère, part vite et s'arrête vite ; la porte moyenne glisse plus longtemps ; la grande porte s'ébranle lentement,
   puis son inertie la porte sur près de deux secondes ;
3. **à la fermeture** : départ doux, puis les battants prennent de la vitesse jusqu'au cadre et **claquent** (le moment
   le plus rapide du mouvement) ; ils rebondissent à peine (2,3° au plus pour une petite porte, 1,6° pour une moyenne,
   à peine 1° pour une grande, puis un second rebond huit fois plus petit, puis plus rien), les anneaux tressautent un instant sous le
   choc, puis la porte se verrouille : les anneaux tournent et les pênes rentrent ;
4. sur les portes doubles, le second battant part un peu après le premier (10 % de la course pour les portes moyennes,
   12 % pour les grandes) et, à la fermeture, se ferme le premier : l'autre vient se rabattre dessus.

Les engrenages tournent **à la vitesse des battants** (immobiles pendant le déverrouillage, rapides au plus fort du
mouvement, ils suivent même le petit rebond) et les tiges de piston suivent leur battant.

**Sans à-coups (1.33.0).**

* Le client dessine avec sa propre horloge, qui suit l'heure du serveur en douceur : le recalage de l'heure que le
  serveur envoie chaque seconde (en avance ou en retard, surtout quand le serveur rame) ne fait plus sauter les portes.
  (Mesuré en simulation : sur un serveur à 15 ticks par seconde, un battant de grande porte reculait jusqu'à 17° d'un
  coup en 1.32.0 ; il ne recule plus jamais, son plus grand pas d'une image à la suivante est de 0,8°.)
* Quand un nouveau mouvement arrive (clic, redstone, levier, demi-tour), le client part de ce qu'il dessinait, position
  et vitesse comprises, et rejoint le nouveau mouvement en douceur (en un quart de la durée de la porte, 5 à 12 ticks) :
  aucun saut, même si son horloge n'est pas exactement celle du serveur.
* Une porte qui change de sens en plein mouvement repart de là où sont ses battants, sur la courbe de son nouveau sens
  (le serveur reprend la courbe au point où les battants sont aussi ouverts) : ni saut, ni fermeture précipitée ; à
  l'écran, le battant ralentit, s'arrête et repart dans l'autre sens.

**Sons**, chacun au tick de la courbe auquel il correspond : un petit déclic quand les anneaux commencent à tourner, le
claquement métallique du loquet quand les pênes sont sortis, le son de la porte quand les battants quittent le cadre
(et, pour les portes à vapeur, le piston, le sifflement et la bouffée de vapeur à ce moment-là), des grincements le
long de la course (un pour les portes moyennes en bois, quatre pour les grandes, espacés, jamais sur le claquement),
rien à la butée (elle est amortie ; une petite bouffée pour les portes à vapeur). À la fermeture : les grincements, le
claquement (plus doux pour le premier battant d'une porte double ; avec un choc sourd pour les grandes portes), le
déclic du loquet quand les battants se sont posés après leur petit rebond, puis le claquement des pênes. Rien n'est
joué en boucle ni à chaque tick.

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
| `cle` (1.32.0) | seulement avec **une clé de cette porte** (ou le passe-partout d'un administrateur) | **non** | oui | oui |
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

## Clés et passe-partout (1.32.0 ; une clé = une porte depuis la 1.33.0)

### Le principe

* Chaque porte peut avoir une **serrure** : un identifiant tiré au hasard, gardé dans la porte (il n'est jamais envoyé
  aux joueurs).
* Une **clé** (`medievalships:cle`) est **vierge** jusqu'à ce qu'un administrateur la lie à une porte. Une clé liée
  affiche dans son infobulle **« Ouvre uniquement : maison_12 »** (le nom de la porte, ou ses coordonnées `x y z` si
  elle n'en a pas) ; F3+H affiche aussi l'identifiant de la serrure et la porte (dimension et position). **Renommée à
  l'enclume, elle reste valable.**
* **Une clé = une porte (1.33.0).** Une clé n'ouvre que **la porte à laquelle elle a été liée** : la serrure **et** la
  porte elle-même (sa dimension et la position de son contrôleur, gardées dans la clé) doivent correspondre. Même deux
  portes qui auraient la même serrure (une porte de derrière qui partageait la serrure en 1.32.0, un bloc copié avec
  ses données, une structure dupliquée) ne s'ouvrent pas avec la même clé. **Chaque porte a sa propre serrure** : quand
  un administrateur lie une clé à une porte dont la serrure sert aussi à une autre porte, cette porte reçoit une
  nouvelle serrure (le message le dit ; les anciennes clés de la 1.32.0 ne l'ouvrent alors plus).
* Une porte en accès **`cle`** ne s'ouvre (et ne se ferme) au clic que pour un joueur qui a **une clé de cette porte
  n'importe où dans son inventaire** (main, seconde main, inventaire, emplacements d'armure) : pas besoin de la tenir en
  main. Sinon : **« Vous n'avez pas la clé de cette porte. »** et le son du coffre verrouillé. La clé d'une autre porte
  ne marche pas. L'inventaire n'est regardé qu'au moment du clic (rien ne tourne en permanence).
* **Les clés de la 1.32.0** ne connaissent que leur serrure : elles continuent d'ouvrir leur porte, et **la première
  porte qu'une telle clé ouvre devient la sienne** (elle est alors liée à cette porte, et à elle seule ; d'ici là, son
  infobulle dit « Clé de la 1.32.0 : elle sera liée à la première porte qu'elle ouvrira. »).
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
| **Clic droit** sur une porte avec une **clé vierge** en main | la clé est liée à cette porte et à elle seule (sa serrure est créée si elle n'en avait pas, renouvelée si une autre porte avait la même) et la porte passe en accès `cle` : « Clé liée à la porte « maison_12 » : elle n'ouvre que cette porte (seuls ses détenteurs et le passe-partout l'ouvrent). » |
| Refaire avec une **autre clé vierge** | un **double** : un autre exemplaire de la clé de cette même porte (« Double de la clé de la porte « maison_12 » : il n'ouvre que cette porte. ») |
| **Accroupi + clic droit** sur une autre porte avec une **clé déjà liée** | refusé, rien ne change : « Cette clé est déjà liée à « maison_12 ». Une clé n'ouvre qu'une seule porte. » (ou « … à la porte en 120 64 -40. … » pour une porte sans nom) |
| **Accroupi + clic droit** sur sa propre porte avec sa clé | « Cette clé ouvre déjà cette porte. » |
| **Accroupi + clic droit** avec le **passe-partout** | bascule la porte entre `libre` (tout le monde l'ouvre) et `cle` (seuls les détenteurs de sa clé et le passe-partout) ; depuis un autre accès (verrouillée, quête...), elle passe en `cle` |
| Clic droit avec une clé liée ou le passe-partout (debout) | un clic ordinaire : la porte s'ouvre ou se ferme si la clé est la bonne |

Chaque geste répond par un message dans la barre d'action. Un joueur qui n'est pas administrateur ne peut lier aucune
clé (« Seul un administrateur peut lier une clé à une porte. ») ; accroupi avec **sa** clé, il ouvre simplement sa
porte.

### Les commandes des clés

| Commande | Effet |
|---|---|
| `/porte acces [porte] cle` | accès à clé (crée la serrure si la porte n'en a pas) |
| `/porte cle donner <joueurs> [porte]` | donne à chaque joueur une clé liée à cette porte et à elle seule (dans l'inventaire, ou à ses pieds s'il est plein) ; une porte `libre` passe en accès `cle` ; une porte dont la serrure sert aussi à une autre reçoit d'abord la sienne |
| `/porte serrure changer [porte]` | nouvelle serrure : **les anciennes clés n'ouvrent plus** cette porte |
| `/porte serrure info [porte]` | accès, identifiant de la serrure, libellé et porte que portent ses clés, nombre de clés liées depuis la 1.33.0, autres portes qui auraient la même serrure |

### Exemples

**Maison d'un joueur, à la main** : l'administrateur nomme la porte (`/porte nommer maison_12` en la regardant), prend
une clé vierge (onglet « Portes »), fait clic droit sur la porte, et donne la clé au joueur. S'il y a une porte de
derrière : une clé = une porte, il la nomme (`maison_12_arriere`), lie une **seconde** clé vierge à cette porte-là et
donne les deux clés au joueur. Les autres joueurs lisent « Vous n'avez pas la clé de cette porte. ».

**Achat d'une maison auprès d'un PNJ (Easy NPC, action « commande »)** : une fois la porte préparée
(`/porte nommer ... maison_12`, `/porte acces maison_12 cle`), l'action du PNJ après paiement :

```
porte cle donner @p maison_12
```

(et, s'il y a une porte de derrière, une seconde action `porte cle donner @p maison_12_arriere` : une clé par porte ;
comme pour les autres commandes `/porte`, l'action doit s'exécuter avec un niveau de permission suffisant : voir plus
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

**Clé perdue ou volée** : `/porte serrure changer maison_12` puis `/porte cle donner <joueur> maison_12`. Une clé
n'ouvre que sa porte : les autres portes ne sont pas concernées.

**Maison dont les deux portes partageaient une serrure en 1.32.0** : rien ne casse, chaque ancienne clé ouvre encore la
première des deux portes qu'elle ouvre (et devient sa clé). Pour que le joueur ait les deux, donnez-lui une clé de la
seconde porte (`/porte cle donner <joueur> maison_12_arriere`) : comme sa serrure sert aussi à l'autre porte, elle en
reçoit une nouvelle à ce moment-là (les anciennes clés partagées ne l'ouvrent alors plus ; elles ouvrent toujours la
porte de devant).

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
| `/porte cle donner <joueurs> [porte]` | donne une clé liée à cette porte (elle n'ouvre qu'elle) |
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
  (cible, tick de départ, progression de départ), avec leur horloge lissée : **aucun paquet par tick**, et rien de plus
  par image qu'en 1.32.0 (quelques calculs de courbe par porte visible).
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
`bolt_*` (glissent de 0,25 bloc le long de x, en s'éloignant du milieu de leur battant, pendant le déverrouillage au
début de l'ouverture, et reviennent pendant le verrouillage à la fin de la fermeture), `piston_*` (montent de 0,25 bloc
avec leur battant), `handle_*` (anneaux, poignées, volants : tournent autour de l'axe z de leur pivot, sens horaire vu
de face sous `leaf_l` (et `frame`), anti-horaire sous `leaf_r` (en miroir), 30° pendant le déverrouillage puis
reviennent quand les battants partent, tressautent de quelques degrés au claquement, tournent de nouveau pendant le
verrouillage ; 180° sur les portes à vapeur, sans tressauter ; `ring_*`, `poignee_*`, `anneau_*` sont lus de même), cubes `glow*` en
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
  compte). Le libellé « Ouvre uniquement : ... » est celui de la porte au moment où la clé a été liée (renommer la porte
  ensuite ne change pas les clés déjà faites ; elles ouvrent toujours). Une clé est liée à la porte par sa position :
  une porte cassée puis reposée au même endroit est une nouvelle porte, avec une nouvelle serrure, que les anciennes
  clés n'ouvrent pas. Les portes dont le chunk n'a pas été chargé depuis la 1.33.0 ne sont pas encore connues avec leur
  serrure : si l'une d'elles partageait sa serrure, c'est elle (et non l'autre) qui en recevra une nouvelle quand une clé
  lui sera liée. Un joueur en mode **aventure** qui s'accroupit avec une clé en main n'ouvre rien (le jeu n'utilise pas
  les objets en aventure) : debout, ou la clé dans l'inventaire, ça marche. En créatif, un joueur peut obtenir n'importe
  quel objet (même une clé déjà liée, en connaissant sa serrure et sa porte) : le mode créatif est réservé aux
  administrateurs.
* Une porte de la 1.31.0 dont un administrateur avait explicitement réglé `/porte fermeture ... 0` ne se distingue pas
  du défaut de l'époque : elle passe aussi à 60 s (refaire `/porte fermeture <porte> 0`).
* Testé : JUnit (types, empreinte et orientation, chronologie des collisions sur la courbe, courbe d'animation 1.33.0
  (bornes, jamais au-delà de la butée, déverrouillage puis poussée et élan, arrivée amortie, départ plus lent et
  glissade plus longue des portes lourdes, fermeture qui accélère jusqu'au claquement, deux petits rebonds amortis,
  anneaux qui tressautent, décalage du second battant, engrenages, demi-tour sans saut ni précipitation, sons au bon
  tick), horloge du client (serveur lent, rapide, paquets irréguliers : jamais de retour en arrière, allure entre 0,7 et
  1,3, continuité d'un tick à l'autre), suivi du client (aucun saut à l'arrivée d'un paquet ni au demi-tour, vitesse
  conservée), accès, clés (une clé = une porte : même serrure sur une autre porte refusée, autre dimension refusée,
  clés de la 1.32.0 liées à la première porte, serrure propre à chaque porte, passe-partout, gestes et message de la
  clé déjà liée), fermeture automatique et migration des portes 1.31.0, OU logique) ; les tests en jeu (`DoorGameTest` :
  pose des trois tailles, refus, quatre orientations, clic, redstone, levier lié, animation vue du client et photos de
  la grande porte au quart, à mi-course et aux trois quarts, **douze photos régulières de l'ouverture puis de la
  fermeture d'une porte moyenne et d'une grande porte** (`portes_anim_<id>_<ouv|ferm>_<nn>`, avec la pose dessinée par
  le client vérifiée à chaque photo), collisions, commandes, verrouillage, quête, clés (clé refusée sur une seconde
  porte de même serrure, clé de la 1.32.0, plus de partage, serrure renouvelée), passe-partout, serrure changée,
  fermeture automatique, anti-écrasement, suppression, redémarrage (serrures et clés gardées), serveur dédié) tournent
  dans l'intégration continue ; voir le rapport de la CI pour leur résultat. Le refus du passe-partout à un
  non-administrateur y est simulé en relevant le niveau d'administrateur le temps du clic. Non vérifié à l'œil en jeu
  par l'auteur de la 1.33.0 : la courbe a été regardée sur des graphiques et des GIF rendus image par image avec les
  modèles (outil de prévisualisation), pas dans un vrai client.
