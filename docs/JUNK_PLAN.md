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
| Maison de poupe : murs, avant-toit, faîte | x 342 → 465, y 217 / 195 / 135 | z −8 → −19,5 ; avant-toit +6,15 (≈2,6 de mur blanc au-dessus de la galerie, vues arrière et de côté) ; faîte **+13,4**, flèche +16,1 (vue arrière) |
| Toit principal : 4 rangs superposés, débord | x 330 → 474 ; vue arrière : rangs larges de 1 / 0,73 / 0,63 / 0,37 × l'avant-toit, coins relevés d'environ 1 bloc | z −8,6 (pignon avant) → −20,9 (croupe au-dessus de la galerie) ; ±5,2 (+0,3 aux coins) ; bords des rangs à 1,0 / 1,8 / 2,9 de l'avant-toit |
| Toit du porche (pignon avant plus bas) | x 325 → 342 | z −5,6 → −8,6, faîte +10,1 (~38°) |
| Galerie de poupe (balcon) | vue arrière (galerie ≈ 1,24 × le mur, avant-toit ≈ 1,34 ×) | au niveau du gaillard, +0,9 hors bord, +1,05 derrière le tableau |
| Maison du capot (abri de l'escalier) | x 230 → 280 | z −1,5 → +4, toit en appentis +4,6 → +2,4, côté bâbord |
| Mât : pied, inclinaison, tête | (100, 233) → (207, 17) | pied z +16,5 ; **incliné vers l'arrière de 26°** ; tête y +22 |
| Vergue de tête de la voile | y 80, x 157 → 203 (vues avant et perspective : à ~4 blocs sous la tête du mât) | y +18, z +10,4 → +5,6 |
| Point d'amure / point d'écoute (vues de côté, dessus, avant) | (67, 207) / (250, 240) ; vue de dessus ±1,45 × la demi-largeur | z +19,6 y +3,3 / z +3 y +1,2, **±6,4** |
| Voile d'étrave (blanche) | x 30 → 72, y 227 → 262 | sous une courte vergue juste devant la proue, 2,3 de chute |
| Ancre (bâbord) | x 197, y 242 → 300 | z +7,3, bossoir saillant de 1,2 ; ancre de −5,3 à −7,6 (bien sous la quille) |
| Escalier extérieur (bâbord) | x 325 → 350, y 242 → 270 | z −8,3 → −4,6, y +2,3 → −2,6 |

**Vue arrière** (la plus revue, reprise en détail pour la 1.9.x) : en ogive, du haut vers le bas : une **flèche** sombre à
bagues dorées au bout du faîtage ; le **toit à quatre rangs empilés**, chacun une jupe de tuiles rouges dont le bord
**se relève vers chaque angle** (le bord pend entre les angles), des **perches de bambou** posées sur chaque rang, croisées
aux angles et terminées par de **gros nœuds**, une **perche centrale** qui descend le long de la croupe ; sous le rang du bas
une **lourde poutre d'avant-toit** sur deux **poteaux d'angle à pommeau** (les « oreilles » de la vue arrière) d'où pendent
deux lanternes ; le mur de planches crème à **trois grandes fenêtres en arc** qui remplissent le mur entre la lisse de la
galerie et l'avant-toit (arcs et montants de bois sombre en saillie, clé sculptée, appui sur consoles) ; la **galerie**
dont le garde-corps est, autour de la poupe, fait de **panneaux pleins de planches claires** (un losange sculpté sombre
chacun) et le **poteau central clair** qui prolonge l'étambot ; le **bandeau rouge** de panneaux laqués entre des
**montants clairs** ; la **large lisse claire** posée sur des **consoles sombres** ; puis la **voûte** sombre en V, l'**étambot
clair** au milieu, le grand **gouvernail** dessous.

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
  claires cerclé de fer qui sort de la proue, le **brion** (le bas de la coque sous la proue, en avant de z +16) bordé des
  mêmes planches claires jusqu'à un montant sombre boulonné (vues de côté et perspective) ; à l'arrière la **voûte** remonte en V jusqu'au petit tableau incliné (pied à +0,9,
  haut à +2,5 et 0,4 plus en arrière), l'**étambot clair** cerclé de fer le long de son milieu. Préceintes sombres qui
  remontent avec la voûte ; à l'avant une **bande de blocs de plâtre blancs** (≈1,5 de haut) entre des montants sombres,
  sur une coque sombre deux fois plus haute ; à l'arrière
  des **panneaux laqués rouges** entre des montants serrés (leur pied remonte vers la poupe) sous une **frise claire à
  anneaux sombres**. Grand **gouvernail** sous la voûte (z −16 → −17,9, jusqu'à −5,2), bord de fuite clair.
* **Gaillard** à +2,5 : balustrade de **balustres clairs** entre lisses et poteaux sombres, **barre** (roue) devant le
  porche. La **galerie de poupe** (balcon décoratif) fait le tour de la maison au même niveau, sur des consoles sombres.
* **Maison de poupe** : murs de **planches crème** (leurs lignes se voient sur les vues de côté et arrière) **dans une grille de
  poteaux et de lisses sombres**, de petites **fenêtres à croisillons par paires**, hautes dans les murs latéraux, **frise
  sombre à consoles** sous l'avant-toit ; mur arrière à **trois grandes fenêtres en arc** (voir la vue arrière) ; façade :
  porte à deux battants laqués dans un cadre sombre, crête sculptée, **deux lanternes** de part et d'autre.
* **Porche** sous son **propre pignon, plus bas** (~38°) : poteaux sur dés de pierre, consoles, poutre d'avant-toit,
  **tympan de planches crème entre des bois sombres** (poinçon, entrait, contrefiches), **médaillon** rond (disque beige,
  nœud sombre), lanternes ; **bardeaux de rive lourds en bois clair** terminés en **volutes**, crête sculptée au sommet.
* **Toit principal rouge à quatre rangs empilés** (pagode) : chaque rang est une **jupe** de tuiles presque plate à son
  bord et plus raide sous le rang suivant, son bord posé au-dessus du haut du rang inférieur (une ligne d'ombre sous chaque
  bord, rangée de bouts de tuiles ronds, ligne de chevrons sombre) ; les **avant-toits se relèvent et s'écartent vers chaque
  angle** (jusqu'à ~1 bloc pour le rang du bas, de moins en moins vers le haut, un peu moins aux angles du pignon), les
  arêtiers finissent en **pointe recourbée** ; **perches de bambou** autour de chaque rang (croisées aux angles, gros
  nœuds), perches dans la pente, **perche centrale** sur la croupe ; faîtage, épi recourbé au pignon, **flèche** au bout
  arrière ; pignon avant en **planches crème entre des bois sombres** derrière le toit du porche, **bardeaux de rive clairs
  et lourds** qui suivent les rangs en escalier ; **poutre d'avant-toit** sur poteaux d'angle à pommeau, lanternes aux
  angles ; **hampe** penchée vers l'arrière sur le faîtage avec sa flamme rouge.
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
  mottes au-dessus de l'eau, secours et chutes, fichier de grille, maniabilité (bornes fixes ; l'ordre Dirigeable de Cristal < Jonque < Navire
  Rustique est vérifié par `ThreeFlyersTest`), vol ; plus `NewShipModelsTest` (os, animations, quads Java = quads Python) et
  `NoZFightingTest`.
* **En jeu** (`JunkGameTest`, appelé par `ShipClientGameTest`, CI « In-game test », variantes vanilla / lithium / décor) :
  pose au-dessus d'un bassin, rien dans la coque, vol stationnaire, marche sur le pont et entrée dans la cabine de poupe par
  sa porte, pilotage (montée, avance, virage, roue animée), descente au ras de l'eau (la quille s'arrête entre 0,4 et 1,4
  bloc au-dessus de la surface), descente du pilote sur le gaillard, `/ship give`, 13 captures (5 vues extérieures, les
  pièces, au ras de l'eau).

**Limites** : les vues de la planche ne sont pas cohérentes entre elles (image générée) ; la vue arrière montre une coque
en ogive plus pointue que ce que permettent les pièces du pont inférieur (il leur faut leur largeur à −3) : le fond est en
V arrondi, la voûte en V franc ; la vue arrière montre aussi un toit plus haut que la vue de côté : le toit (faîte +13,4,
flèche +16,1) prend un compromis entre les deux ; la galerie de poupe et l'escalier extérieur sont décoratifs (sans
collisions), comme les angles relevés du toit et sa flèche (hors de la grille, couverts par les sondes du pilote
automatique). Les
sculptures sont plus simples que sur la perspective. Les pièces sont un peu plus grandes que sur les vues intérieures (il
faut 2 blocs de hauteur sous plafond et des passages de 1 bloc pour marcher).
