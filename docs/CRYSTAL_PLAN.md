# Le Grand Dirigeable de Cristal (`crystal_airship`) — plan et guide

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
