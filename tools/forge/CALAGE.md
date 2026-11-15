# Forge divine — points de calage (structure A -> décor B)

Repère du brief : blocs, origine = centre du bloc d'ancrage, y = 0 dessus du sol, +z = face avant, +x = droite vue de face.
Valeurs FINALES de la structure (`tools/forge/generate_forge_divine.py`).

## Inchangés (conformes au brief)
- Plateforme : dessus à y = 0.5 (deux marches de 0.25 : x ∈ [-6.5, 6.5], z ∈ [-3.0, 3.0] puis x ∈ [-6.2, 6.2], z ∈ [-2.75, 2.7]).
  Grille de lave (glow) x ∈ [-1.9, 1.9], z ∈ [1.98, 2.6], dessus y = 0.535, cadre de fer jusqu'à y = 0.56.
- Dessus du corps central (base du socle de la statue) : y = 6.5, surface pleine sur x ∈ [-4.2, 4.2], z ∈ [-2.3, 0.7]
  (x ∈ [-1, 1], z ∈ [-1.2, 0.2] est libre et porteur). Sur le dessus, déjà occupés par A : arceaux de cuivre
  x ∈ ±[1.25, 2.7], z ∈ [-1.85, -1.35], jusqu’à y = 7.47 (évents jusqu’à 7.7 en x = ±1.975) ; plaques d'or
  x ∈ ±[2.6, 3.8], z ∈ [-0.3, 0.75], y ≤ 6.56 ; tours des potences x ∈ ±[2.92, 4.47], z ∈ [-1.52, -0.28].
- Potences hautes : dessous des bras à y = 8.4, bras x ∈ ±[3.25, 6.05], z ∈ [0.3, 0.9] (centre z = 0.6), dessus or y = 8.84.
  Accroches sous le bras : x = ±5.6 (bannières) et x = ±3.6 (lanternes), y = 8.4, z = 0.6.
  Console de pierre sous le bras en x ∈ ±[3.78, 4.38], y ∈ [7.62, 8.42] : la lanterne en ±3.6 doit rester dans
  |x| ≤ 3.76 ; la bannière en ±5.6 a toute la place jusqu'à |x| = 6.05.
  Au-dessus : gradins pierre/or jusqu'à y = 9.52, vers l'intérieur jusqu'à |x| = 2.62 (ne pas y mettre d'ailes).
- Établi GAUCHE (tableau de plans + râtelier) : dessus y = 1.0, x ∈ [-5.6, -3.6] (centre -4.6), z ∈ [0.6, 2.0]
  (liseré or jusqu'à ±0.03 autour, sous y = 0.975).
- Socle de la presse : dessus y = 0.9, centré x = +5.2, z = 1.3 (x ∈ [4.35, 6.05], z ∈ [0.55, 2.05]), pierre noire,
  marche basse x ∈ [4.25, 6.15], z ∈ [0.45, 2.15], y ≤ 0.72.

## DÉPLACÉ (conflit du brief : l'établi droit x=+4.6 z∈[0.6,2.0] chevauchait le socle de la presse x=+5.2 z=1.3)
- Établi DROIT (cristal doré + outils) : comme sur l'image, DERRIÈRE, contre la façade, à gauche de la presse :
  dessus y = 1.0, x ∈ [2.1, 3.95] (centre x = +3.025), z ∈ [0.2, 1.2] (centre z = 0.7).
  => translation pour B : (-1.575, 0, -0.6) par rapport à l'ancien centre (4.6, 1.0, 1.3).
  Cristal suggéré vers x = +3.5, outils vers x = +2.5.
- Établi ARRIÈRE GAUCHE en plus (outils au mur sur l'image) : dessus y = 1.0, x ∈ [-3.5, -2.1], z ∈ [0.2, 1.2].
  Mur derrière les établis arrière à z = 0.25 (râteliers d'outils de B : z ≥ 0.27), libre pour y ∈ [1.0, 2.6]
  entre les montants de fer x ∈ [-2.14, -2.02] / [2.07, 2.19] et ±[3.96, 4.08] (traverse de bois à y ∈ [2.6, 2.7], z ≤ 0.3).

## Points d'accroche supplémentaires (facultatifs pour B)
- Lanternes latérales basses : sièges de pierre, dessus y = 1.2, x ∈ ±[5.25, 5.95], z ∈ [-0.3, 0.3] (centre z = 0).
- Crochets de fer sous les tuyaux latéraux (chaîne vers ces lanternes) : (±5.6, 3.36, 0.0).
- Tuyau vertical droit x ∈ [4.85, 5.15], z ∈ [-0.15, 0.15], de y = 0.5 à 3.95 (vanne vers y = 2.1) : à éviter.

## Poser un objet de B sur une surface de A
Une face de B posée exactement sur une face de A (y = 1.0, 0.9, 6.5…) est une paire coplanaire entre les deux
modèles : enfoncer de 1/32 (ex. pied à y = 1.0 - 1/32) ou laisser ≥ 1/64 d'écart.

## Audit partagé
`tools/forge/forge_audit.py` : `python3 tools/forge/forge_audit.py forge_divine` ou
`python3 tools/forge/forge_audit.py forge_divine_deco [--with forge_divine]`. Contrôle faces coplanaires/parallèles
< 1/64 (deux sens), cubes < 1/64, texels alpha < 255 sur les faces pleines (seuls `cut_*` / `glow_cut_*` exemptés),
trous (vues ortho face / dos / 3/4 ; parasite = trou d'épingle < 0.004 bloc² ou fente < 1/16), chaque image de
flipbook (`*_f<k>`) avec la structure et les `craft_*` (ou `idle_*`), `gear_*` à 0° et 45°. `--with forge_divine`
contrôle aussi le décor CONTRE la structure (paires entre les deux modèles). Structure : DEFECTS = 0.
