# Modèle 3D, textures et animations

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
