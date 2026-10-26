# Le Navire Volant Rustique (`rustic_skiff`) — analyse, plan et guide du joueur

Planche de référence : `scratchpad/ref/rustic_skiff_ref.png` (grande perspective, vues de côté, de dessus,
avant, arrière et quatre vues intérieures : pont avant, façade de la cabine et poste de pilotage, chambre,
cale / couloir de stockage). Une vieille barque de bois faite main, transformée en engin volant : petite,
agile, rapiécée, médiévale-fantastique (jamais un avion moderne).

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
| Poutre de proue (beaupré court) | x 20 → 70 | jusqu'à z +18 |
| Tubes de poupe | x 330 → 437 | 7,9 (8,4 pour le tube central) |
| Longueur totale | x 20 → 437 | **39** (poutre → bouches des tubes) |
| Fond de coque au milieu | y 178 | −3,0 mesuré, **−3,4** retenu (place pour la cale) |
| Bastingage du pont avant / tête de proue | y 135 / 122 | +1,0 / +2,8 (proue relevée en banane) |
| Cabine (façade → poupe), toit = poste de pilotage | x 228 → 330, y 116 | z −3 → −13, **+3,0** |
| Balustrade du poste de pilotage | y 92–100 | **1,5** au-dessus du poste (hauteur de poitrine) |
| Toile du toit : avant-toits / faîte | y 58–80 / 8–14 | **8,9** (pans affaissés à 7,9) / **12,5**, mât central 13,4 |
| Étendue du toit (côté / dessus) | x 215 → 395 | compromis : z −0,1 → −16,9, 11,8 de large |
| Ailes avant : racine, coin haut, pointe | (207,178) (277,200) (267,238) | (z −0,6, y −2,2) (−7,4, −4,6) (−6,4, −9,0) |
| Ailes arrière : racine, coin haut, pointe | (320,160) (400,160) (343,268) | (−11,9, −1,2) (−18,6, −1,7) (−14,2, −11,0) |

Vue de dessus : **proue étroite** (≈ 4 blocs) puis un **épaulement** brusque vers z ≈ +5 et un corps large
(8 blocs) jusqu'à la poupe — le modèle mélange les deux plans entre z +3,5 et +6,5. Vue avant : le poste de
pilotage **déborde** de la coque (4,9 de demi-largeur contre 4,0), le toit a à peu près la largeur du poste,
la coque est en V et une **pique de quille** descend au centre (sous le caisson de poupe), les ailes
pendent presque verticalement. Vue arrière : quatre gros tubes (2 × 2) et un tube central plus mince.

Proportions : 26 × 8 blocs de coque, 39 de long hors tout, 13 de large ailes comprises, 25 de haut (du fleuron
du mât central à la pointe des ailes arrière). Petit à côté du Léviathan (65 blocs) et du Vieux Corsaire
(53), plus grand que le dirigeable steampunk (22), mais **plus maniable** que lui.

## 2. Structure, matériaux, éléments mobiles

* **Coque** longue en banane, bordé de planches brunes irrégulières rapiécées (longueurs d'autres bois, plaques
  de fer clouées), lisses sombres, **planches de renfort verticales moussues**, **lisse de plat-bord moussue**
  avec gros blocs de mousse, anneaux de fer et **chaînes en festons** le long des flancs, trois **lanternes au
  bout de chaînes** sous la coque de chaque bord, quille remontant en étrave jusqu'à la tête de proue, poutre de
  proue cerclée de fer avec sous-barbe en chaîne et lanterne.
* **Appentis de proue** en planches claires délavées (faîtage, chevalet en A, toile roulée) : le **coin de
  stockage**.
* **Pont avant ouvert** (deux marches sous l'appentis), **caillebotis de fer** au-dessus de l'échelle de la cale.
* **Cabine** centrale-arrière : murs de planches verticales sur poteaux, **fenêtre à croisillons éclairée**
  de chaque bord, façade avec porte à deux battants et deux lanternes, **escalier de caisses** à tribord jusqu'au
  poste de pilotage.
* **Poste de pilotage** sur le toit de la cabine : plancher, poutres de rive en débord sur consoles,
  **balustrade rustique** à poteaux moussus, **roue** sur sa colonne, bancs, lanternes.
* **Grand toit de toile beige usée** sur quatre **perches écartées** (pointes de fer au-dessus de la toile) et un
  mât central : toile tachée et rapiécée, coutures, pans affaissés entre les perches, **lanières déchirées**
  pendant des avant-toits (et quelques-unes sous la toile).
* **Deux longues perches inclinées** à la poupe (mâts de charge) avec cordages jusqu'aux tubes et au toit.
* **Cordes de fanions déchirés** (beige, rouge, noir) de la poutre de proue aux perches avant du toit.
* **Cinq tubes de bronze** cerclés de fer sur le tableau arrière (berceau de sangles), bouches évasées au fond
  rougeoyant avec un **ventilateur** à l'intérieur.
* **Quatre ailes de toile** souples et triangulaires sur **nervures de bois**, bord libre festonné, pointes de
  fer, accrochées sous les flancs (charnières de fer) ; caisson de poupe et pique de quille ferrée.

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
de la rambarde de l'escalier ; **trappe à caillebotis** (2) du pont avant au-dessus de l'**échelle** de la cale ;
**escalier** de la salle commune vers la cale (ouverture bordée de rambardes) ; **escalier de caisses** du pont
avant au poste de pilotage (passage dans la balustrade). Toutes les pièces sont reliées et fermées (aucune
cellule de pièce ne touche l'air extérieur ; `SkiffTest`).

Ameublement (mods de décoration de l'utilisateur d'abord, comme sur les vues intérieures) :

* **Pont avant** (vue 1) : caisses et tonneau contre la façade, rouleau de cordage, banc sur le bastingage ;
  sous l'appentis caisses, tonneau couché (Lands of Icaria), sacs (Farmer's Delight), coffre, lanterne.
* **Façade / poste** (vue 2) : porte, lanternes, escalier de caisses ; roue, balustrade, lanternes de coin.
* **Salle commune** : table et chaises (Furnish), bouteille, verre, assiette, lanterne suspendue (Farmhouse
  Decorations), buffet (Furnish) avec livres et lanterne, étagère à pots au-dessus de l'escalier, caisse,
  tonneau, chemin de table rouge.
* **Chambre** (vue 3) : lit (Farmhouse Decorations) sous la fenêtre, coffre au pied du lit, grande bibliothèque,
  bureau avec livres ouverts, carte et lanterne, sa chaise, commode, tapis rouge à bordure dorée, lanternes.
* **Cale** (vue 4) : chemin rouge, établi et panneau d'outils, casiers (« les portes de droite »), caisses,
  tonneaux, sacs, étagères à pots, lanternes sur potences.

Meubles modélisés seulement quand aucun bloc de mod ne convient : tonneaux debout, caisses empilées, coffres,
rouleaux de cordage, tapis, potences de lanternes. Sans les mods, chaque bloc est remplacé par une boîte de
même taille (le navire reste complet et utilisable).

## 4. Contraintes techniques

* Grille 22 × 24 × 56 cellules (11 × 12 × 28 blocs), ~6 Ko ; murs, planchers et plafonds des pièces dessinés
  **sur les limites de la grille** : ce qui est dessiné est ce qui bloque.
* La balustrade du poste de pilotage fait 1,5 bloc (pas de saut par-dessus en vol) ; bastingage du pont avant
  d'un bloc ; vitres solides.
* Le toit, les ailes, les tubes et la pique ne sont pas des surfaces où l'on marche, mais des **sondes de
  terrain** couvrent tout le volume (coque, poutre, toit, perches, tubes, ailes, pique : ~250 points) : le
  pilote automatique aérien et la pose les respectent ; la pose vérifie toute la place (au-dessus du sol, de
  l'eau ou d'un toit).
* Modèle ~4 100 cubes (coque en panneaux inclinés entre stations, toile en éventail, ailes en lamelles le long
  des nervures), une texture 512 × 512.

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
  `tools/skiff_shape.py`, ponts et pièces praticables, portes, trappe, escaliers, échelle, balustrades, vitres,
  aucune sortie à travers la coque, sièges et leurs places pour se relever, vol (stationnaire, montée rapide,
  virage serré, arrêt au-dessus du sol), os et animations du modèle, aucune face en z-fighting.
* Test en jeu (`SkiffGameTest`, appelé par `ShipClientGameTest`) : pose en l'air, captures des vues de la
  planche et des pièces, marche sur le pont avant, entrée dans la cabine, vol depuis la barre (montée, avant,
  virage), animations, descente du pilote sur le poste, objet.

Limites connues : les vues de la planche se contredisent (largeur du toit et des ailes) — compromis expliqué
plus haut ; la cale est basse (2 blocs) comme dans une vraie barque ; les blocs des mods gardent leurs propres
couleurs (le lit Farmhouse est blanc, la planche le montre rouge).
