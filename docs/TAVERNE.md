# Taverne nomade (un bloc = une taverne) et sièges

La **taverne nomade** (`taverne_nomade`, en anglais *Nomad Tavern*, 1.19.0) est une grande roulotte-taverne
médiévale pour une place de village, un camp de route ou une foire. Comme les [charrettes](CHARRETTES.md) et les
[tentes](TENTES.md), **c'est UN seul bloc** : on pose le bloc, toute la taverne est dessinée à partir de lui, comme un
seul modèle statique. Elle est rangée avec les charrettes (onglet créatif **Charrettes**, en dernier ; objet
`medievalships:taverne_nomade`, piles de 16).

Nouveauté de cette version : **on peut s'asseoir** sur ses tabourets et ses bancs. Le même système marche pour tout
objet en un bloc dont le fichier décrit des sièges (le banc de l'[aire d'entraînement aux tatamis](ENTRAINEMENT.md)
aussi).

## Ce qu'on y trouve

D'après l'image de référence (`ref/taverne_nomade_ref.png`), environ 13 x 10 blocs au sol :

- une **grande roulotte de bois** sur grandes **roues à rayons cerclées de fer**, au **toit de toile arrondi** sur
  arceaux (pièces rouges et beiges, lierre sur le dessus, caisses et un coffre sur le toit) ;
- une **cheminée de pierre** qui fume (rarement : particule de feu de camp), une fenêtre en arc et une **porte avec
  ses marches** à l'extrémité gauche ;
- sur le long côté tourné vers l'avant, un grand **comptoir de taverne** ouvert : étagères de bouteilles, petits
  tonneaux à robinet, chopes sur le comptoir, lanternes ;
- des **bannières rouges à la chope de bière** dorée, un **auvent rayé** rouge et beige à festons sur poteaux vers la
  droite, une **enseigne carrée à la chope** pendue à un poteau ;
- devant, une **terrasse** : plusieurs **tables carrées** avec chopes, bouteilles et lanternes, des **tabourets**
  autour (ce sont les sièges), un **tapis** rouge à motifs, des tonneaux, un sac, des caisses ;
- à droite, un **feu de camp** dans un cercle de pierres avec un **chaudron noir** pendu à un trépied (lueur, flammes
  et fumée de temps en temps).

Le modèle, sa texture, ses meubles de mods de décoration (tabourets, tables, tonneaux, bouteilles, tapis : voir
`tools/tavern/generate_taverne_nomade.py`), ses boîtes de collision (roulotte, roues, comptoir, tables, tabourets bas,
tonneaux, cercle du feu, poteaux ; la terrasse entre les tables reste praticable) et la liste de ses sièges viennent
du générateur Python, qui écrit `assets/medievalships/carts/taverne_nomade.json`.

## S'asseoir

- **Clic droit sur un tabouret** (ou une place de banc) : le joueur s'assoit dessus, tourné comme le siège (vers la
  table ou le comptoir). On vise le siège lui-même, à **4 blocs au plus** ; un mur, une table ou un mob devant le
  cache. Rien ne se passe en sneakant (Maj enfoncé), en spectateur, ou si l'on est déjà assis / monté.
- **Se lever** : **Maj** (la touche vanilla pour descendre d'une monture). Le joueur se relève **devant le siège** ;
  si c'est occupé (une table, un autre tabouret, un mur), sur un côté, sinon derrière — jamais dans une boîte de
  collision ni dans un bloc.
- **Une personne par siège** : un siège pris est refusé avec un court message dans la barre d'action (« Cette place
  est prise. ») — un clic droit sur quelqu'un d'assis vise son siège à travers lui. Plusieurs joueurs peuvent
  s'asseoir en même temps sur des sièges différents.
- **Posture** : la posture assise vanilla ; les cuisses reposent sur le dessus du siège (ni flottant, ni enfoncé) ;
  le corps reste face au siège, la tête peut tourner jusqu'à 105° de chaque côté (comme dans un bateau).
- On est levé automatiquement si la taverne est cassée ou retirée (`/tent remove`), si elle est tournée, à la mort,
  à une téléportation, en passant en spectateur, en se déconnectant.

## Comment ça marche (pour les admins et développeurs)

- **Sièges dans le JSON** : `"seats": [{"pos": [x, y, z], "yaw": deg}, ...]` dans
  `assets/medievalships/<groupe>/<id>.json` ; `pos` = centre du dessus du siège en blocs locaux (y = 0 le sol, +z
  l'avant de l'objet, ancrage en 0,0,0), `yaw` = la direction regardée par la personne assise (convention Minecraft :
  0 = +z, 90 = -x, 180 = -z, 270 = +x). Un banc = une entrée par place. Les sièges tournent avec l'orientation de
  l'objet comme les boîtes de collision (`TentType.seats(quart)`, yaw + 90° par quart de tour). Lu par `TentType`
  (testé par JUnit `SeatsTest`).
- **Entité de siège** `medievalships:seat` (`SeatEntity`) : invisible, minuscule, sans IA ni gravité ni collision,
  impossible à frapper, à pousser, à brûler, à faire exploser ou à invoquer (`/summon` refusé). Elle est créée **à la
  demande** au moment où l'on s'assoit, exactement sur le dessus du siège, et **disparaît dès que plus personne n'est
  dessus**. Elle n'est **jamais sauvegardée** (ni avec le chunk, ni dans le fichier du joueur) : aucun reste après un
  redémarrage, même après un plantage. Un joueur qui se déconnecte assis est d'abord relevé à côté du siège.
- **Choix du siège** côté client (`SeatPicker`) : à chaque image, le rayon de visée est testé contre une petite boîte
  autour de chaque siège des objets proches (rien n'est calculé s'il n'y a aucun objet chargé) ; un clic droit envoie
  `SitPayload` (bloc d'ancrage + numéro du siège) au serveur, qui **revérifie tout** : l'objet est toujours là, le
  siège existe, le joueur est vivant, pas spectateur, pas déjà monté, à 4,5 blocs au plus (4 + la taille de la boîte),
  le siège est libre (`Seats.sit`).
- **Hauteur** : le point d'attache du passager est le dessus du siège ; Minecraft place les pieds d'un joueur monté
  0,6 bloc sous ce point, et la posture assise met le dessous des cuisses 0,59 au-dessus des pieds : les cuisses
  touchent le siège (même règle que les bancs des navires).
- **Coût serveur** : rien tant que personne n'est assis ; un siège occupé lit un état de bloc par tick.
- **Multijoueur / serveur dédié** : tout est décidé par le serveur ; un client sans le mod ne peut pas envoyer la
  demande (le client ne l'envoie que si le serveur la connaît).

## Tests faits

- **JUnit** (`SeatsTest`) : lecture des sièges (champ absent, entrées invalides ignorées, yaw par défaut et ramené dans
  [0, 360)), rotation avec l'orientation (comme les boîtes de collision, yaw + 90° par quart), la taverne enregistrée
  comme charrette avec ses noms, ses fichiers et au moins deux sièges dans son emprise, la hauteur assise (cuisses sur
  le siège), le rayon de visée contre la boîte d'un siège, l'ordre des places où l'on se relève. `CartTest`,
  `WorkshopTest`, `TrainingTest` mis à jour (neuf charrettes, indices de la liste des objets).
- **En jeu** (`SeatGameTest`, appelé par `ShipClientGameTest`, en solo et sur serveur dédié) : la taverne posée par
  `/tent place`, le joueur en survie assis sur le siège 0 par le traitement serveur de la demande (monté sur une
  entité de siège, pieds 0,6 sous le dessus du siège, corps et regard tournés comme le siège, entité jamais
  sauvegardée), capture d'écran du joueur assis ; un porte-armure refusé sur le même siège (et aussi par la monture
  vanilla), accepté sur un autre siège pendant que le joueur reste assis (deux à la fois) ; se lever avec la touche Maj :
  plus d'entité de siège, le joueur hors de tout bloc et de toute boîte de collision, à côté du siège ; le vrai chemin
  client pour le siège 1 (viser, `SeatPicker` le choisit, la touche utiliser envoie la demande, le joueur est assis) ;
  la taverne retirée pendant qu'il est assis : il est relevé, aucune entité de siège ne reste.
- `CartGameTest` pose aussi la taverne avec les autres charrettes (bloc, orientation, collisions, capture).

## Non vérifié / limites

- La déconnexion d'un joueur assis et le redémarrage du serveur pendant qu'il est assis ne sont pas rejoués par le
  test en jeu : le code relève le joueur à la déconnexion (événement Fabric, avant la sauvegarde du joueur) et
  l'entité de siège refuse d'être écrite (vérifié en jeu : `saveData` rend faux). Après un **plantage** du serveur
  (pas un arrêt normal) pendant qu'un joueur est assis, il revient debout à l'emplacement du siège, sans entité de
  siège.
- Seuls les joueurs s'assoient par clic droit ; d'autres entités peuvent être assises par le code (`Seats.sit`),
  mais leur hauteur est réglée pour un joueur.
- La branche Java de cette version porte un **JSON provisoire** de la taverne (géométrie de la roulotte de marchand
  et trois sièges) : le vrai modèle, ses meubles, ses collisions et ses sièges sur les tabourets arrivent avec le
  générateur de la taverne.
