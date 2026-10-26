# Le Navire Volant Rustique (`rustic_skiff`) — analyse, plan et guide du joueur

Planche de référence : `scratchpad/ref/rustic_skiff_ref.png` (grande perspective, vues de côté, de dessus,
avant, arrière et quatre vues intérieures : pont avant, façade de la cabine et poste de pilotage, chambre,
cale / couloir de stockage). Une vieille barque de bois faite main, transformée en engin volant : petite,
agile, rapiécée, médiévale-fantastique (jamais un avion moderne).

Comparaison planche / rendu du modèle (5 vues et 4 pièces) : [`preview_rustic_skiff.png`](preview_rustic_skiff.png).

Les sessions de jeu ne passent **pas** par Valkyrien Skies : comme le Nautilus, le Vieux Corsaire et le
Léviathan, le navire décrit ses pièces par une **grille intérieure** (cellules de 0,5 bloc) que le mod lit pour
les collisions, les portes, l'échelle et le volume où l'on est transporté. On marche, on s'assoit et on
change de niveau pendant le vol, en multijoueur, sans glisser à travers les murs.

## 1. Mesures sur la planche

Échelle retenue sur la vue de côté (458 × 275 px de la planche) : **0,1 bloc par pixel**, pont avant à
y = 148 px. Les vues ne sont pas tout à fait cohérentes entre elles (image générée) : le modèle suit d'abord la
vue de côté et la perspective, puis prend un compromis avec les vues de dessus, avant et arrière.

| Élément | Pixels (vue de côté) | Blocs (modèle) |
|---|---|---|
| Coque, tête d'étrave → tableau arrière | x 70 → 330 | **26,4** (z +13,4 → −13,0) |
| Poutre de proue (poutre carrée horizontale) | x 20 → 70 | jusqu'à z +17,2, à hauteur du plat-bord |
| Tubes de poupe | x 330 → 437 | 7,1 (paire basse) et 8,5 (paire haute, la plus longue) |
| Longueur totale | x 20 → 437 | **38,4** (poutre → bouches des tubes) |
| Fond de coque au milieu | y 178 | −3,0 mesuré, **−3,15** retenu (place pour la cale) |
| Bastingage du pont avant / tête de proue | y 135 / 122 | +1,0 / +2,8 (proue relevée en banane) |
| Cabine (façade → poupe), toit = poste de pilotage | x 228 → 330, y 116 | z −3 → −13, **+3,0** |
| Balustrade du poste de pilotage | y 92–100 | **1,5** au-dessus du poste (hauteur de poitrine) |
| Toile du toit : avant-toits / faîte | y 58–80 / 8–14 | coins tirés jusqu'en haut des perches **9,5** (pagode), pans creusés à 7,9 / **11,8**, mât central 12,6 |
| Étendue du toit (côté / dessus) | x 215 → 395 | compromis : z −0,4 → −17,6, 11,2 de large |
| Ailes avant : racine, coin haut, pointe | (207,178) (277,200) (267,238) | (z −0,6, y −1,8) (−7,4, −4,6) (−6,4, −9,0), x 2,6 → 3,9 → 3,4 |
| Ailes arrière : racine, coin haut, pointe | (320,160) (400,160) (343,268) | (−11,9, −1,2) (−18,6, −1,7) (−14,2, −11,0), x 2,45 → 3,8 → 3,4 |
| Quille étagée et pique (vues avant / arrière) | « toupie » sous la coque | 3 gradins (largeurs 2,9 / 2,0 / 1,2) sous l'arrière, pique jusqu'à y −9,5 |

Vue de dessus : **proue étroite** (≈ 4 blocs) puis un **épaulement** brusque vers z ≈ +5 et un corps large
(8 blocs) jusqu'à la poupe — le modèle mélange les deux plans entre z +3,5 et +6,5. Vue avant : le poste de
pilotage **déborde** de la coque (4,9 de demi-largeur, 5,7 avec les consoles sculptées, contre 4,0 pour la coque), le toit a
à peu près la largeur du poste ; la coque se resserre sous la préceinte (bouchain pincé, mais la cale garde son plancher)
puis continue en **toupie** : une quille à trois gradins et une longue **pique** ferrée ; les ailes, vues par la tranche,
pendent presque verticalement à ±3,4 blocs avec une lanterne. Vue arrière : **quatre tubes télescopiques** (2 × 2, la paire
haute la plus longue) autour d'un **poteau sculpté** en anneaux empilés, bouches en cloche sombres et creuses, le mur
arrière de la cabine et ses deux lanternes de part et d'autre. La vue de dessus montre les ailes très écartées : elle
contredit les vues avant et arrière, le modèle suit ces dernières.

Proportions : 26 × 8 blocs de coque, 38,4 de long hors tout, 11,4 de large au poste de pilotage (consoles comprises), 24 de haut (du fleuron
du mât central à la pointe des ailes arrière). Petit à côté du Léviathan (65 blocs) et du Vieux Corsaire
(53), plus grand que le dirigeable steampunk (22), mais **plus maniable** que lui.

## 2. Structure, matériaux, éléments mobiles

* **Coque** longue en banane, bordé de planches brunes irrégulières rapiécées (longueurs d'autres bois, plaques
  de fer clouées), lisses sombres, **planches de renfort verticales moussues**, **lisse de plat-bord moussue** (vert
  olive) avec des blocs de mousse alternant avec des blocs de bois, **anneaux de fer gris et bittes sur le plat-bord** et
  **chaînes en festons** le long des flancs depuis le bout de la poutre de proue, trois **lanternes au bout de chaînes**
  sous la coque de chaque bord, quille remontant en étrave jusqu'à la tête de proue, **poutre de proue carrée,
  horizontale**, cerclée de fer, coiffe de fer et petites ferrures pendantes, lanterne. Sous l'arrière, la **quille
  étagée** (trois gradins cerclés de fer) et sa longue **pique** ferrée.
* **Appentis de proue** en grandes planches grises délavées : faîtage **haut à la proue** sur un poteau équarri et un
  pignon de planches, descendant vers l'arrière où il est ouvert ; ses pans reposent sur les plats-bords : le **coin
  de stockage**.
* **Pont avant ouvert** (deux marches sous l'appentis), **caillebotis de fer** au-dessus de l'échelle de la cale.
* **Cabine** centrale-arrière : murs de planches verticales sur poteaux, gros poteaux d'angle, **deux fenêtres à
  croisillons éclairées** de chaque bord (salle commune et chambre ; vu de l'intérieur, le ciel par les carreaux, un
  rideau déchiré dans la chambre) et entre elles un **grand panneau carré encadré à l'emblème sculpté**, façade avec porte à deux battants et deux lanternes, **escalier de caisses** à tribord jusqu'au
  poste de pilotage.
* **Poste de pilotage** sur le toit de la cabine : plancher, poutres de rive en débord sur consoles et **consoles
  sculptées** dépassant de ses flancs,
  **balustrade rustique** à poteaux moussus, **roue** sur sa colonne, bancs, lanternes.
* **Grand toit de toile gris-brun usée** en **pagode** sur quatre **piliers** de bois coiffés (traverses entièrement sous
  la toile), quatre **perches écartées** dont la toile est tirée jusqu'en haut (coins relevés, pointes de fer au-dessus)
  et un mât central (chapeau ligaturé au faîte) : toile tachée et rapiécée, coutures, bords creusés entre les perches,
  **une rangée de langues de toile déchirées** de la couleur du toit, longueurs inégales (quelques longues aux coins).
* **Deux longues perches inclinées** à la poupe (mâts de charge) avec cordages jusqu'aux tubes et au toit.
* **Cordes de grands fanions déchirés** (beige, rouge, noir, brun ; queue fendue) de la poutre de proue aux perches
  avant du toit.
* **Quatre tubes télescopiques** de bronze bruni sur le tableau arrière : trois longueurs de plus en plus larges vers
  l'arrière, un **collier de fer** à chaque ressaut, **bouche en cloche** creuse et sombre (une lueur sourde au fond, un
  **ventilateur** noirci dedans), la paire haute la plus longue ; autour d'un **poteau sculpté** en anneaux empilés,
  sangles de fer et sellette, élingues des mâts de charge.
* **Quatre ailes de toile** souples en **chauve-souris** : longue nervure d'attaque et deux nervures écartées en segments
  de bois sombre et d'**os pâle**, colliers de fer et ligatures, **bord libre en arcs creusés** lisses entre les pointes,
  toile cousue (coutures piquées), trouée et rapiécée, pointes de fer, une **lanterne** pendue à chaque nervure d'attaque ;
  accrochées sous les flancs (charnières de fer), presque parallèles à la coque.

**Animations** (os du modèle, appliquées par le moteur de rendu existant) : `engine` (phase du moteur, qui
n'avance qu'en mouvement) — les ventilateurs tournent dans les tubes et **les quatre ailes battent
lentement** ; `steer` — la roue et les ailes arrière (gouvernes) ; `elevator` — les quatre ailes s'inclinent à
la montée / descente ; `streamer_wave` — fanions et lanières du toit au vent ; `lantern_sway` — lanternes
pendues ; `door_0..2` — portes et trappe. Le dessin flotte doucement en vol stationnaire (sans toucher aux
collisions), s'incline dans les virages (moteur de rendu commun). **Particules** : bouffées de fumée à la bouche
du tube central (plus fortes en marche) et bourdonnement des tubes (effets communs des aéronefs à hélice).

## 3. Niveaux et pièces (grille intérieure)

| Niveau | y du plancher | Pièces |
|---|---|---|
| Poste de pilotage | +3,0 | roue (pilote debout derrière, face à la proue), bancs, mât central, perches |
| Pont avant / cabine | 0 (0,5 et 1 sous l'appentis) | pont ouvert, coin de stockage ; **salle commune** (z −3,5 → −7,5) ; **chambre** (z −8 → −12,5) |
| Cale | −2,5 | **couloir de stockage** bas (2 blocs) de z +4,5 à −10,5 |

Accès : porte de cabine (0) à deux battants dans la façade ; porte de la chambre (1) dans la cloison, à tribord
de l'ouverture de l'escalier de la cale ; **trappe à caillebotis** (2) du pont avant au-dessus de l'**échelle** de la cale ;
**escalier** de la salle commune vers la cale (à bâbord, ouverture bordée de rambardes) ; **escalier de caisses** du pont
avant au poste de pilotage (passage dans la balustrade), bordé côté mer d'une **rambarde** sur le bastingage. Toutes les pièces sont reliées et fermées (aucune
cellule de pièce ne touche l'air extérieur ; `SkiffTest`).

Ameublement (mods de décoration de l'utilisateur d'abord, comme sur les vues intérieures) :

* **Pont avant** (vue 1) : caisses et tonneau contre la façade, rouleau de cordage, banc sur le bastingage ;
  sous l'appentis caisses, tonneau couché (Lands of Icaria), sacs (Farmer's Delight), coffre, lanterne.
* **Façade / poste** (vue 2) : porte, lanternes, escalier de caisses ; roue, balustrade, lanternes de coin.
* **Salle commune** : table et chaises (Furnish), bouteille, verre, assiette, lanterne suspendue (Farmhouse
  Decorations), buffet (Furnish) avec livres et lanterne, étagère à pots au-dessus de l'escalier, caisse,
  tonneau, chemin de table rouge.
* **Chambre** (vue 3) : lit (Farmhouse Decorations) sous la fenêtre avec une **courtepointe rouge** (le lit du mod n'a pas de
  variante rouge), coffre au pied du lit, grande bibliothèque, bureau avec livres ouverts, carte et lanterne, sa chaise,
  commode, petite caisse, tapis rouge à bordure dorée, deux lanternes murales et une suspendue.
* **Cale** (vue 4) : chemin rouge, établi et panneau d'outils, casiers et **portes de casier à barreaux de fer** (« les
  portes de droite »), caisses, tonneaux, sacs, **rangées d'étagères à pots** sur les deux murs, lanternes sur potences.

Meubles modélisés seulement quand aucun bloc de mod ne convient : tonneaux debout, caisses empilées, coffres,
rouleaux de cordage, tapis, potences de lanternes. Sans les mods, chaque bloc est remplacé par une boîte de
même taille (le navire reste complet et utilisable).

## 4. Contraintes techniques

* Grille 22 × 24 × 56 cellules (11 × 12 × 28 blocs), ~6 Ko ; murs, planchers et plafonds des pièces dessinés
  **sur les limites de la grille** : ce qui est dessiné est ce qui bloque.
* La balustrade du poste de pilotage fait 1,5 bloc (pas de saut par-dessus en vol) ; le **bastingage du pont avant**
  est vertical côté pont, d'une cellule d'épaisseur au moins, et bloque à 1,5 bloc (la lisse dessinée est à 1,25) : pas
  d'escalier de cellules le long du bordé évasé, pas de saut dessus ; aucun meuble solide contre lui ni contre la
  balustrade (caisses, tonneaux et bancs du pont avant, du coin de stockage et du poste de pilotage sont traversables) ;
  la rambarde de l'escalier de caisses bloque à 2 blocs au-dessus de chaque marche ; vitres solides. Une recherche de
  chemin (pas de 0,6 et saut de 1 bloc) ne trouve aucune place debout sur un bastingage ou une rambarde (`SkiffTest`).
* Le toit, les ailes, les tubes et la pique ne sont pas des surfaces où l'on marche, mais des **sondes de
  terrain** couvrent tout le volume (coque, poutre, toit, perches, tubes, ailes, quille étagée, pique, consoles :
  ~280 points) : le pilote automatique aérien et la pose les respectent ; la pose vérifie toute la place (au-dessus du
  sol, de l'eau ou d'un toit).
* **Monter à bord depuis le sol** : posé, le navire a sa coque à ~8 blocs du sol (les ailes et la pique pendent
  dessous). Les ailes, la quille étagée et la pique ont des **boîtes de clic** (jamais solides) : un joueur au sol qui
  fait clic droit sur la pointe d'une aile ou sur la pique monte à bord (et un administrateur peut le récupérer
  accroupi + clic gauche) ; à bord, cliquer une aile ne fait rien. Ajout générique et sans effet sur les autres
  navires : `ShipGeometry.Spec.pickBoxes` (vide par défaut).
* Modèle ~6 600 cubes (coque en panneaux inclinés entre stations, toile en éventail de 28 pans, ailes en
  lamelles le long des nervures puis du bord libre), une texture 512 × 512 ; deux passes anti-z-fighting à l'export
  (`tools/zfight.py` puis une passe plus large pour les faces presque parallèles). Les os des pièces, meubles et ferrures sont masqués au-delà
  de 48 blocs, les petits détails au-delà de 80 (moteur de rendu commun).

## 5. Pilotage

Prendre la barre : clic droit sur la roue. Mêmes touches que les autres aéronefs (touches de déplacement de
Minecraft, modifiables dans *Options → Commandes*) : avancer / ralentir-reculer, tourner, **Espace** monter,
**Ctrl** descendre, Maj quitter. Réglages par défaut (section `rustic_skiff` de `config/medievalships.json`) :
vitesse normale 6,2 blocs/s (rapide 9,5), accélération 1,1, virage jusqu'à 20°/s, montée 2,4 blocs/s avec une
accélération verticale de 1,8 — **plus vif que le dirigeable steampunk** (accélération 0,55, 12°/s, montée 1,6).
Pilote automatique et routes : ceux des aéronefs du mod (`/ship route ...`, destinations et escales
sauvegardées).

## 6. Rapport de test

* Tests unitaires (`SkiffTest`, `NewShipModelsTest`, `NoZFightingTest`) : formes identiques à
  `tools/skiff_shape.py`, silhouette (coque plus étroite que le poste, bouchain pincé, ailes près des flancs, pique),
  ponts et pièces praticables, portes, trappe, escaliers, échelle, balustrades, vitres, **bastingage vertical et
  continu**, **aucun chemin (pas de 0,6 et saut) vers le dessus d'un bastingage ou d'une rambarde**, aucun meuble
  solide près de la balustrade, aucune sortie à travers la coque, sièges et leurs places pour se relever, **clic depuis
  le sol sous le navire** (aile, pique), vol (stationnaire, montée rapide, virage serré, arrêt au-dessus du sol), os
  et animations du modèle, aucune face en z-fighting.
* Test en jeu (`SkiffGameTest`, appelé par `ShipClientGameTest`) : pose en l'air, captures des vues de la
  planche et des pièces, **un joueur au sol sous le navire clique la pointe d'une aile et monte à bord**, marche sur le
  pont avant, entrée dans la cabine, vol depuis la barre (montée, avant,
  virage), animations, descente du pilote sur le poste, objet.

Limites connues : les vues de la planche se contredisent (largeur du toit et des ailes : la vue de dessus les montre
écartées, les vues avant et arrière pendantes) — le modèle suit les vues avant et arrière ; la cale est basse
(2 blocs) comme dans une vraie barque et se resserre vers le bas ; les blocs des mods gardent leurs propres couleurs
(le lit Farmhouse est blanc : une courtepointe rouge modélisée le recouvre) ; les caisses, tonneaux et bancs posés
contre le bastingage ou la balustrade se traversent (sinon ils feraient une marche pour passer par-dessus en vol).
