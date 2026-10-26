# Le Grand Dirigeable de Cristal (`crystal_airship`) — plan, animations et guide du joueur

Planche de référence : `scratchpad/ref/crystal_airship_ref.png` (grande perspective, vues de côté, de dessus,
avant, arrière, quatre vues intérieures : poste de pilotage, salon, salle des machines, réserve).

## 1. Mesures sur la planche

Vue de côté (448 × 332 px dans la planche, la proue à gauche). Échelle retenue : **0,13 bloc par pixel**
(z = (222 − x) × 0,13 vers la proue, y = (205 − y) × 0,13 vers le haut, le pont principal à y = 0). La vue
avant est à 0,78 fois l'échelle de la vue de côté (hauteurs drapeau → cristal du bas comparées), la vue de
dessus à la même échelle que la vue de côté. La planche n'est pas cohérente d'une vue à l'autre (lobes du
ballon, nacelles) : la disposition retenue, symétrique, reproduit la silhouette des trois vues à la fois.

| Élément | Pixels (côté) | Blocs |
|---|---|---|
| Longueur totale (beaupré → poupe) | x 8 → 400 | **51** (56 avec l'espar d'enseigne et la nacelle de cristal arrière) |
| Coque (étrave → poupe) | x 25 → 398 | **48,6** ; maître-bau 12 (vue avant 76 px) ; poupe **arrondie** en plan sur les 4 derniers blocs |
| Pont principal / quille | y 205 / 278 | 0 / quille « banane » : −7,4 à z 15, −9,4 au milieu, −8,2 à z −10, −6,2 à la poupe ; avant à pied coupé remontant à +3,4 |
| Tonture | rambarde y 197 → 183 → 178 | +1 au milieu, monte en continu vers le gaillard (+2,4 à z 13) et l'étrave (+3,3), tête d'étrave sculptée à +4,6 |
| Galerie du salon (bandeau brun) | y 205 → 236, fenêtres y 213 → 230, x 150 → 265 | six hautes fenêtres éclairées −3 → −1, z −5,5 → 8,5, pilastres, corniche, appui |
| Bas de coque vert | y 236 → 281 | bande verte de −4 à la quille relevée vers l'avant (suit le pied d'étrave), virures brunes le long de la quille |
| Gaillard d'avant (pont, garde-corps) | rambarde y 183, x 25 → 120 | pont à +2,0, z 13,3 → 25,6 ; panneau vert à volute dorée ; beaupré carré relevé de 12°, bagues de laiton |
| Vitrail en éventail de l'avant | x 75 → 110, y 208 → 245 | quart de disque, moyeu en haut à l'arrière (z 13,8, y −0,3), rayon 4,6 ; deux fenêtres éclairées derrière |
| Tourelle (vigie) du pont | x 120 → 145, sommet y 175 | z 10 → 13,3, haut +4,0, chapeau mouluré, lanterne sur poteau |
| Château arrière, en gradins | façades x 300 / 310 / 320, toits y 186 / 167 / 153 | étage 1 (0 → +3) en retrait de 0,3 sur la coque, arrondi à la poupe ; étage 2 (+3 → +6,4) en retrait de 1,1, en encorbellement jusqu'à z −23,9 ; pont de toit et hiloire verte jusqu'à +7,3, cimier +8,4 |
| Moteurs latéraux | x 290 → 400, y 200 → 262, œil de cristal en (366, 225), r 13 | z −9,6 → −24,4, centre y −2,3, rayon 3,1, à ±8,3 ; œil r 1,7 (lunette à dents r 2,6) |
| Médaillon de poupe (vue arrière) | disque Ø 37 px vue arrière | rayon 3, centre y −3,5, à fleur de la poupe arrondie |
| Hélices sous la poupe (pales dorées) | x 255 → 340, y 255 → 310 ; vue avant à ±45 px | deux nacelles inclinées à x ±7,5, y −7 → −10 |
| Grand anneau doré | centre (222, 157), r 31 | centre y +5,4, rayon 4,1, dans le plan de symétrie ; son sommet entre de 1,8 bloc dans le ventre du ballon |
| Lobe central | x 103 → 345, y 50 → 158 | 31,6 de long, 15,2 de large, 13,8 de haut, axe à +14,6, bas à +7,7 |
| Lobe avant / lobe arrière (sur l'axe, plus hauts) | x 60 → 155, y 48 → 100 / x 250 → 378, y 40 → 105 | 13,2 × 8 × 7,4 / 17,2 × 9,6 × 9 |
| Quatre lobes latéraux (bosses aux coins, vue de dessus ; lobes de côté, vue avant) | vue de dessus x 127 → 167 et 273 → 333 | 12 à 13 de long, 9 de diamètre, à ±6,4 de l'axe |
| Mât et flamme rouge | x 221, y 15 → 50 | sommet +29,5 |
| Plateforme à cristaux sous la quille | (220, 300), cristal jusqu'à y 325 | plateforme −12, pointe −14,6 |
| Nacelles flottantes à cristal | avant (35, 150), arrière (410, 121) | (0, 7,2, 24,4) et (0, 10,9, −24,4) ; anneau en travers du navire, cristaux vers l'avant et l'arrière |

Proportions : 56 blocs de long, 25 de large (moteurs et leurs ailes compris, 22 au ballon), 41 de haut. Ballon en grappe :
un grand lobe central (œuf, sections elliptiques), un lobe avant et un lobe arrière sur l'axe, plus hauts, et
quatre lobes latéraux aux coins, plus bas ; sangles dorées autour de chaque lobe, ceinture dorée et festons
de chaînes à joyaux bleus, câbles vers la coque.

## 2. Structure, matériaux, pièces mobiles

* **Ballon** : toile crème et ivoire « bosselée » (petits cubes en relief, l'aspect voxel de la planche), qui
  gonfle entre les sangles ; sangles posées du côté caché depuis les bouts (pas de cibles ni de disques vus de
  face ou de dos), ceinture et festons de chaîne dorés, gros joyaux bleus sertis de laiton aux croisements,
  guirlande de petites lumières chaudes sous les festons, mât et flamme rouge au sommet. Il « respire »
  (léger gonflement et balancement).
* **Coque** : quille en banane, tonture qui monte vers une haute étrave sculptée (volute dorée), poupe arrondie ;
  bois brun chaud en haut (galerie de six hautes fenêtres éclairées entre pilastres, corniche et appui), bande
  vert olive qui suit les courbes, filets dorés, virures brunes le long de la quille ; vitrail en éventail de
  chaque côté de l'avant ; panneaux verts du gaillard à volute dorée ; beaupré relevé à bagues de laiton.
* **Château arrière** en gradins : étage 1 en retrait, arrondi à la poupe, galerie de hautes fenêtres éclairées
  tout autour et balcon à balustres dorés sur le pavois de poupe ; étage 2 plus étroit, en encorbellement sur
  consoles sculptées, panneaux verts à cadres dorés à l'arrière, fenêtres vitrées sur les côtés, grande baie
  cintrée et porte vers la terrasse à l'avant ; pont de toit à balustrade, hiloire verte à volutes dorées,
  cimier à joyau, hublots de laiton à joyau bleu, deux mâtereaux à flammes, espar d'enseigne en porte-à-faux.
* **Moteurs** : deux machines de laiton ornées contre les flancs (casque de laiton à pointe et deux ailes de
  plumes, grille à lames, tambour à plaques rivetées autour d'un grand œil de cristal bleu dans une lunette à
  dents, corolle de pétales vert-bronze, deux cheminées, réservoirs de cuivre, tôles de carénage vers la
  coque, capot de fer nervuré et petite hélice en pointe, cristaux bleus sertis) ; un **médaillon de laiton**
  à fleur de poupe (couronne dentée, anneau sombre, anneau riveté, engrenage tournant derrière un hublot
  bleu) ; deux nacelles inclinées sous la poupe à hélice de longues pales dorées en griffe.
* **Cristaux** : cristaux bleus lumineux (texture « glow ») : plateforme sous la quille, deux lanternes de
  cristal suspendues sous l'avant, lampes de cristal du château, nacelles flottantes avant et arrière (anneau
  en rotation lente), joyaux du ballon. Quelques particules magiques bleues près des cristaux.
* **Pièces mobiles** (os animés) : hélices (vitesse), rotors des nacelles, anneaux des nacelles flottantes et
  bob des cristaux, roue de la barre (barre), flammes rouges (vent), lanternes, portes ; tout le vaisseau
  flotte (dessin seulement).

## 3. Niveaux et pièces (y = 0 au pont principal, +z = proue)

| Niveau | Pièces |
|---|---|
| Toit du château (+6,4 → +8,4) | pont de toit à balustrade, hiloire verte, cimier, mâtereaux à flammes (décor) |
| Château, étage 2 (+3) | **poste de pilotage** (murs de pierre et poutres) : grande baie cintrée vitrée face à la proue, grande roue de barre (le pilote debout derrière), colonnes d'instruments en laiton, lampes, lampe de cristal ; table des cartes et bibliothèques à l'arrière, sous l'encorbellement ; **porte vers la terrasse** (sur le toit de l'étage 1) à tribord de la baie |
| Château, étage 1 (0) | **carré des officiers** (table, chaises) ; escalier vers le poste de pilotage (bâbord) et vers la salle des machines (tribord) ; porte double sur le pont |
| Pont principal (0) et gaillard (+2) | pont ouvert, anneau doré sur son pilier, tourelle, lampes de cristal, bancs ; escaliers extérieurs vers le gaillard |
| Pont du salon (−4) | **salon** luxueux (canapés rouges, tapis, table basse, bibliothèques et vitrines, carte murale, lanternes, grandes fenêtres) ; **réserve** à l'avant (caisses, tonneaux, sacs, étagères, chaînes et lanternes) |
| Salle des machines (−8 → −0,5, deux niveaux) | palier au niveau du salon, passerelle tribord, escalier vers le fond, **grande machine à cœur de cristal bleu**, tuyaux, engrenages, grilles au sol |
| Cale (−8) | sous le salon, échelle et trappe : stockage |

Portes (grille) : 0 château (porte double sur le pont), 1 salon ↔ salle des machines, 2 salon ↔ réserve,
3 trappe de la cale, 4 poste de pilotage ↔ terrasse. Escaliers de 0,5 bloc (château ↔ poste de pilotage, château ↔ salle des machines, palier
↔ fond de la salle des machines, pont ↔ gaillard) ; échelle de la cale. Fenêtres : cellules « vitre » de la
grille (on voit dehors) : baie du poste de pilotage, fenêtres du salon.

## 4. Contraintes techniques

* Tout ce qui se marche est dans la grille intérieure (cellules de 0,5 bloc) : coque, ponts, murs, planchers,
  plafonds (dessinés sur les limites des cellules, ce qui est dessiné est ce qui arrête), ballon et nacelles
  pleins ; aucune pièce ne s'ouvre sur le vide (`CrystalTest.noWayOut`).
* Le mod ne dépend pas de Valkyrien Skies : le système maison de grille intérieure porte les joueurs, les
  fait marcher dans les pièces, monter les escaliers et s'asseoir pendant le vol (même chose que le Léviathan).
* Vol : physique `Flight` (comme le Léviathan), réglages encore plus lourds et lents ; sondes de terrain sur
  tout le volume (lobes, anneau, nacelles, moteurs, cristaux, mâts) pour le pilote automatique aérien.
* Modèle Blockbench généré (`tools/generate_crystal.py`), deux textures (extérieur, pièces), meubles des mods
  de décoration embarqués (identifiants seulement, boîtes de remplacement si un mod manque).

## 5. Ce qui a été construit

Comparaison planche / modèle : [comparaison_crystal_airship.png](comparaison_crystal_airship.png) (côté,
dessus, avant, arrière, perspective) et [comparaison_crystal_airship_pieces.png](comparaison_crystal_airship_pieces.png)
(vues de la planche à gauche, rendu des pièces meublées à droite).

| Fichier | Rôle |
|---|---|
| `tools/crystal_shape.py` | formes (lobes du ballon, coque, château, nacelles, cristaux), source unique des mesures |
| `tools/crystal_interior.py` | grille intérieure (cellules de 0,5 bloc) : pièces, portes, escaliers, échelle, vitres |
| `tools/crystal_decor.py` | ameublement : blocs des mods de décoration, meubles faits sur mesure, sièges, tableaux |
| `tools/crystal_furniture.py` | meubles sur mesure (colonnes d'instruments, lampes de cristal, horloge murale, carte du monde, chaînes, porte-voix) |
| `tools/crystal_texture.py` | les deux textures (extérieur 512², pièces) et l'icône |
| `tools/generate_crystal.py` | modèle Blockbench (≈ 17 000 cubes, 12 animations) ; réutilise les outils du Léviathan et du Corsaire |
| `core/CrystalLayout.java` | type, géométrie, sondes, sièges, barre, réglages de vol (miroir de `crystal_shape.py`) |
| `entity/CrystalAirshipEntity.java`, `client/CrystalEffects.java` | entité, particules (étincelles bleues des cristaux et du médaillon, vapeur des moteurs) |
| `CrystalTest` (JUnit), `CrystalGameTest` (en jeu) | tests |

Ameublement (148 blocs de mods, 40 places assises) : `farmhouse_decorations` (75 : canapés, fauteuils,
tables, piano, gramophone, bibliothèques, vitrines, lampes, établi), `furnish` (55 : caisses, étagères,
tabourets, casiers, tableaux), `farmersdelight` (10 : caisses de légumes, sacs, paniers), `landsoficaria`
(2 tonneaux), `mebahelcreaturesdwarven` (6 : tuyaux et blocs de métal nain de la salle des machines).
Faits sur mesure (aucun mod n'a la pièce) : roue de barre, colonnes d'instruments, lampes de cristal,
machine à cœur de cristal (engrenages et pistons animés), horloge et manomètres muraux, carte du monde,
chaînes de la réserve, tonneaux et sacs, lanternes. Sans les mods, des boîtes de remplacement texturées
prennent leur place (même encombrement).

## 6. Animations et effets

| Animation | Pièces | Pilotée par |
|---|---|---|
| `propeller` | petites hélices en pointe des deux moteurs, hélices des deux nacelles inclinées sous la poupe | la vitesse (immobiles à l'arrêt) |
| `engine` | engrenages et pistons de la machine à cœur de cristal, engrenage du médaillon de poupe (lent) | la vitesse |
| `steer` | roue de la barre | la barre |
| `elevator` | ailerons en plume des moteurs (± 14°) | montée / descente |
| `flag_wave`, `streamer_wave` | flamme du mât, flammes du château et de la queue du ballon ; bob des nacelles flottantes, rotation lente de leurs anneaux ; respiration du ballon (gonflement de 1 %, balancement de 0,05 bloc) | le temps |
| `lantern_sway` | lanternes suspendues, lanternes de cristal sous l'avant | le temps |
| portes 0 à 4 | battants, trappe | clic droit |

Particules (côté client, à moins de 80 blocs) : étincelles et lueurs bleues autour des cristaux (plateforme,
nacelles flottantes, yeux de cristal des moteurs, hublot du médaillon), nuages derrière les moteurs quand ils tournent.

## 7. Guide du joueur

### Obtenir et poser

* Objet *Le Grand Dirigeable de Cristal* (inventaire créatif, onglet *Navires médiévaux*) ou
  `/ship give crystal_airship [joueurs]` ; `/ship spawn crystal_airship` le pose au-dessus de vous.
* **Clic droit sur le sol, l'eau ou un toit** : il apparaît en vol stationnaire au-dessus, seulement si toute
  sa place est libre (environ 56 blocs de long, 25 de large, 41 de haut : ballon, anneau, moteurs,
  cristaux, mât). Sinon un message l'indique et rien n'est posé.

### À bord

* **Clic droit sur la coque** : on est déposé sur le pont principal. On marche partout, pendant le vol :
  pont, gaillard d'avant (escaliers de chaque côté de la tourelle), château, **poste de pilotage** (escalier
  bâbord du carré), **salon** et **réserve** (escalier tribord du carré, puis le palier de la salle des
  machines), **fond de la salle des machines** (escalier du palier), **cale** (trappe et échelle du salon),
  **terrasse** sur le toit du carré (porte du poste de pilotage, à tribord de la baie).
* **Portes** (clic droit) : 0 porte double du château sur le pont, 1 salon ↔ salle des machines, 2 salon ↔
  réserve, 3 trappe de la cale, 4 poste de pilotage ↔ terrasse. Les vitres (baie du poste de pilotage, grandes fenêtres du salon) laissent
  voir dehors.
* **Sièges** : canapés, fauteuils, chaises, tabourets, bancs du pont (40 places) ; Maj pour se lever.

### Piloter

**Prendre la barre** : clic droit sur la grande roue du poste de pilotage (le pilote se tient derrière).
Z avancer, S ralentir puis reculer, Q / D virer, **Espace monter**, **Ctrl descendre**, Maj quitter la barre
(on se retrouve debout dans le poste de pilotage). Relâchées, Espace et Ctrl laissent le dirigeable garder son
altitude. C'est le vaisseau volant le plus lourd du mod, plus lent que le Léviathan : il prend son erre
lentement, la roue vient progressivement, la proue pivote doucement (quelques degrés par seconde),
il monte et descend sans à-coups.

Pilote automatique : itinéraires aériens comme le dirigeable steampunk et le Léviathan (`/ship route create
<nom> loop air`, `addstop`, `addpoint`, `assign` ; voir [COMMANDES.md](COMMANDES.md)). Les sondes de terrain
couvrent tout le volume (lobes, anneau, nacelles, moteurs, cristaux) : il garde au moins 9 blocs sous la
quille au-dessus du relief et descend à l'escale dans les 52 derniers blocs.

### Réglages (`config/medievalships.json`, bloc `ships.crystal_airship`, `/ship reload`)

| Clé | Défaut | Rôle |
|---|---|---|
| `slowSpeed` / `normalSpeed` / `fastSpeed` / `reverseSpeed` | 1.8 / 3.8 / 6.0 / 1.0 | allures (blocs/s) |
| `acceleration`, `braking`, `waterDrag` | 0.22, 0.45, 0.12 | forte inertie |
| `maxTurnRate`, `minTurnFactor` | 5.0, 0.45 | rotation (°/s), part disponible à l'arrêt |
| `helmRate`, `helmReturnRate`, `turnResponse`, `turnSpeedLoss` | 0.6, 0.7, 0.4, 0.08 | barre lente, rotation lente |
| `waveRocking` | 0.4 | balancement visuel |
| `flight.climbSpeed` / `flight.descendSpeed` / `flight.verticalAcceleration` | 1.0 / 0.85 / 0.35 | montée et descente |
| `flight.aiClearance`, `flight.aiApproachDistance`, `flight.sway` | 9, 52, 0.5 | pilote automatique, balancement en vol |

## 8. Limites

* La planche n'est pas cohérente d'une vue à l'autre : la grappe du ballon a été rendue symétrique ; le pont
  principal reste plat au milieu (pour y marcher), la tonture monte vers le gaillard et l'étrave.
* Sur la planche, le haut de l'anneau passe devant le ventre du ballon ; en 3D l'anneau est dans le plan de
  symétrie, son sommet entre donc dans le ventre (1,8 bloc caché) : compromis entre la hauteur du ballon et un
  anneau entier.
* Vus de l'arrière, les moteurs restent des masses rondes (tambour, corolle, capot) : sans roue ni hélice
  visibles, avec leurs cristaux bleus, mais pas aussi « bosselés » que sur la planche.
* Les vitres sont des cellules pleines transparentes : on ne passe pas par les fenêtres.
* Les tonneaux, sacs et caisses de la réserve et de la cale sont du décor (pas d'inventaire).
