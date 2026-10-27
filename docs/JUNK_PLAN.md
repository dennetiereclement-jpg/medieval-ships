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
| Beaupré (court, montant de 13°) | x 30 | jusqu'à z +23,4 ; **44,3** hors tout (beaupré → arrière du toit) |
| Largeur (vue de dessus) ; face carrée de la proue | 88 px ; ~50 % de la largeur | **8,8** (pleine de z −5 à +4) ; **4,8** |
| Fond de coque | y 280 | quille **−5,1** au milieu, relevée vers l'avant (−4,3 à z +14) et en voûte vers l'arrière |
| Bande blanche (bordé de plâtre) avant : haut / bas | y 230 / 245 (perspective : ~1,6 bloc sur une coque sombre deux fois plus haute) | +1,0 (relevé à +1,75 à la proue) / −0,5, préceinte sombre −0,9 → −0,5 |
| Gaillard (dunette) après la coupure | y 215–217 | **+2,5** |
| Maison de poupe : murs, avant-toit, faîte | x 342 → 465, y 217 / 195 / 135 | z −8 → −19,5 ; avant-toit +6,15 (≈2,6 de mur blanc au-dessus de la galerie, vues arrière et de côté) ; faîte **+13** |
| Toit principal : 4 rangs superposés, débord | x 330 → 474 | z −8,6 (pignon avant) → −20,9 (croupe au-dessus de la galerie) ; ±5,2 |
| Toit du porche (pignon avant plus bas) | x 325 → 342 | z −5,6 → −8,6, faîte +10,1 (~38°) |
| Galerie de poupe (balcon) | vue arrière | au niveau du gaillard, +0,6 hors bord, +1,05 derrière le tableau |
| Maison du capot (abri de l'escalier) | x 230 → 280 | z −1,5 → +4, toit en appentis +4,6 → +2,4, côté bâbord |
| Mât : pied, inclinaison, tête | (100, 233) → (207, 17) | pied z +16,5 ; **incliné vers l'arrière de 26°** ; tête y +22 |
| Vergue de tête de la voile | y 80, x 157 → 203 (vues avant et perspective : à ~4 blocs sous la tête du mât) | y +18, z +10,4 → +5,6 |
| Point d'amure / point d'écoute (vues de côté, dessus, avant) | (67, 207) / (250, 240) ; vue de dessus ±1,45 × la demi-largeur | z +19,6 y +3,3 / z +3 y +1,2, **±6,4** |
| Voile d'étrave (blanche) | x 30 → 72, y 227 → 262 | sous une courte vergue juste devant la proue, 2,3 de chute |
| Ancre (bâbord) | x 197, y 242 → 300 | z +7,3, bossoir saillant de 1,2 ; ancre de −5,3 à −7,6 (bien sous la quille) |
| Escalier extérieur (bâbord) | x 325 → 350, y 242 → 270 | z −8,3 → −4,6, y +2,3 → −2,6 |

**Vue arrière** (la plus revue) : en ogive, du haut vers le bas : toit à quatre rangs empilés (pagode, cornes relevées
à chaque rang, épi), mur de plâtre crème à **trois fenêtres en arc** éclairées entre des panneaux sculptés, **galerie** à
balustres clairs tout autour de la poupe, **bandeau rouge** étroit sous la galerie, lisse claire, puis la **voûte** sombre
en V qui descend vers la quille, l'**étambot clair** au milieu, le grand **gouvernail** dessous.

**Voile** : vues de dessus et de face, la grande voile forme un **V** (une tente vue de l'avant) : deux pans lattés
pendent de la courte vergue sous la tête du mât, leur ralingue avant près de l'axe jusqu'au bout du gui avant, leurs
points d'écoute écartés à ±6,4 et tenus par de **longues perches claires** qui descendent vers l'arrière le long des
flancs. Le bas de chaque pan est échancré en **arche** autour du mât (vues de côté et perspective). Le **dragon noir**
est peint dans la texture de la voile (pochoir vectoriel dessiné par `tools/junk_dragon.py`, d'après la perspective) :
une haute colonne deux fois plus haute que large, du cinquième supérieur du pan jusqu'au-dessus de la bordure, un peu en
arrière du milieu ; la tête à gauche (vers la proue) au quart de la hauteur, gueule ouverte, crocs, petits bois,
moustaches, une **crête de longues mèches** qui monte au-dessus d'elle ; un corps épais en S fait d'**écailles noires
séparées par de fines bandes de toile rouge** et d'une fine coupe le long du ventre (l'effet pochoir), des flammes en
feuilles le long du dos, quatre pattes à trois griffes, la queue qui descend vers l'arrière et finit en **éventail de
flammes**. Les lattes sont de fines perches sombres (le dragon reste lisible). Rouge de la toile éclairci (le jeu
l'assombrit d'environ moitié), coutures discrètes, échancrure en arche plus
petite qui laisse un pied de toile d'un cinquième de la bordure. Chaque pan le montre tourné vers la proue (le pan
tribord le voit en miroir).

## 2. Structure, matériaux, éléments mobiles

* **Coque** : bordé de planches sombres sur 39 couples, **sections en V arrondi** (fond en V sous le pont inférieur,
  bouchains fermes, flancs qui rentrent dès +1), plan qui s'affine régulièrement sur le tiers avant jusqu'à la **proue
  carrée** (moitié de la largeur), **quille relevée** vers l'avant, **lisse relevée** à la proue ; **bec** de planches
  claires cerclé de fer qui sort de la proue sombre ; à l'arrière la **voûte** remonte en V jusqu'au petit tableau incliné (pied à +0,9,
  haut à +2,5 et 0,4 plus en arrière), l'**étambot clair** cerclé de fer le long de son milieu. Préceintes sombres qui
  remontent avec la voûte ; à l'avant une **bande de blocs de plâtre blancs** (≈1,5 de haut) entre des montants sombres,
  sur une coque sombre deux fois plus haute ; à l'arrière
  des **panneaux laqués rouges** entre des montants serrés (leur pied remonte vers la poupe) sous une **frise claire à
  anneaux sombres**. Grand **gouvernail** sous la voûte (z −16 → −17,9, jusqu'à −5,2), bord de fuite clair.
* **Gaillard** à +2,5 : balustrade de **balustres clairs** entre lisses et poteaux sombres, **barre** (roue) devant le
  porche. La **galerie de poupe** (balcon décoratif) fait le tour de la maison au même niveau, sur des consoles sombres.
* **Maison de poupe** : murs de **plâtre blanc dans une grille de poteaux et de lisses sombres** (sans écharpes), fenêtres
  à croisillons éclairées, **frise sombre à consoles** sous l'avant-toit ; mur arrière à **trois fenêtres en arc** dans des
  cadres sculptés, panneaux sculptés entre elles ; façade : porte à deux battants laqués dans un cadre sombre, crête
  sculptée, **deux lanternes** de part et d'autre.
* **Porche** sous son **propre pignon, plus bas** (~38°) : poteaux sur dés de pierre, consoles, poutre d'avant-toit,
  pignon garni de **panneaux sculptés sombres**, **médaillon** rond (disque beige, nœud sombre), lanternes ; **bardeaux de
  rive sombres et lourds** terminés en **volutes**, crête sculptée au sommet.
* **Toit principal rouge à quatre rangs empilés** (profil de pagode : raide aux avant-toits, plus doux vers le faîte),
  chaque rang déborde sur le précédent avec un **bord relevé**, tuiles rouge brique en rangs à bords arrondis, pannes
  sombres, **cornes relevées en trois segments** à chaque angle de rang, arêtiers, faîtage et épis recourbés, pignon avant
  garni de panneaux sculptés derrière le toit du porche, **grosses lattes de bambou** en quadrillage (4 × 4), lanternes
  aux angles, **hampe** penchée vers l'arrière sur le faîte avec sa flamme rouge.
* **Maison du capot** (bâbord, à la coupure) : murs de panneaux laqués rouges, porte vers la proue, **toit en appentis**
  qui descend vers le bordé depuis un faîtage de plâtre blanc côté axe, **poteau d'angle blanc** au médaillon sculpté.
* **Gréement** : mât sombre cerclé de fer et de cordage, chouque, croisillon, poulie et chaîne de la vergue, haubans,
  étai vers le beaupré, deux étais vers la hampe de poupe, balancines, écoutes, amures, bosses ; **gui avant**, perches
  d'écoute, beaupré et sa vergue avec la **petite voile blanche lattée**, flamme rouge en tête de mât.
* **Ancre** pendue bien sous la quille à une **grosse chaîne** de maillons ouverts sous un bossoir bâbord saillant,
  **escalier extérieur** bâbord (décoratif : il monte à la galerie, sans collisions ; la balustrade du gaillard reste
  fermée), **échelle de corde** sur la face de la proue (qui tombe sur le bec remonte à bord), **lanternes** sur dés de
  pierre le long des pavois, bittes, caillebotis (le vide sombre de la cale sous ses barreaux), caisses et tonneaux.

**Éléments animés** (petits os, le reste vient du cache statique du moteur de rendu) : `steer` (roue et gouvernail),
`sail_wind` (les deux pans respirent et se balancent, la voile d'étrave bat), `streamer_wave` (flammes), `lantern_sway`
(lanternes suspendues), `rope_sway` (bouts mous sous la vergue), `door_0..4`. Le vaisseau flotte en l'air (léger
balancement de ±0,06 bloc, `ShipModels.Visual.hover`). Effets client (`JunkEffects`) : embruns le long des flancs et
sillage quand elle rase l'eau, filets de vent au bout des perches en route.

## 3. Niveaux et pièces (y = 0 au pont principal, +z = proue)

| Niveau | Pièces |
|---|---|
| Gaillard / maison de poupe (+2,5) | pont du gaillard, **barre** (pilote debout derrière la roue, z −5,6), porche ; **cabine de poupe** (z −8,5 → −19, plafond +6) : table de palétuvier et tabourets sur un tapis, assiettes de porcelaine bleue et blanche, bureau du capitaine et fauteuil face à la porte, bibliothèques, canapé rouge, cabinet à liqueurs, étagères de bocaux, fenêtres à croisillons, lanternes, charpente apparente |
| Pont principal (0) | ouvert de la proue à la coupure : mât, caillebotis, lanternes sur dés de pierre, bittes, bancs, caisses, tonneaux, cordages ; **panneau** et échelle vers la réserve ; **maison du capot** (escalier vers la salle principale) ; escalier vers le gaillard (tribord) ; porte de la chambre dans la cloison de la coupure |
| Sous le gaillard (−0,5) | **chambre** : lit sous sa couverture rouge le long du bordé bâbord sous la fenêtre, table de nuit et lanterne à sa tête, coffre au pied ; côté tribord le **bureau** et sa chaise, sa lanterne et une étagère de bouteilles au-dessus, commode, armoire ; bibliothèque sur la cloison arrière, tapis au milieu ; à l'avant un **fauteuil à bascule** devant une table basse et son échiquier, un portemanteau et une horloge près de la porte |
| Pont inférieur (−3) | **salle principale** (z −1,5 → +7,5) : grande table et sa carte sur le tapis rouge, tabourets, canapé rouge, étagères de bouteilles et bocaux, écritoire et lanterne près d'un hublot, coffre ; **réserve** (z +8 → +17, qui s'étrécit vers la proue) : deux piliers sur dés (pleins) avec leurs lanternes, caisses empilées sur deux rangs le long des deux bords, râtelier à tonneaux, tonneaux, sacs de riz entassés, caisses de récoltes, étagères de bouteilles, bocaux, cordages, échelle |

Portes : 0 cabine de poupe (deux battants), 1 chambre, 2 maison du capot, 3 réserve (deux battants), 4 panneau du pont.
Escaliers de 0,5 bloc (gaillard, capot) ; échelle de la réserve. Toutes les pièces sont fermées par au moins une cellule
pleine sur leurs six faces : aucune ne s'ouvre sur le vide (`JunkTest.noWayOut`) ; toutes sont atteintes depuis le pont
principal (`JunkTest.roomsConnected`, `junk_interior.walkable_report`) ; de tout endroit atteint depuis le pont en sautant
(1 bloc), en tombant et par les échelles, on peut revenir sur le pont (`JunkTest.noTrapOutside`,
`junk_interior.trapped`) : le bec sous la proue a son échelle de corde. Le toit en appentis du capot est plein dans la
grille jusque sous ses tuiles (on marche dessus, jamais dedans).

## 4. Pilotage, vol, pilote automatique

Physique `Flight` des aéronefs, maniabilité **intermédiaire** entre le Grand Dirigeable de Cristal (lent, majestueux) et
le Navire Volant Rustique (agile) : 2,4 / 5,0 / 7,8 blocs/s, accélération 0,55, virage max 11°/s, montée 1,7 et
descente 1,45 bloc/s (accélération verticale 0,9). Touches : Z/S vitesse, Q/D cap, Espace monter, Ctrl descendre,
Maj quitter (touches vanilla configurables). **Au ras de l'eau, en pilotage manuel** : en descendant au-dessus de l'eau
calme, la quille s'arrête à 0,8 bloc de la surface (l'ancre trempe) et remonte si elle a été poussée plus bas
(`DragonJunkEntity`, décision dans `JunkLayout.skimVy`, testée par `JunkTest.skimsTheWater` ; seule la vitesse verticale
est touchée avant le pas de vol normal : collisions et transport des passagers inchangés). L'eau qui tombe (cascade,
colonne traversée) et l'eau suspendue au-dessus du vide sont ignorées. Pilote automatique : itinéraires `air` du mod,
5 blocs de marge au-dessus du relief, approche des escales à 32 blocs ; il garde l'**ancre** (point le plus bas) à
0,6 bloc au-dessus de l'eau ou du sol, soit la quille à environ 3 blocs : le rase-mottes est réservé au pilotage
manuel. Sondes de terrain sur tout le volume (coque, voûte, gouvernail, galerie, maison, toits, mât, vergue, voiles,
perches, beaupré, ancre, escalier).

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
* **JUnit** (`JunkTest`, 16 tests) : formes = générateur Python, forme de la coque (proue, rocker, voûte, tableau incliné,
  V de l'arrière), dimensions, sondes du pilote automatique sur tout le volume, sièges (assis et descente libre), sols et
  hauteur sous plafond pièce par pièce, portes qui ferment, escaliers et échelle, aucune pièce ouverte sur le vide, toutes
  les pièces atteintes depuis le pont, **aucun piège** hors des pièces (retour au pont depuis partout, bec compris), rase-
  mottes au-dessus de l'eau, secours et chutes, fichier de grille, maniabilité (bornes fixes entre les valeurs du Dirigeable
  de Cristal et du Navire Rustique, qui ne sont pas sur cette branche), vol ; plus `NewShipModelsTest` (os, animations, quads Java = quads Python) et
  `NoZFightingTest`.
* **En jeu** (`JunkGameTest`, appelé par `ShipClientGameTest`, CI « In-game test », variantes vanilla / lithium / décor) :
  pose au-dessus d'un bassin, rien dans la coque, vol stationnaire, marche sur le pont et entrée dans la cabine de poupe par
  sa porte, pilotage (montée, avance, virage, roue animée), descente au ras de l'eau (la quille s'arrête entre 0,4 et 1,4
  bloc au-dessus de la surface), descente du pilote sur le gaillard, `/ship give`, 13 captures (5 vues extérieures, les
  pièces, au ras de l'eau).

**Limites** : les vues de la planche ne sont pas cohérentes entre elles (image générée) ; la vue arrière montre une coque
en ogive plus pointue que ce que permettent les pièces du pont inférieur (il leur faut leur largeur à −3) : le fond est en
V arrondi, la voûte en V franc ; la galerie de poupe et l'escalier extérieur sont décoratifs (sans collisions). Les
sculptures sont plus simples que sur la perspective. Les pièces sont un peu plus grandes que sur les vues intérieures (il
faut 2 blocs de hauteur sous plafond et des passages de 1 bloc pour marcher).
