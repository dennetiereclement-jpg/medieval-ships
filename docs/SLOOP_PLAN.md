# Le Petit voilier de commerce (`trade_sloop`) — analyse, plan et guide du joueur

Référence : `scratchpad/ref/trade_sloop_ref.png` (une seule vue, trois-quarts avant bâbord, caméra basse, le
voilier remplit l'image). Un petit sloop marchand trapu : coque de bois brun à **virures bleues**, proue relevée
avec un long beaupré, un mât unique portant une **grand-voile à corne** et un **grand foc** beige clair, haubans à
enfléchures, pont de bois avec caisses et tonneaux, petite plate-forme arrière avec la barre franche, lanternes.

Comparaison référence / rendu du modèle : [`preview_trade_sloop.png`](preview_trade_sloop.png).

## 1. Mesures sur la référence

Image de 768 × 512 px. La coque visible va de l'étrave (x ≈ 245) au tableau (x ≈ 610), raccourcie par la
perspective (≈ 0,85) : longueur réelle ≈ 430 px. Échelle retenue : **15 blocs de coque ≈ 28,7 px/bloc**.

| Élément | Pixels | Blocs (modèle) |
|---|---|---|
| Coque, étrave → tableau | 245 → 610 (raccourci) | **15,0** (z −7,5 → +7,5 ; posts à ±8,2) |
| Beaupré, tête d'étrave → pointe | (245, 330) → (95, 262) | **5,3**, relevé de 16° (z +6,9 → +12,2, y 3,45 → 4,9) |
| Longueur hors tout | | **20,4** (étambot → pointe du beaupré) |
| Franc-bord au milieu (lisse → flottaison) | y 355 → 418 ≈ 63 px ×1,2 (vue oblique) | **2,6** (lisse à y 2,1, eau à −0,5) |
| Bande bleue | de 33 % à 75 % du franc-bord | y **0,3 → 1,3** (deux virures), couples bruns tous les 1,3 blocs |
| Relevé de la proue | lisse +30 px à l'étrave | **+1,4** à l'étrave, +0,25 à l'arrière |
| Mât, pont → pomme | y 330 → 15 ≈ 315 px | **13,4 au-dessus du pont** (pomme à y 14,0), barres de flèche à 11,0 |
| Grand-voile : envergure (bôme) / hauteur | x 390 → 640 / y 120 → 300 | bôme z +1,2 → **−8,8** (dépasse le tableau), têtière 10,2, pic (11,6, −6,3), pied à 3,1 |
| Foc : point de drisse / amure / écoute | (370, 125) / (100, 265) / (330, 300) | (10,6 ; +1,5) / pointe du beaupré / (3,2 ; +2,2) |
| Largeur (vue avant, estimée) | ≈ 0,3 × longueur | **4,6** (demi-largeur 2,3) |

Vue de dessus déduite : entrée pleine et arrondie (`fore` 8,1 / 2,0 / 0,8), arrière presque rond et plus plein
(`aft` 8,0 / 3,2 / 0,6) pour loger la plate-forme arrière. Tirant d'eau faible : quille à −1,5 (1,0 sous l'eau).

## 2. Structure

- **Coque** : 25 couples, 11 virures par bord (fond goudronné sombre → une virure brune → deux virures **bleues** →
  préceinte miel) ; lisse de plat-bord en bois clair avec un boudin ; couples bruns saillants qui traversent la
  bande bleue ; quille, étrave courbe montant jusqu'à une **tête d'étrave** carrée (apôtres de part et d'autre) qui
  porte le beaupré ; étambot ; gouvernail suspendu avec sa mèche traversant la voûte jusqu'à la **barre franche**.
- **Ponts** : pont principal à y 0,6 (z −3,6 → +6,9), **plate-forme arrière** à y 1,1 (une marche de 0,5, z < −3,6)
  avec une lisse basse à balustres ; panneau de cale à claire-voie au milieu ; bittes et guindeau à l'avant.
- **Gréement** : mât (bas-mât ⌀ 0,42, mât de flèche ⌀ 0,26) avec barres de flèche, cercles de fer, pomme peinte
  en clair ; bôme et corne à mâchoires, cercles de mât ; beaupré conique à cercle de fer ; étai et draille de foc,
  sous-barbe, 2 haubans par bord avec cap de mouton et cadènes et **7 enfléchures**, galhaubans, drisse de pic,
  balancine, écoute de grand-voile, écoutes de foc, une glène de drisse qui se balance.
- **Voiles** : grand-voile à corne (grille 8 × 9 cellules sur une surface bombée, chute légèrement creuse, ralingues,
  renforts aux coins, bande de ris) ; foc (triangle 6 × 9, chute et bordure bombées). Beige clair, coutures simples.
- **Chargement** : 5 caisses (deux + une pour s'asseoir sur la plate-forme arrière, deux à tribord devant), 3 tonneaux,
  un sac, un petit coffre (décoratif), glènes de cordage. Les caisses et tonneaux sont **solides** (on bute dessus,
  on peut monter dessus) — pas de coffre de stockage fonctionnel dans le mod.
- **Lanternes** : deux sur des bossoirs de fer aux hanches, une sous la tête d'étrave (verre allumé, balancement).
- Textures : atlas 512 × 512 propre (`tools/sloop_texture.py`), 1 texture ; ≈ 1 500 cubes.

## 3. Parties mobiles et animations

| Animation | Os | Effet |
|---|---|---|
| `sail_wind` | `sail_main`, `sail_jib` | léger gonflement / respiration du tissu |
| `sail_furl` | `sail_main`, `sail_jib` | la grand-voile s'affale sur la bôme, le foc se rassemble à son amure (voiles ferlées à l'arrêt) |
| `steer` | `rudder` | safran **et barre franche** pivotent avec la barre (la barre part du côté opposé, comme en vrai) |
| `lantern_sway` | `lantern_0`, `lantern_1`, `lantern_bow` | balancement des lanternes |
| `rope_sway` | `rope_slack_0` | la glène pendue au mât oscille |

## 4. Places et pilotage

- **Pilote** : debout à la barre franche sur la plate-forme arrière (z −5,0), descend devant la barre.
- **Passagers** : banc bâbord et banc tribord au milieu (x ±1,55, z −2), banc de proue (z +4,8), caisse à tribord
  de la plate-forme arrière (x 1,0, z −6,3). **5 places**.
- Physique (`SloopLayout.config`) : petit bateau chargé — accélération progressive (0,65), vitesses 2,4 / 5,2 / 7,8,
  virage souple avec un peu d'inertie, roulis plus marqué que les grands navires (1,15), voiles ferlées à l'arrêt.
  Pilote automatique maritime : mêmes commandes `/ship route …` que les autres bateaux (rayon de passage 6, arrêt 1,8).
- Effets : sillage et éclaboussures d'étrave génériques (`bowWake`), sons génériques du mod.

## 5. Contraintes et choix

- Le pont est ouvert (pas de grille intérieure) : on marche librement sur les deux ponts pendant la navigation, on
  est transporté avec le bateau ; la bôme passe 2 blocs au-dessus de la plate-forme arrière.
- La bande bleue suit la tonture (elle monte vers la proue comme sur l'image).
- L'image n'a qu'une vue : la largeur, le dessin de l'arrière et le plan de pont sont déduits (arrière rond, pas de
  tableau plat).
- Pas de drapeau (la référence n'en montre pas ; la pomme du mât est peinte en clair).
- Test en jeu `SloopGameTest` (≈ 40 s) : flottaison, voiles ferlées / établies, 4 vues de référence, marche sur
  les deux ponts, navigation à la barre (barre, voiles, accélération, virage), descente du pilote, objet.
