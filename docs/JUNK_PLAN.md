# La Jonque du Dragon (`dragon_junk`) — analyse, plan et guide du joueur

Planche de référence : `scratchpad/ref/dragon_junk_ref.png` (grande perspective, vues de côté, de dessus, avant,
arrière et cinq vues intérieures : pont principal, pont devant la maison de poupe, salle principale, réserve,
chambre). Une jonque d'inspiration asiatique, longue coque sombre, grande voile rouge lattée peinte d'un dragon noir,
montrée en vol au ras de l'eau : elle vole comme les autres aéronefs du mod et peut **planer au ras de l'eau**.

Comparaison planche / modèle (les 5 vues et les pièces) : [`preview_dragon_junk.png`](preview_dragon_junk.png).

Les pièces ne passent **pas** par Valkyrien Skies (non utilisé par ce mod) : comme le Nautilus, le Vieux Corsaire et le
Léviathan, la jonque décrit ses pièces par une **grille intérieure** (cellules de 0,5 bloc, `tools/junk_interior.py`)
que le mod lit pour les collisions, les portes, l'échelle et le volume où l'on est transporté. On marche, on s'assoit,
on change de niveau et on regarde par les fenêtres pendant le vol, en multijoueur, sans glisser à travers les murs.

## 1. Mesures sur la planche

Échelle retenue sur la vue de côté (498 × 312 px de la planche 1536 × 1024) : **0,1 bloc par pixel**, pont principal à
y = 240 px. Les vues de la planche ne sont pas tout à fait cohérentes entre elles (image générée) : le modèle suit
d'abord la vue de côté et la perspective, puis prend un compromis avec les vues de dessus, avant et arrière.

| Élément | Pixels (vue de côté) | Blocs (modèle) |
|---|---|---|
| Coque, face carrée de la proue → tableau arrière | x 75 → 465 | **39** (z +19,5 → −19,5) |
| Bec (éperon de planches claires) sous la proue | pointe (45, 282) | jusqu'à z +22,6, y −3,6 |
| Beaupré | x 7 | jusqu'à z +26,3 ; **46,7** hors tout (beaupré → arrière du toit) |
| Largeur (vue de dessus) | 88 px | **8,8** |
| Fond de coque | y 280 | −4,0 mesuré, **−4,5** retenu (place pour le pont inférieur) |
| Bande blanche (bordé de plâtre) avant : haut / bas | y 230 / 255 | +1,0 / −1,5 (préceinte sombre dessous) |
| Gaillard (dunette) après la coupure | y 215–217 | **+2,5** |
| Maison de poupe : murs, avant-toit, faîte | x 342 → 465, y 217 / 195 / 135 | z −8 → −19,5 ; avant-toit +5 ; faîte **+10,5** |
| Toit : 4 rangs superposés, débord | x 330 → 474 | z −5,8 (pignon avant, penché vers l'avant) → −20,4 (croupe) ; ±5,4 |
| Maison du capot (abri de l'escalier) | x 230 → 280, faîte y 170 | z −1,5 → +4, faîte +6,8, côté bâbord |
| Mât : pied, inclinaison, tête | (100, 233) → (207, 17) | pied z +16,5 ; **incliné vers l'arrière de 26°** ; tête y +22 |
| Vergue de tête de la voile | y 80, x 157 → 203 | y +16, z +11,4 → +6,6 |
| Point d'amure / point d'écoute (vues de côté, dessus, avant) | (67, 207) / (250, 240) | z +20,2 y +3,3 / z +3 y +1,2, **±7** |
| Voile d'étrave (blanche) | x 30 → 72, y 227 → 262 | sous la vergue d'étrave, 3,3 de chute |
| Ancre (bâbord) | x 197, y 242 → 300 | z +7,3, de −0,3 à −6,4 |
| Escalier extérieur (bâbord) | x 325 → 350, y 242 → 270 | z −8,3 → −4,6, y +2,3 → −2,6 |

**Voile** : vues de dessus et de face, la grande voile forme un **V** (une tente vue de l'avant) : deux pans lattés
pendent de la courte vergue sous la tête du mât, leur ralingue avant près de l'axe jusqu'au bout du gui avant, leurs
points d'écoute écartés à ±7 et tenus par de **longues perches claires** qui descendent vers l'arrière le long des
flancs. Le bas de chaque pan est échancré en **arche** autour du mât (vues de côté et perspective). Le **dragon noir**
est peint dans la texture de la voile (vecteur dessiné par `tools/junk_dragon.py`) : tête à gauche (vers la proue)
gueule ouverte, crocs, œil rouge, deux longues cornes, crinière en flammes, moustaches ; corps annelé en S, crête de
pointes, quatre pattes griffues, queue enroulée terminée par une touffe en flammes. Chaque pan le montre tourné vers la
proue (le pan tribord le voit en miroir).

## 2. Structure, matériaux, éléments mobiles

* **Coque** : bordé de planches sombres sur 38 couples (fond plat qui s'arrondit au bouchain, flancs droits, arrière en
  V jusqu'au tableau), **bec** de planches claires cerclé de fer pointant vers l'avant sous la **proue carrée**, quille,
  préceintes sombres ; à l'avant une **bande de blocs de plâtre blancs** entre des montants sombres, lisse de plat-bord ;
  à l'arrière des **panneaux laqués rouges** entre des montants serrés sous une bande blanche ; tableau plat (rouge,
  blanc), mèche du gouvernail au milieu, **gouvernail** de planches sombres sous la voûte.
* **Gaillard** à +2,5 : balustrade de laque rouge ajourée et poteaux sombres, **barre** (roue) devant le porche.
* **Maison de poupe** : murs de **plâtre blanc à pans de bois sombres** (lisses, poteaux, écharpes), fenêtres à croisillons
  éclairées (côtés, arrière, façade), porte à deux battants laqués, lanternes ; pignon avant de plâtre et poutres avec le
  médaillon au dragon enroulé, porche sous l'avancée du toit (poteaux sur dés de pierre, consoles).
* **Toit rouge à quatre rangs** sur un profil concave : chaque rang déborde sur le précédent, bord relevé, tuiles rondes,
  pannes sombres à **bouts relevés coiffés de pommeaux clairs**, arêtiers, faîtage et épis, **bardeaux de rive** du
  pignon avant, **lattes de bambou** (en long et en travers), lanternes aux angles, **hampe** penchée vers l'arrière
  sur le faîte avec sa flamme rouge.
* **Maison du capot** (bâbord, à la coupure) : murs de panneaux laqués rouges, porte vers la proue, toit à deux pans et
  deux rangs à bouts relevés, **poteau d'angle blanc sculpté** au médaillon du dragon.
* **Gréement** : mât sombre cerclé de fer et de cordage, chouque, croisillon, poulie et chaîne de la vergue, haubans,
  étai vers le beaupré, deux étais vers la hampe de poupe, balancines, écoutes, amures, bosses ; **gui avant**, perches
  d'écoute, beaupré et sa vergue avec la **petite voile blanche lattée**, flamme rouge en tête de mât.
* **Ancre** pendue à sa chaîne sous un bossoir bâbord, **escalier extérieur** bâbord, **lanternes** sur dés de pierre,
  bittes, caillebotis, caisses et tonneaux.

**Éléments animés** (petits os, le reste vient du cache statique du moteur de rendu) : `steer` (roue et gouvernail),
`sail_wind` (les deux pans respirent et se balancent, la voile d'étrave bat), `streamer_wave` (flammes), `lantern_sway`
(lanternes suspendues), `rope_sway` (bouts mous sous la vergue), `door_0..4`. Le vaisseau flotte en l'air (léger
balancement de ±0,06 bloc, `ShipModels.Visual.hover`). Effets client (`JunkEffects`) : embruns le long des flancs et
sillage quand elle rase l'eau, filets de vent au bout des perches en route.

## 3. Niveaux et pièces (y = 0 au pont principal, +z = proue)

| Niveau | Pièces |
|---|---|
| Gaillard / maison de poupe (+2,5) | pont du gaillard, **barre** (pilote debout derrière la roue, z −5,6), porche ; **cabine de poupe** (z −8,5 → −19, plafond +6) : table laquée et tabourets sur un tapis, assiettes de porcelaine bleue et blanche, bureau du capitaine et fauteuil face à la porte, bibliothèques, canapé rouge, cabinet à liqueurs, étagères de bocaux, fenêtres à croisillons, lanternes, charpente apparente |
| Pont principal (0) | ouvert de la proue à la coupure : mât, caillebotis, lanternes sur dés de pierre, bittes, bancs, caisses, tonneaux, cordages ; **panneau** et échelle vers la réserve ; **maison du capot** (escalier vers la salle principale) ; escalier vers le gaillard (tribord) ; porte de la chambre dans la cloison de la coupure |
| Sous le gaillard (−0,5) | **chambre** : lit sous sa couverture rouge, coffre au pied du lit, table de nuit et lanterne près de la fenêtre, étagère de bouteilles, tapis, commode, armoire, chaise, chevet et sa lanterne ; dans le coin avant tribord un **fauteuil à bascule** devant une table basse et son échiquier, une étagère de livres et de bouteilles, un portemanteau et une horloge près de la porte |
| Pont inférieur (−3) | **salle principale** (z −1,5 → +7,5) : grande table et sa carte sur le tapis rouge, tabourets, canapé rouge, étagères de bouteilles et bocaux, écritoire et lanterne près d'un hublot, coffre ; **réserve** (z +8 → +17) : deux piliers sur dés (pleins), caisses empilées, tonneaux couchés et debout, sacs, caisses de récoltes, bocaux, cordages, échelle |

Portes : 0 cabine de poupe (deux battants), 1 chambre, 2 maison du capot, 3 réserve (deux battants), 4 panneau du pont.
Escaliers de 0,5 bloc (gaillard, capot) ; échelle de la réserve. Toutes les pièces sont fermées par au moins une cellule
pleine sur leurs six faces : aucune ne s'ouvre sur le vide (`JunkTest.noWayOut`) ; toutes sont atteintes depuis le pont
principal (`JunkTest.roomsConnected`, `junk_interior.walkable_report`).

## 4. Pilotage, vol, pilote automatique

Physique `Flight` des aéronefs, maniabilité **intermédiaire** entre le Grand Dirigeable de Cristal (lent, majestueux) et
le Navire Volant Rustique (agile) : 2,4 / 5,0 / 7,8 blocs/s, accélération 0,55, virage max 11°/s, montée 1,7 et
descente 1,45 bloc/s (accélération verticale 0,9). Touches : Z/S vitesse, Q/D cap, Espace monter, Ctrl descendre,
Maj quitter (touches vanilla configurables). **Au ras de l'eau** : en descendant au-dessus de l'eau, la quille s'arrête
à 0,8 bloc de la surface (l'ancre trempe) et remonte si elle a été poussée plus bas (`DragonJunkEntity`, seule la vitesse
verticale est touchée avant le pas de vol normal : collisions et transport des passagers inchangés). Pilote
automatique : itinéraires `air` du mod, 5 blocs de marge au-dessus du relief, approche des escales à 32 blocs, il peut
descendre à 0,6 bloc au-dessus de l'eau ou du sol ; sondes de terrain sur tout le volume (coque, bec, maison, toit, mât,
vergue, voiles, perches, beaupré, ancre, escalier).

## 5. Fichiers

`tools/junk_shape.py` (formes, = `JunkLayout.java`), `tools/junk_interior.py` (grille), `tools/junk_decor.py` (meubles des
mods et sièges), `tools/junk_texture.py` (atlas, voile, intérieur, icône), `tools/junk_dragon.py` (le dragon),
`tools/generate_junk.py` (modèle). Java : `core/JunkLayout`, `entity/DragonJunkEntity`, `client/JunkEffects`. Tests :
`JunkTest` (forme, pièces, portes, escaliers, échelle, sièges, sondes, vol), `NewShipModelsTest` / `NoZFightingTest`
(modèle), `JunkGameTest` (en jeu).

## 6. Vérifications

* **Rendus de comparaison** (`docs/preview_dragon_junk.png`) : les 5 vues de la planche à côté du modèle (rendu logiciel
  du `.bbmodel`), puis les pièces vues depuis les points de vue des vues intérieures de la planche, avec les **meubles des
  mods dessinés comme le jeu les dessine** (modèles de blocs des mods, état par défaut).
* **JUnit** (`JunkTest`, 13 tests) : formes = générateur Python, dimensions, sondes du pilote automatique sur tout le
  volume, sièges (assis et descente libre), sols et hauteur sous plafond pièce par pièce, portes qui ferment, escaliers et
  échelle, aucune pièce ouverte sur le vide, toutes les pièces atteintes depuis le pont, secours et chutes, fichier de
  grille, maniabilité intermédiaire, vol ; plus `NewShipModelsTest` (os, animations, quads Java = quads Python) et
  `NoZFightingTest`.
* **En jeu** (`JunkGameTest`, appelé par `ShipClientGameTest`, CI « In-game test », variantes vanilla / lithium / décor) :
  pose au-dessus d'un bassin, rien dans la coque, vol stationnaire, marche sur le pont et entrée dans la cabine de poupe par
  sa porte, pilotage (montée, avance, virage, roue animée), descente au ras de l'eau (la quille s'arrête entre 0,4 et 1,4
  bloc au-dessus de la surface), descente du pilote sur le gaillard, `/ship give`, 13 captures (5 vues extérieures, les
  pièces, au ras de l'eau).

**Limites** : les vues de la planche ne sont pas cohérentes entre elles (image générée), le modèle suit la vue de côté et
la perspective ; le toit est un peu plus haut et plus raide que sur la vue arrière ; les sculptures du pignon avant sont
plus simples que sur la perspective. Les pièces sont un peu plus grandes que sur les vues intérieures (il faut 2 blocs de
hauteur sous plafond et des passages de 1 bloc pour marcher).
