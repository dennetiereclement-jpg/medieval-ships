# Forge divine — points de calage (structure A -> décor B)

Repère du brief : blocs, origine = centre du bloc d'ancrage, y = 0 dessus du sol, +z = face avant, +x = droite vue de face.

## Inchangés (conformes au brief)
- Plateforme : dessus à y = 0.5 (deux marches de 0.25 : x ∈ [-6.5, 6.5], z ∈ [-3.0, 3.0] puis x ∈ [-6.2, 6.2], z ∈ [-2.75, 2.7]).
- Dessus du corps central (base du socle de la statue) : y = 6.5, surface pleine sur x ∈ [-4.1, 4.1], z ∈ [-2.3, 0.7]
  (donc x ∈ [-1, 1], z ∈ [-1.2, 0.2] est bien libre et porteur).
- Potences hautes : dessous des bras horizontaux à y = 8.4, bras centrés z = 0.6 (z ∈ [0.3, 0.9]),
  points d'accroche sous le bras à x = ±5.6 (bannières) et x = ±3.6 (lanternes), y = 8.4.
  Au-dessus des bras : blocs en gradins pierre/or jusqu'à y ≈ 9.45, vers l'intérieur jusqu'à |x| = 2.6 (ne pas y mettre d'ailes).
- Établi GAUCHE (tableau de plans + râtelier) : dessus y = 1.0, x ∈ [-5.6, -3.6] (centre -4.6), z ∈ [0.6, 2.0].
- Socle de la presse : dessus y = 0.9, centré x = +5.2, z = 1.3 (x ∈ [4.35, 6.05], z ∈ [0.55, 2.05]), pierre noire.

## DÉPLACÉ (conflit du brief : l'établi droit x=+4.6 z∈[0.6,2.0] chevauchait le socle de la presse x=+5.2 z=1.3)
- Établi DROIT (cristal doré + outils) : comme sur l'image, il est DERRIÈRE, contre la façade, à gauche de la presse :
  dessus y = 1.0, x ∈ [1.95, 3.95] (centre x = +2.95), z ∈ [0.3, 1.2] (centre z = 0.75).
  => translation pour B : (-1.65, 0, -0.55) par rapport à l'ancien centre (4.6, 1.0, 1.3).
  Cristal suggéré vers x = +3.45, outils vers x = +2.45.
- Établi ARRIÈRE GAUCHE en plus (outils au mur sur l'image) : dessus y = 1.0, x ∈ [-3.5, -1.95], z ∈ [0.3, 1.2].
  Le mur derrière les établis arrière est à z = 0.25 (râteliers d'outils de B : z ≥ 0.27, y ∈ [1.0, 2.8]).

## Points d'accroche supplémentaires (facultatifs pour B)
- Lanternes latérales basses : bloc de pierre (siège) dessus y = 1.2 en x = ±5.6, z ∈ [-0.6, 0.2] (centre z = -0.2).
- Crochets sous les tuyaux latéraux (chaîne vers ces lanternes) : (±5.6, 3.3, -0.2).
- Façade supérieure (fond des engrenages) : z = 0.30 ; poutre haute de pierre y ∈ [6.0, 6.5], avant à z = 0.7.

## Audit partagé
`tools/forge/forge_audit.py` (écrit par A) : `python3 tools/forge/forge_audit.py forge_divine` ou
`python3 tools/forge/forge_audit.py forge_divine_deco`. Contrôle faces coplanaires/parallèles < 1/64 (deux sens),
cubes < 1/64, texels alpha < 255 sur les faces pleines (seuls `cut_*` / `glow_cut_*` exemptés), trous (vues ortho
face / dos / 3/4), chaque image de flipbook (`*_f<k>`) avec la structure et les `craft_*`, `gear_*` à 0° et 45°.
Option `--with forge_divine` pour contrôler aussi le décor CONTRE la structure (paires entre les deux modèles).
