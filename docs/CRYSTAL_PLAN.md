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
| Longueur totale (beaupré → poupe) | x 8 → 400 | **51** (55 avec l'espar arrière et la nacelle de cristal arrière) |
| Coque (étrave → poupe) | x 25 → 398 | **48,6** ; maître-bau 12 (vue avant 76 px) |
| Pont principal / quille la plus basse | y 205 / 281 | 0 / −9,8 (quille relevée aux deux bouts, étrave en guibre) |
| Bandeau brun des grandes fenêtres (salon) | y 205 → 236, fenêtres y 210 → 230, x 150 → 265 | −4,0 → 0 ; fenêtres −3,3 → −0,7, z 9,4 → −5,6 |
| Bas de coque vert | y 236 → 281 | −4,0 → −9,8 |
| Gaillard d'avant (pont, garde-corps) | rambarde y 183, x 25 → 120 | pont à +2,0, z 13,3 → 25,6 |
| Tourelle crénelée du pont | x 120 → 145, sommet y 172 | z 10 → 13,3, haut +4,3 |
| Château arrière, 3 niveaux | façades x 300 / 330 / 345, toits y 182 / 165 / 148 | étages à 0 / +3 / toit vert jusqu'à +8,6 ; z −10,1 / −14 / −15,5 → −23 |
| Nacelles latérales (moteurs) | x 290 → 400, y 200 → 262, œil de cristal en (366, 222), r 15 | z −9 → −23, centre y −2,3, rayon 3,4 ; à ±8,3 du milieu (vue avant) |
| Moteur arrière (vue arrière) | disque Ø 60 px vue arrière | rayon 4, centre y −4,4, sur le tableau arrière |
| Hélices sous la poupe (pales dorées) | x 255 → 340, y 255 → 310 ; vue avant à ±45 px | deux nacelles inclinées à x ±7,5, y −7 → −10 |
| Grand anneau doré | centre (222, 150), r 37 | centre y +6,6, rayon 4,3, dans le plan de symétrie, sur un pilier |
| Lobe central | x 103 → 345, y 50 → 160 | 31,6 de long, 15,2 de large, 14 de haut, bas à +10,9 (au-dessus de l'anneau) |
| Lobe avant / lobe arrière (sur l'axe, plus hauts) | x 60 → 155, y 48 → 100 / x 250 → 378, y 40 → 105 | 13,2 × 8 × 7,4 / 17,2 × 9,6 × 9 |
| Quatre lobes latéraux (bosses aux coins, vue de dessus ; lobes de côté, vue avant) | vue de dessus x 127 → 167 et 273 → 333 | 12 à 13 de long, 9 de diamètre, à ±6,4 de l'axe |
| Mât et flamme rouge | x 221, y 15 → 50 | sommet +29,5 |
| Plateforme à cristaux sous la quille | (220, 300), cristal jusqu'à y 325 | plateforme −12, pointe −14,6 |
| Nacelles flottantes à cristal | avant (35, 148), arrière (410, 118) | (0, 7,4, 24,3) et (0, 11,3, −24,4) |

Proportions : 55 blocs de long, 23 de large (nacelles comprises, 22 au ballon), 44 de haut. Ballon en grappe :
un grand lobe central (œuf, sections elliptiques), un lobe avant et un lobe arrière sur l'axe, plus hauts, et
quatre lobes latéraux aux coins, plus bas ; sangles dorées autour de chaque lobe, ceinture dorée et festons
de chaînes à joyaux bleus, câbles vers la coque.

## 2. Structure, matériaux, pièces mobiles

* **Ballon** : toile crème « matelassée » (petits carrés crème, blancs et gris, l'aspect voxel de la planche),
  sangles et ceinture en laiton doré, joyaux bleus lumineux aux croisements, mât et flamme rouge au sommet.
* **Coque** : bois brun chaud en haut (bandeau des grandes fenêtres éclairées du salon), bordé vert foncé en
  bas, listons et moulures dorés, volutes dorées sur l'avant, rosace en éventail éclairée de chaque côté de
  l'avant, guibre et beaupré, gaillard d'avant à balustres, tourelle crénelée.
* **Château arrière** : trois niveaux (fenêtres éclairées cintrées), toit vert à corniche dorée, volute de
  laiton, deux mâtereaux à flammes rouges, espar arrière à flamme.
* **Moteurs** : deux nacelles latérales de bronze (capot en dôme, œil de cristal bleu lumineux à rayons,
  ailettes en plumes de laiton, tuyaux de cuivre, rotor arrière), un grand moteur arrière rond (hélice dans un
  anneau, cœur de cristal), deux nacelles inclinées sous la poupe à hélice de pales dorées.
* **Cristaux** : cristaux bleus lumineux (texture « glow ») : plateforme sous la quille, deux lanternes de
  cristal suspendues sous l'avant, lampes de cristal du château, nacelles flottantes avant et arrière (anneau
  en rotation lente), joyaux du ballon. Quelques particules magiques bleues près des cristaux.
* **Pièces mobiles** (os animés) : hélices (vitesse), rotors des nacelles, anneaux des nacelles flottantes et
  bob des cristaux, roue de la barre (barre), flammes rouges (vent), lanternes, portes ; tout le vaisseau
  flotte (dessin seulement).

## 3. Niveaux et pièces (y = 0 au pont principal, +z = proue)

| Niveau | Pièces |
|---|---|
| Toit du château (+6,5 → +8,6) | toit vert (plein), volute, mâtereaux à flammes |
| Château, étage 2 (+3) | **poste de pilotage** : grande baie cintrée vitrée face à la proue, grande roue de barre (le pilote debout derrière), colonnes d'instruments en laiton, lampes, lampe de cristal ; table des cartes à l'arrière |
| Château, étage 1 (0) | **carré des officiers** (table, chaises) ; escalier vers le poste de pilotage (bâbord) et vers la salle des machines (tribord) ; porte double sur le pont |
| Pont principal (0) et gaillard (+2) | pont ouvert, anneau doré sur son pilier, tourelle, lampes de cristal, bancs ; escaliers extérieurs vers le gaillard |
| Pont du salon (−4) | **salon** luxueux (canapés rouges, tapis, table basse, bibliothèques et vitrines, carte murale, lanternes, grandes fenêtres) ; **réserve** à l'avant (caisses, tonneaux, sacs, étagères, chaînes et lanternes) |
| Salle des machines (−8 → −0,5, deux niveaux) | palier au niveau du salon, passerelle tribord, escalier vers le fond, **grande machine à cœur de cristal bleu**, tuyaux, engrenages, grilles au sol |
| Cale (−8) | sous le salon, échelle et trappe : stockage |

Portes (grille) : 0 château (porte double sur le pont), 1 salon ↔ salle des machines, 2 salon ↔ réserve,
3 trappe de la cale. Escaliers de 0,5 bloc (château ↔ poste de pilotage, château ↔ salle des machines, palier
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
| `tools/generate_crystal.py` | modèle Blockbench (≈ 13 000 cubes, 11 animations) ; réutilise les outils du Léviathan et du Corsaire |
| `core/CrystalLayout.java` | type, géométrie, sondes, sièges, barre, réglages de vol (miroir de `crystal_shape.py`) |
| `entity/CrystalAirshipEntity.java`, `client/CrystalEffects.java` | entité, particules (étincelles bleues des cristaux, fumée des moteurs) |
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
| `propeller` | rotors des deux nacelles, hélice du moteur arrière, hélices des deux nacelles inclinées sous la poupe | la vitesse (immobiles à l'arrêt) |
| `engine` | engrenages et pistons de la machine à cœur de cristal | la vitesse |
| `steer` | roue de la barre | la barre |
| `elevator` | volets des nacelles (± 14°) | montée / descente |
| `flag_wave`, `streamer_wave` | flamme du mât, flammes du château et de l'espar ; bob des nacelles flottantes, rotation lente de leurs anneaux | le temps |
| `lantern_sway` | lanternes suspendues, lanternes de cristal sous l'avant | le temps |
| portes 0 à 3 | battants, trappe | clic droit |

Particules (côté client, à moins de 80 blocs) : étincelles et lueurs bleues autour des cristaux (plateforme,
nacelles flottantes, yeux de cristal des moteurs), nuages et fumée blanche derrière les moteurs quand ils tournent.

## 7. Guide du joueur

### Obtenir et poser

* Objet *Le Grand Dirigeable de Cristal* (inventaire créatif, onglet *Navires médiévaux*) ou
  `/ship give crystal_airship [joueurs]` ; `/ship spawn crystal_airship` le pose au-dessus de vous.
* **Clic droit sur le sol, l'eau ou un toit** : il apparaît en vol stationnaire au-dessus, seulement si toute
  sa place est libre (environ 55 blocs de long, 23 de large, 44 de haut : ballon, anneau, nacelles,
  cristaux, mât). Sinon un message l'indique et rien n'est posé.

### À bord

* **Clic droit sur la coque** : on est déposé sur le pont principal. On marche partout, pendant le vol :
  pont, gaillard d'avant (escaliers de chaque côté de la tourelle), château, **poste de pilotage** (escalier
  bâbord du carré), **salon** et **réserve** (escalier tribord du carré, puis le palier de la salle des
  machines), **fond de la salle des machines** (escalier du palier), **cale** (trappe et échelle du salon).
* **Portes** (clic droit) : 0 porte double du château sur le pont, 1 salon ↔ salle des machines, 2 salon ↔
  réserve, 3 trappe de la cale. Les vitres (baie du poste de pilotage, grandes fenêtres du salon) laissent
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

* La planche n'est pas cohérente d'une vue à l'autre : la grappe du ballon a été rendue symétrique, la coque
  est un peu plus droite que sur la grande perspective (pont continu, pour pouvoir y marcher).
* Les vitres sont des cellules pleines transparentes : on ne passe pas par les fenêtres.
* Les tonneaux, sacs et caisses de la réserve et de la cale sont du décor (pas d'inventaire).
