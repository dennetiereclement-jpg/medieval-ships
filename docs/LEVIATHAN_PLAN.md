# Le Léviathan des Cieux (`sky_leviathan`) — analyse et plan (phase 1)

Planche de référence : `scratchpad/ref/leviathan_ref.png` (vues de côté, avant, arrière, dessus,
perspective, détails, six vues intérieures). Comparaisons rendu / référence : voir le rapport.

## 1. Mesures sur la planche (vue de côté, 1536 × 1024)

Échelle retenue : **0,07 bloc par pixel** de la vue de côté (65 blocs de la pointe avant à la pointe
arrière, comme le cahier des charges).

| Élément | Pixels (vue de côté) | Blocs |
|---|---|---|
| Ballon (nez → fin de l'enveloppe) | x 100 → 838 | **52** |
| Ballon, hauteur | y 145 → 425 | **19,6** |
| Ballon, largeur (vue avant, rapport L/H ≈ 1,3) | — | **24,4** (sections elliptiques, un peu aplaties) |
| Cerclages en bois | x 160, 255, 705, 785 | z = 21, 14,35, −17,15, −22,75 |
| Grands panneaux de bois des flancs | entre les deux cerclages du milieu, y 190 → 395 | azimut 45° → 142° |
| Nez : ferrure à engrenage + pointe | x 0 → 100 | jusqu'à z = 32,2 |
| Queue : moyeu + pointe | x 838 → 935 | jusqu'à z = −33,2 |
| Navire suspendu (coque) | x 165 → 745 | **35,8** (41 avec l'éperon, 45 avec le beaupré), 10 de large |
| Pont principal / quille | y 540 / 630 | 0 / −6,3 |
| Gaillard d'avant, dunette, château arrière | y 497 / 490 / 455 | +3,0 / +3,0 / +5,5 |
| Espace ballon → pont | y 425 → 540 | 8 blocs |
| Mât du pavillon (sommet) | y 18 | +36,8 |
| Aileron ventral (pointe) | (465, 705) | y −11,55 |

Proportions : longueur totale 65 (67 avec les ailerons latéraux), hauteur totale 48 (pavillon
compris). Le ballon est un **œuf** : sections `(1 − t^a)^b` (avant a = 2,6, b = 0,55 ; arrière
a = 2,4, b = 0,6), plus effilé vers l'arrière, le plus large au milieu.

Ailerons noirs « aile de chauve-souris » (bord d'attaque bombé, bord de fuite festonné entre les
nervures, trois trous près de la pointe, pique en emblème) : un dorsal sur le ballon, deux hauts
(±30°), deux latéraux (±115°), un bas, au moyeu de queue ; un ventral sous la quille. Le dorsal et
le bas servent de gouvernail (`steer`), les latéraux de profondeur (`elevator`). La planche n'est pas
cohérente d'une vue à l'autre (vue arrière : ailerons d'un seul côté) : disposition symétrique
retenue, qui reproduit la silhouette des vues de côté et de dessus.

## 2. Niveaux et pièces (coordonnées du navire : y = 0 au pont principal, +z = proue)

| Niveau | Pièces |
|---|---|
| Pont d'observation (y 28, sur le ballon) | plancher arrondi de 24 × 11, garde-corps, mât et pavillon pirate, roue décorative, cabestan, trappe |
| Dunette (y 5,5) | garde-corps, lanternes de poupe |
| Château arrière (y 3) | **barre** (pilote debout derrière la roue, z −11,6), escaliers ; sous la dunette : **salle des cartes** (y 3 → 5) |
| Pont principal (y 0) | pont ouvert entre les châteaux, **tour centrale** (échelle intérieure jusqu'au pont d'observation, grand engrenage), descente vers la salle commune, bancs ; sous le château arrière : **cabine du capitaine** (bureau + chambre, porte double) ; sous le gaillard : **magasin du maître d'équipage** |
| Pont inférieur (y −3) | **salle commune** (grande table, bancs), **coursive** (tapis rouge) avec **poste d'équipage** et **cambuse** de chaque côté, porte vers la salle des machines |
| Cale (y −5,5) | **cale / stockage** sur toute la longueur, échelle et trappe vers la coursive |
| Salle des machines (y −5 → −0,5, sur deux niveaux) | palier au niveau du pont inférieur, escalier, **chaudière** avec cheminée, manomètres, volant, pistons et engrenage animés |

Portes (grille) : 0 tour, 1 trappe du pont d'observation, 2 cabine du capitaine, 3 chambre,
4 salle des cartes, 5 magasin avant, 6 salle commune, 7 poste d'équipage, 8 cambuse,
9 salle des machines, 11 trappe de la cale. Escaliers de 0,5 bloc ; échelles : tour (28 blocs) et cale.

Tout est dans la grille intérieure (cellules de 0,5 bloc, `tools/leviathan_interior.py`) : le ballon
y est plein, les ponts ouverts sont « dehors » mais portés (on y marche pendant le vol), les murs,
planchers et plafonds des pièces sont dessinés sur les limites des cellules.

## 3. Vol et pilote automatique

Physique `Flight` du dirigeable steampunk, réglages d'un très grand vaisseau lourd : 2 / 4,2 /
6,8 blocs/s, accélération 0,3, virage max 6,5°/s, montée 1,2 et descente 1,0 bloc/s avec une
accélération verticale de 0,45 (changements d'altitude progressifs), marge de 8 blocs au-dessus
du relief pour le pilote automatique (itinéraires `air`), approche des escales à 48 blocs.

## 4. Reste à faire (phase 2)

Décoration complète des pièces avec les meubles des mods, sons et vapeur de la salle des machines,
cordages animés, vérification en jeu de la persistance après redémarrage.
