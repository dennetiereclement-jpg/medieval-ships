# Passerelles : réglages par navire

Complément de `docs/PASSERELLES.md` (le système : levier, règles de sécurité, messages, tests). Ce fichier décrit où
et comment la passerelle de chaque navire est posée. Les valeurs sont dans
`src/main/resources/assets/medievalships/gangplanks/<id>.json` et sont générées par `tools/gangplank/ships_g2.py`
(avec les modèles `models/entity/gangplank_<id>.bbmodel`) ; le trade_sloop et le dirigeable steampunk, navires de
référence du système, sont décrits dans `docs/PASSERELLES.md`.

Repère : celui du navire (`core/Gangplank.java`) : x vers bâbord, y vers le haut (0 = ligne de flottaison d'un navire),
z vers la proue, en blocs. Angles : positifs vers le bas.

## Règles de placement

* **Charnière** sur la face extérieure de la coque, au sommet du bastingage (ou du pavois de la grille intérieure
  pour les navires à pièces), sur une portion de flanc dégagée : entre les sabords, les rames, les haubans, les tambours
  de roue, les bancs, les écoutilles et les fenêtres.
* **Escalier intérieur** (`step`) : du pont jusqu'à la hauteur de la charnière, collé au bastingage, marches de
  0,45 au plus (elles n'existent que passerelle déployée). Les navires ouverts ont aussi un `rail_gap` : le
  bastingage cesse de bloquer au-dessus de la charnière sur la largeur de la passerelle.
* **Levier** sur le pont, à côté de l'escalier (jamais dessus), à moins de 4 blocs de la charnière.
* **Longueur** : de quoi atteindre un quai à un bloc au-dessus de l'eau (navires) dans les pentes permises, ou une
  plate-forme d'embarquement à environ 3,9 blocs sous le pont (grands dirigeables, `max_drop`).
* **Largeur** : 2 à 2,4 pour les navires à sabords serrés ou à rames, 3 pour les grands navires à pièces, 3 à 3,5
  pour les grands dirigeables.

## Navires équipés

| Navire | Côté | Charnière (x, y, z) | Largeur × longueur | Style | Escalier intérieur | Pentes | Dénivelé max | Levier (x, y, z) |
|---|---|---|---|---|---|---|---|---|
| galère (`galley`) | tribord | -2.48, 1.63, 3.20 | 2.0 × 3.5 | wood | 3 marches de 0.39 (pont 0.45 → 1.63) | -25° à 25° | 1.47 | -1.80, 0.45, 4.42 |
| grand galion (`galleon`) | tribord | -4.39, 2.22, -4.50 | 2.0 × 5.5 | dark_wood | 3 marches de 0.41 (pont 1.00 → 2.22) | -20° à 38° | 3.38 | -2.55, 1.00, -5.25 |
| vaisseau de guerre (`warship`) | tribord | -6.33, 5.83, -5.25 | 2.4 × 9.0 | dark_wood | 3 marches de 0.44 (pont 4.50 → 5.83) | -15° à 42° | 6.02 | -4.60, 4.50, -6.25 |
| galère médiévale (`medieval_galley`) | tribord | -2.60, 2.15, 1.80 | 2.0 × 4.0 | wood | 4 marches de 0.42 (pont 0.45 → 2.15) | -25° à 30° | 1.99 | -1.60, 0.45, 0.45 |
| vapeur à aubes (`steam_paddleboat`) | tribord | -3.60, 3.37, -6.70 | 2.0 × 5.5 | steel | 3 marches de 0.32 (pont 2.40 → 3.37) | -20° à 40° | 3.53 | -2.20, 2.40, -5.30 |
| voilier elfique (`elven_sailboat`) | tribord | -2.80, 1.94, -3.80 | 2.2 × 4.0 | elven | 3 marches de 0.45 (pont 0.60 → 1.94) | -25° à 35° | 2.29 | -1.05, 0.60, -2.55 |
| vieux corsaire (`old_corsair`) | tribord | -4.70, 6.00, 0.00 | 3.0 × 8.0 | worn | 4 marches de 0.38 (pont 4.50 → 6.00) | -15° à 42° | 5.35 | -3.50, 4.50, 1.95 |
| frégate bleue (`blue_frigate`) | tribord | -4.60, 7.55, 1.00 | 3.0 × 10.0 | dark_wood | 5 marches de 0.41 (pont 5.50 → 7.55) | -15° à 42° | 6.69 | -3.50, 5.50, 2.95 |
| dirigeable de cristal (`crystal_airship`) | tribord | -6.03, 1.13, -0.50 | 3.5 × 5.5 | crystal | 3 marches de 0.38 (pont 0.00 → 1.13) | -25° à 45° | 3.88 | -5.00, 0.00, -2.80 |
| léviathan du ciel (`sky_leviathan`) | tribord | -5.02, 1.14, -1.50 | 3.0 × 5.5 | dark_wood | 3 marches de 0.38 (pont 0.00 → 1.14) | -25° à 45° | 3.88 | -4.05, 0.00, 0.45 |
| jonque du dragon (`dragon_junk`) | tribord | -3.98, 1.14, 9.50 | 3.0 × 5.5 | jade | 3 marches de 0.38 (pont 0.00 → 1.14) | -25° à 45° | 3.88 | -3.10, 0.00, 7.20 |

## Remarques par navire

* **Galère** : huit rames par bord sous le bastingage ; la passerelle repose sur le bastingage et ses pentes sont
  limitées à 25° pour qu'elle passe au-dessus des rames (inclinées à 28°). Entre les bancs (z 1,6 et 4,8).
* **Grand galion** : entre les canons de pont de z −6 et −3, en arrière des haubans du grand mât et en avant de
  l'escalier du gaillard d'arrière.
* **Vaisseau de guerre** : entre les canons de pont de z −7 et −3,5 ; pont à 5,6 blocs au-dessus de l'eau, d'où les
  9 blocs de long.
* **Galère médiévale** : les boucliers couvrent tout le bastingage ; la passerelle se pose sur leurs bords (y 2,15),
  les sabords de nage (y 0,75) sont bien en dessous. Entre le mât et le banc de z 3,6.
* **Vapeur à aubes** : sur le garde-corps, en arrière du rouf et du tambour de roue, entre deux lanternes, à côté de
  la barbette du canon arrière.
* **Voilier elfique** : entre les écoutilles de z −2 et −5,5, en arrière des haubans.
* **Nautilus** (en surface seulement) : depuis le bord de la plate-forme (sol à 9,0), en avant de la rambarde et des
  volets du salon, en arrière de la timonerie ; la plate-forme est à 9 blocs au-dessus de l'eau : passerelle de
  12 blocs (pente jusqu'à 46°, la coque bombée reste dessous). Pas d'escalier : la plate-forme est de plain-pied.
  Rangée, elle se dresse haut au bord de la plate-forme.
* **Vieux corsaire** : planches usées, au milieu du pont entre les haubans des deux mâts.
* **Frégate bleue** : posée sur la lisse dorée du pavois (y 7,55), entre les haubans du grand mât et du mât de
  misaine, côté tribord (l'écoutille ouverte est à bâbord).
* **Dirigeable de cristal** : sur le pont principal entre les banquettes latérales (z −5..−4 et 3..4).
* **Léviathan du ciel** : sur le pont principal, en arrière des caisses, en avant de l'escalier du gaillard.
* **Jonque du dragon** : laque rouge et jade, sur le pont avant entre les deux ouvertures du pavois (z 6,75 et
  11,25), en arrière du mât incliné.

## Navires sans passerelle

* **Canot** (`rowboat`) : on y monte d'un clic, il n'a pas de pont où marcher.
* **Montgolfière** (`hot_air_balloon`) : une nacelle.
* **Esquif rustique** (`rustic_skiff`) : petit volant qui a déjà son propre escalier d'embarquement.

## Vérifications

* `GangplankSpecsTest` (JUnit) : chaque navire listé a sa spec et les exclus n'en ont pas ; valeurs plausibles
  (largeur, longueur, pentes, dénivelé atteignant un quai à un bloc au-dessus de l'eau) ; charnière sur le flanc au
  sommet du bastingage avec le passage libre au-dessus ; escalier partant du pont, dans un espace libre ; levier sur le
  pont, hors de l'escalier, à portée ; passerelle hors des parties solides du navire à tous les angles permis, pendant
  sa rotation et rangée ; modèle aux dimensions de la spec.
* Rendus de contrôle : `python3 tools/gangplank/ships_g2.py sheet <sortie.png>` (une ligne par navire : rangée,
  déployée à 20°, coupe le long de la quille, vue du flanc).

> Retirés à la demande du joueur (1.23.0) : `trade_sloop` (petit sloop) et `nautilus` n'ont pas de passerelle ; leurs
> fichiers ont été supprimés. Le test en jeu se fait avec la galère à quai et le dirigeable steampunk.
