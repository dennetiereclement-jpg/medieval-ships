# Décorations de rue (un bloc = une décoration)

Huit décorations médiévales pour les rues, places, marchés, ports et fêtes de village (1.20.0). **Chaque décoration
est UN seul bloc**, exactement comme les [tentes](TENTES.md) et les [charrettes](CHARRETTES.md) : on pose le bloc,
la décoration entière (poteaux, cordes, tissus, filet, lanternes…) est dessinée à partir de lui, tournée vers le
joueur qui la pose. Elles sont **statiques** : pas d'animation, pas d'IA, rien ne « tick ». Elles sont persistantes
(c'est un bloc : sauvegardé avec le monde) et légères (60 à 75 cubes pour les quatre premières, petits détails dans
la texture ; les plus petits éléments sont masqués au-delà de 32 blocs).

| id | nom | emprise (l × h × p, blocs) | cubes | boîtes de collision | lumière | générateur |
|----|-----|-----|-----|-----|-----|-----|
| `deco_guirlande` | Guirlande festive (Festive Bunting) | 5,2 × 3,4 × 0,7 | 60 | 2 (poteaux) | 12 | `tools/deco/generate_deco_guirlande.py` |
| `deco_etendoir` | Étendoir à linge (Clothesline) | 5,4 × 3,4 × 0,7 | 51 | 2 (poteaux) | 0 | `tools/deco/generate_deco_etendoir.py` |
| `deco_draperie` | Draperie rouge (Red Drapery) | 5,1 × 3,7 × 1,1 | 64 | 2 (poteaux) | 0 | `tools/deco/generate_deco_draperie.py` |
| `deco_filet` | Filet suspendu (Hanging Net) | 5,4 × 3,4 × 0,7 | 73 | 2 (poteaux) | 0 | `tools/deco/generate_deco_filet.py` |
| `deco_sechoir` | Séchoir à herbes (Herb Drying Rack) | voir le générateur | | poteaux, socles | 0 | `tools/deco/generate_deco_sechoir.py` |
| `deco_lanterne` | Lanterne suspendue (Hanging Lantern) | voir le générateur | | poteau | 15 | `tools/deco/generate_deco_lanterne.py` |
| `deco_banniere` | Bannière de la Couronne (Crown Banner) | voir le générateur | | poteau | 0 | `tools/deco/generate_deco_banniere.py` |
| `deco_ombrage` | Toiles d'ombrage (Shade Sails) | voir le générateur | | quatre poteaux | 0 | `tools/deco/generate_deco_ombrage.py` |

Les quatre dernières sont modélisées par une seconde branche (deco-2) ; tant qu'elle n'est pas fusionnée, leurs
fichiers sont des **copies provisoires** de la guirlande (même modèle, même icône ; la lanterne a déjà sa lumière 15).

- **Guirlande festive** : deux poteaux équarris (liens de corde en haut, bandes de fer rivetées au pied), une corde
  qui pend légèrement entre eux, six fanions de tissu aux bouts découpés en pointes (rouge, jaune, bleu, rouge, jaune,
  rouge) qui suivent la pente de la corde, une petite lanterne allumée sur une potence de fer contre chaque poteau.
- **Étendoir à linge** : deux poteaux (liens de corde en haut, grosses ligatures de corde au pied), une corde à linge
  avec des pinces de bois : un drap blanc, une tunique bleue à rayures claires, un tissu beige usé et troué, un tissu
  rouge brique ; les tissus tombent en plis verticaux, l'ourlet effiloché.
- **Draperie rouge** : deux grands poteaux (liens de corde en haut, bandes de fer au pied), une draperie rouge semée
  de points d'or en deux drapés superposés (bordure d'or dentelée), ses deux pans tombant le long des poteaux.
- **Filet suspendu** : deux poteaux (gros liens de corde, bandes de fer), une grosse corde nouée qui pend, un filet de
  pêche à mailles en losange accroché en poche profonde, trois flotteurs (blanc, rouge, bleu) pendus à des ficelles.

Objets : `medievalships:deco_guirlande`, `medievalships:deco_etendoir`, `medievalships:deco_draperie`,
`medievalships:deco_filet`, `medievalships:deco_sechoir`, `medievalships:deco_lanterne`, `medievalships:deco_banniere`,
`medievalships:deco_ombrage` — tous dans l'onglet créatif **Décorations**.

## Obtenir, poser, retirer

```
/give @p medievalships:deco_guirlande          (ou /deco give deco_guirlande [joueurs], /tent give ...)
/deco place deco_lanterne                       (à sa position, orientée selon son regard)
/deco place deco_filet ~ ~ ~5 north             (position et orientation : north, south, east, west)
/deco list                                      (les décorations chargées, les plus proches d'abord)
/deco remove nearest | /deco remove x y z       (/tent remove marche aussi)
```

`/deco` ne touche qu'aux décorations ; `/tent` accepte tous les accessoires (tentes, charrettes, décorations...).
Le code (`TentTypes.byId`) reconnaît aussi les noms courts : `guirlande`, `etendoir`, `draperie`, `filet`, `sechoir`,
`lanterne`, `banniere`, `ombrage`.

- **Poser à la main** : clic droit avec l'objet sur le sol ; la décoration fait face au joueur. Il faut la place
  (l'emprise du tableau, plantes et neige recouvertes) et un sol plein dessous (rue, place, quai), sinon un message
  explique ce qui gêne.
- **Retirer** : casser le bloc d'ancrage (au pied, au centre de l'emprise) rend l'objet ; ou `/deco remove`.

## Lumière

Le champ JSON `"light"` (0 à 15, 0 par défaut, borné) donne la **luminance du bloc d'ancrage** : c'est le moteur de
lumière vanilla qui éclaire la zone, comme une torche — rien n'est calculé à chaque tick. La lanterne suspendue vaut
15, la guirlande 12 (ses deux petites lanternes) ; les autres ne donnent pas de lumière.

La source de lumière est le **bloc d'ancrage, au pied de la décoration** (au centre entre les deux poteaux pour la
guirlande, au pied du poteau pour la lanterne), pas la lanterne dessinée elle-même : la lumière part donc du sol et
décroît d'un niveau par bloc (15 au pied, 13 deux blocs au-dessus). Les vitres des lanternes sont dessinées en pleine
lumière (cubes `glow`), elles brillent donc aussi la nuit.

## Collisions

Seuls les **poteaux** (et les socles de pierre) arrêtent les joueurs et les mobs : de fines boîtes de la section du
poteau. Les fanions, le linge, la draperie, le filet, les flotteurs, les voiles, les cordes et les lanternes n'ont
aucune collision : on passe librement entre les poteaux (vérifié par les tests).

## Générer / modifier

Tout vient de `tools/deco/decolib.py` (sur `tentlib` / `cartlib`), l'atlas partagé `textures/entity/decorations.png`
(512 × 512) et un générateur par décoration :

```
python3 tools/deco/generate_deco_guirlande.py      # modèle, JSON decorations/<id>.json, atlas, icône
python3 tools/deco/decolib.py                      # réécrit seulement l'atlas partagé (et liste ses régions)
```

Chaque générateur réécrit l'atlas **complet** : les régions de base de `decolib.py` (positions fixes) puis celles des
modules d'extension `tools/deco/atlas_*.py` (`REGIONS = [(nom, l, h, peintre), ...]`, triés par nom de fichier). Après
une fusion qui touche `decolib.py` ou un `atlas_*.py`, relancer `python3 tools/deco/decolib.py` pour que l'atlas du
dépôt corresponde aux peintres actuels.

Ajouter une décoration : un générateur (`dl.setup`, `dl.post`, `dl.sag_rope`, `dl.pennant` / `dl.clothes` /
`dl.swag` / `dl.net` / `dl.bundle` / `dl.hanging_lantern` / `dl.banner` / `dl.sail`, `dl.export(root, id, light=...)`),
une ligne dans `TentTypes.DECORATIONS`, les noms dans les fichiers de langue, blockstate / modèle d'objet (comme les
autres `deco_*`).

## Tests

- JUnit `DecorationTest` : les huit JSON se chargent dans l'ordre, groupe `decorations` entre les aires
  d'entraînement et le canon, emprises de 1 à 8 blocs de large et au plus 6 de haut au sol, seules de fines boîtes de
  poteaux collisionnent et toutes dans l'emprise, le passage entre deux poteaux est libre, lumière (12, 15, 0 sinon,
  bornage 0-15), modèles chargés sans animation avec un os `detail` et au plus 250 cubes, cubes `glow` quand il y a de
  la lumière, noms français / anglais et fichiers d'objet ; accords « posé / posée / posées ».
- En jeu `DecorationGameTest` (appelé par `ShipClientGameTest`, plateforme x 1300 z 40) : chaque décoration posée
  par commande, bloc / orientation / entité de bloc, boîtes enregistrées, un poteau collisionne, rien entre les
  poteaux, lumière du bloc d'ancrage (15 au pied de la lanterne, 13 deux blocs au-dessus), capture, retrait (plus de
  boîtes, plus de lumière).

Non testé : le rendu réel en jeu n'est vérifié que par les captures de la CI (pas de lancement local du client) ;
les quatre modèles de la branche deco-2 ne sont pas encore là (copies provisoires) ; le niveau de détail lointain
(os `detail`) n'est vérifié que par sa présence.
