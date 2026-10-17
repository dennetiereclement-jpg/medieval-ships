# Modèles 3D, textures et animations

Le mod contient trois navires, chacun avec son propre fichier Blockbench, ses textures et ses
animations : la **galère médiévale**, le **grand galion** et le **grand vaisseau de guerre**.
Le moteur de rendu est commun.

# Galère médiévale

![Aperçu](preview.png)

## Fichiers

| Fichier | Rôle |
|---|---|
| `blockbench/galley.bbmodel` | Modèle éditable dans Blockbench (format *Generic Model / free*, texture intégrée, 6 animations). |
| `src/main/resources/assets/medievalships/models/entity/galley.bbmodel` | Copie chargée par le mod. |
| `src/main/resources/assets/medievalships/textures/entity/galley.png` | Texture 256 × 256. |
| `tools/generate_galley.py` | Générateur du modèle, de la texture et des animations. |
| `tools/preview.py` | Rendu logiciel des 6 vues (`docs/preview.png`), même logique que le mod. |

## Décomposition de l'image de référence

| Élément | Réalisation |
|---|---|
| Coque brune allongée, proue et poupe relevées | 15 tronçons × 2 bords × 5 bordages inclinés qui suivent un profil arrondi (largeur, quille et tonture calculées), + lisse, quille, étrave et étambot courbes |
| Bordures supérieures en bois clair | bordage supérieur clair + lisse (« rail ») plus claire |
| Bande rouge foncé | un bordage rouge sur toute la longueur, qui suit la tonture |
| Pont ouvert | pont principal + plates-formes surélevées à la poupe et à la proue |
| Mât central, voile triangulaire beige, cordages, drapeau rouge | mât de 13 blocs, antenne latine inclinée, voile triangulaire (un seul plan texturé avec transparence), 10 cordages, flamme rouge animée |
| 8 rames par côté | 16 os indépendants, pale élargie |
| Cabine de poupe, toit en tissu rouge, poste de pilotage, barrières | 4 poteaux, toit rouge en bâtière avec lambrequins festonnés, barrière à balustres avec passage, tabouret du barreur, deux avirons de gouverne |
| Proue décorée, petit espace surélevé | figure de proue, plate-forme avant |
| Lanternes (vues avant/arrière), longue flamme rouge de poupe | 4 lanternes lumineuses, flamme en 3 segments animés |

Dimensions : coque de 20 blocs (21,8 avec étrave et étambot), 5,1 de large, 2,8 à 3,8 de haut
de la quille au bastingage, 14,6 blocs du niveau de l'eau au sommet du drapeau.

Optimisation : 374 cubes, aucun bloc de « remplissage » ; les planches sont dans la texture
(densité 16 pixels par bloc comme Minecraft), pas modélisées une à une.

## Modifier le modèle dans Blockbench

1. Ouvrir `blockbench/galley.bbmodel` (Blockbench 4.10 ou plus récent).
2. Modifier formes, UV, texture ou animations.
3. *Fichier → Enregistrer* puis copier le fichier dans un pack de ressources :
   `assets/medievalships/models/entity/galley.bbmodel` (et la texture dans
   `assets/medievalships/textures/entity/galley.png`).
4. En jeu, **F3 + T** recharge le modèle.

Règles à respecter :

* Les **noms des groupes** utilisés par les animations doivent être conservés :
  `oar_l1`…`oar_l8`, `oar_r1`…`oar_r8`, `sail`, `yard`, `rudder_p`, `rudder_s`, `flag`,
  `flag_tip`, `streamer_1`…`streamer_3`.
* Les **noms des animations** sont lus par le mod : `row`, `sail_wind`, `sail_furl`, `steer`,
  `flag_wave`, `streamer_wave`.
* Les cubes dont le nom commence par `glow` sont rendus pleinement éclairés (lanternes).
* Seuls les cubes sont pris en charge (pas les « mesh »), les valeurs d'animation doivent être
  des nombres (pas d'expressions Molang).
* La proue regarde le **nord** de Blockbench (−Z) ; le niveau de l'eau est à Y = 0.

**Important** : les collisions du pont ne viennent pas du modèle mais de la forme de coque
définie dans `core/HullProfile.java` (identique à `tools/hull_profile.py`). Si vous changez
beaucoup la largeur ou la hauteur du pont, adaptez aussi ces deux fichiers.

## Animations

| Animation | Utilisation en jeu |
|---|---|
| `row` (2 s, boucle) | cycle d'aviron : attaque, propulsion, dégagement, retour. Sa vitesse suit la vitesse du navire ; quand le navire s'arrête, les rames ralentissent puis reviennent progressivement au repos. |
| `sail_wind` (3 s, boucle) | légère ondulation de la voile sous le vent. |
| `sail_furl` (1 s) | voile carguée le long de la vergue : jouée quand le navire est à l'arrêt depuis 5 s (option `furlSailWhenStopped`), déroulée au départ. |
| `steer` (2 s) | t = 0 : barre à bâbord, t = 1 : barre au centre, t = 2 : barre à tribord ; suit la barre, qui revient progressivement au centre. |
| `flag_wave`, `streamer_wave` | drapeau et flamme de poupe au vent. |

Le roulis, le tangage et la gîte dans les virages sont ajoutés par le moteur de rendu.

Toutes les animations sont pilotées par l'état synchronisé (vitesse, barre, voile) : tous les
joueurs du serveur voient les mêmes mouvements.

## Régénérer le modèle

```
python3 tools/generate_galley.py   # modèle + texture
python3 tools/preview.py           # aperçu docs/preview.png
```
(Python 3 avec `numpy` et `Pillow`). Attention : la régénération écrase les modifications
faites à la main dans Blockbench.

# Grand galion

![Aperçu du galion](preview_galleon.png)
![Détails : poupe et balcon, pont, proue, gaillard d'arrière et barre](preview_galleon_details.png)

## Fichiers

| Fichier | Rôle |
|---|---|
| `blockbench/galleon.bbmodel` | Modèle éditable dans Blockbench (2 textures intégrées, 4 animations). |
| `src/main/resources/assets/medievalships/models/entity/galleon.bbmodel` | Copie chargée par le mod. |
| `textures/entity/galleon.png` | Texture 512 × 512 (coque, châteaux, toit, voiles…). |
| `textures/entity/galleon_flag.png` | **Texture des drapeaux** (64 × 64) : emblème remplaçable. |
| `textures/item/galleon.png` | Icône de l'objet *Grand galion*. |
| `tools/galleon_shape.py` | Forme de coque et plan du navire, identiques au code Java des collisions. |
| `tools/generate_galleon.py`, `tools/galleon_texture.py` | Générateurs du modèle, des textures et des animations. |

## Ce qui est modélisé

| Élément | Réalisation |
|---|---|
| Coque arrondie et lisse (pas en escalier) | 28 tronçons × 2 bords × 7 bordages **inclinés** qui suivent des sections arrondies (quille, bouchain, flanc, léger rentré en haut) ; œuvres vives sombres, bois naturel, deux préceintes noires, virure rouge des sabords, **frise peinte** (losanges rouges et or sur fond bleu) et moulure dorée sous le plat-bord |
| Dimensions | coque 35 blocs (≈ 43 avec le beaupré et le balcon), 9 de large, ≈ 6,4 de la quille au haut des châteaux, ≈ 28 de la quille au sommet du grand mât |
| Ponts | pont principal, **gaillard d'avant** (+2 blocs), **gaillard d'arrière** (+2,6) au-dessus de la grande cabine, escaliers des deux bords, barrières à balustres |
| Château arrière | murs rouges, rangée de **pavois héraldiques** (boucliers) le long des gaillards, **bouteilles** (galeries de quart fermées) aux deux angles avec fenêtres cintrées éclairées, tableau arrière plat avec fenêtres de galerie et **grandes armes** (l'emblème du pavillon dans un cadre doré couronné), **balcon accessible**, corniche dorée, 3 grandes lanternes |
| Cabine | **grande cabine accessible** sous le gaillard d'arrière (porte dans la cloison, chaises = places assises, lanternes, coffre, poutres) ; **dunette** au toit de tuiles rouges (décorative, fermée) avec pilastres dorés, fenêtres cintrées éclairées et épis de faîtage |
| Gouvernail et barre | roue de barre sur piédestal (os `helm_wheel`) et gouvernail sur le tableau (os `rudder`) |
| Mâture | 3 mâts (misaine, grand mât en deux parties avec hunes, artimon) + beaupré avec **civadière**, vergues avec voile carguée en rouleau, porte-haubans et caps-de-mouton sur la coque |
| Voiles | voiles carrées **gonflées et courbées** (chaque voile = 9 bandes inclinées qui se raccordent exactement et suivent le ventre de la toile ; carguées, les voiles disparaissent dans leur rouleau sur la vergue ; texture continue avec croix rouge sur les basses voiles, garcettes de ris et toile légèrement patinée), voile latine d'artimon, **2 focs** triangulaires |
| Cordages | haubans avec enfléchures, étais, bras, écoutes, sous-barbe (≈ 60 cordages) |
| Drapeaux | pavillons en tête de mât, flamme à deux couleurs au grand mât, grand pavillon de poupe — tous sur la texture `galleon_flag.png` |
| Sabords | 12 sabords décoratifs (6 par bord) avec mantelets ouverts : os `gunport_l1`…`gunport_l6`, `gunport_r1`…`gunport_r6` ; os vides `cannon_l1`…`cannon_r6` à l'emplacement des futurs canons |
| Proue | éperon rouge et doré, figure de proue dorée, ancres, écubiers, lanterne de proue |

Optimisation : 1289 cubes (≈ 6700 faces), aucune géométrie cachée inutile ; 56 os.

## Changer l'emblème des drapeaux

Remplacez `assets/medievalships/textures/entity/galleon_flag.png` dans un pack de ressources
(même taille, 64 × 64) :

* zone `0,0 → 64,40` : le pavillon (fleur de lys dorée sur fond bleu par défaut) ;
* zone `0,40 → 64,48` : la flamme du grand mât.

L'emblème apparaît aussi sur les grandes armes du tableau arrière. Aucune modification du modèle n'est nécessaire, **F3 + T** recharge la texture.

## Animations du galion

| Animation | Utilisation en jeu |
|---|---|
| `sail_wind` (3,6 s, boucle) | le ventre des voiles « respire » et les voiles ondulent ; d'autant plus que la voilure est établie. |
| `sail_furl` (1 s) | voiles carguées sur leurs vergues (focs et latine ramassés) à l'arrêt, déployées au départ. |
| `steer` (2 s) | roue de barre (± 150°) et gouvernail (± 30°), comme pour la galère (0 = bâbord, 1 = centre, 2 = tribord). |
| `flag_wave` (1,2 s, boucle) | les 4 drapeaux flottent (deux segments chacun). |

Le roulis visuel est plus lent et plus faible que celui de la galère (navire lourd), et la gîte
dans les virages est calculée par le moteur de rendu.

## Collisions du galion

Comme pour la galère, les collisions ne viennent pas du modèle : elles sont définies dans
`core/Ships.java` (`Ships.GALLEON`, classe `GalleonLayout`) et reprises par
`tools/galleon_shape.py`. Volumes : coque pleine sous les ponts, murailles, gaillard d'avant,
plancher du gaillard d'arrière, cloison de cabine avec sa porte, tableau arrière avec la porte
du balcon, balcon et sa balustrade, dunette et son toit, escaliers, barrières, 3 mâts.
Un test (`GalleonTest`) vérifie que les deux fichiers donnent les mêmes valeurs.

## Régénérer le galion

```
python3 tools/generate_galleon.py
python3 tools/preview.py blockbench/galleon.bbmodel - docs/preview_galleon.png --scale=1.75
```

# Grand vaisseau de guerre

![Aperçu du vaisseau](preview_warship.png)
![Détails : poupe, pont et canons, proue, flanc](preview_warship_details.png)

## Fichiers

| Fichier | Rôle |
|---|---|
| `blockbench/warship.bbmodel` | Modèle éditable (2 textures intégrées, 4 animations). |
| `models/entity/warship.bbmodel` | Copie chargée par le mod. |
| `textures/entity/warship.png` | Texture 512 × 512. |
| `textures/entity/warship_flag.png` | **Drapeaux** (64 × 64, fleur de lys bleue sur fond blanc) : emblème remplaçable, aussi affiché sur les armes de la poupe. |
| `textures/item/warship.png` | Icône de l'objet. |
| `tools/warship_shape.py` | Forme et plan, identiques au code Java des collisions (test `WarshipTest`). |
| `tools/generate_warship.py`, `tools/warship_texture.py` | Générateurs (réutilisent les outils du galion). |

## Ce qui est modélisé (d'après l'image de référence)

| Élément | Réalisation |
|---|---|
| Coque | 29 tronçons × 2 bords × 10 bordages **inclinés** sur des sections arrondies : œuvres vives **blanches**, bandes **noires** et **ocre** alternées aux rangées de sabords, haut de coque brun sombre, trois préceintes noires, plat-bord doré, léger rentré de la muraille |
| Dimensions | coque 55 blocs, ≈ 67 avec beaupré, bout-dehors et galeries ; 13 de large ; 12 blocs de la quille au couronnement ; 42 jusqu'au sommet du grand mât |
| Ponts | pont principal (canons sur affûts), gaillard d'avant, **gaillard d'arrière** au-dessus de la grande cabine, **dunette** au-dessus de la chambre du conseil ; 3 escaliers doubles, barrières à balustres |
| Canons | **58** : 12 + 11 par bord dans deux rangées de sabords de la coque, 6 par bord sur affûts au pont principal (les 12 affûts sont des sièges) ; un os par canon `cannon_l1`…`cannon_l29`, `cannon_r1`…`cannon_r29` |
| Poupe | tableau très haut, trois étages de fenêtres éclairées avec pilastres, corniches et frises dorées, **deux galeries** à balustres, bouteilles d'angle sur deux étages, grandes armes couronnées, 3 grandes lanternes, pavillon de poupe |
| Grande cabine | accessible par la porte de la cloison : chaises (places assises), lanternes, coffres, baux |
| Mâture | 3 mâts en trois parties (bas-mât, mât de hune, perroquet) avec hunes et barres de flèche ; **3 voiles carrées par mât** à l'avant et au centre, hunier et latine à l'artimon ; beaupré, bout-dehors, civadière, **3 focs** |
| Gréement | haubans avec enfléchures et caps-de-mouton sur porte-haubans, galhaubans, étais, bras, écoutes, sous-barbe |
| Proue | éperon, figure de proue dorée, lisses de poulaine, bossoirs avec ancres, écubiers, lanterne |

Optimisation : 1907 cubes (≈ 11 000 faces), ce qui reste raisonnable pour un navire de cette
taille (le rendu est calculé par le client, sans aucun coût serveur) ; le gréement est simplifié
(cordages droits), les voiles sont des bandes qui se raccordent exactement.

## Animations du vaisseau

Les mêmes que le galion : `sail_wind`, `sail_furl` (voiles ramassées dans leur rouleau à l'arrêt),
`steer` (double roue de barre et gouvernail), `flag_wave`. En plus, le rendu ajoute un roulis et
un tangage plus lents et plus faibles (navire très lourd) et de l'**écume à la proue** et un léger
sillage, proportionnels à la vitesse (quelques particules vanilla par tick, seulement près des joueurs).

## Régénérer le vaisseau

```
python3 tools/generate_warship.py
python3 tools/preview.py blockbench/warship.bbmodel - docs/preview_warship.png --scale=2.7
```
