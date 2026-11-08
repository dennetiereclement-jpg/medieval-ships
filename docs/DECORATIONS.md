# Décorations de rue (un bloc = une décoration)

Huit décorations médiévales pour les rues, places, marchés, ports et fêtes de village (1.20.0), et le
[pieu défensif](#pieu-défensif-1240) (1.24.0), le seul accessoire qui blesse (les mobs hostiles qui touchent sa pointe). **Chaque décoration
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

## Pieu défensif (1.24.0)

`medievalships:pieu_defensif` (« Pieu défensif », *Defensive Stake*), neuvième objet de l'onglet **Décorations** :
**un seul** pieu taillé planté dans le sol, jamais une barricade (aucun lien entre les pieux). Un gros tronc brun
sombre usé (environ 0,6 bloc de section) incliné à 40°, son pied enfoncé dans un petit anneau de mottes de terre
retournée avec quelques pierres grises (dans le modèle : aucun bloc de terre posé), une épaisse **bande de fer** à gros
boulons carrés là où commence la pointe, un **tissu rouge déchiré** noué autour du tronc juste sous la bande avec trois
pans effilochés qui pendent, et une longue **pointe très acérée en bois clair** (sections étagées qui s'affinent, taches
rouge sombre près de la bande). Environ 3,2 blocs de long (2,85 hors du sol), la pointe à environ 1,85 bloc de haut :
un mob qui marche vers le pieu rencontre la pointe à hauteur du corps. 71 cubes (le détail — boulons, mottes, pierres,
herbe, pans de tissu — masqué au-delà de 32 blocs), son propre petit atlas `textures/entity/pieu_defensif.png`
(64 × 64), générateur `tools/deco/generate_pieu_defensif.py`.

**Pose et orientation** : `/give @p medievalships:pieu_defensif`, puis clic droit au sol. La **pointe part à l'opposé
du joueur** qui le pose (dans la direction où il regarde) : on se tient à l'intérieur du camp et on plante les pieux
vers l'extérieur. L'emprise fait **un bloc de large** : on peut planter une rangée de pieux côte à côte, un bloc
d'écart (ou collés). `/deco place pieu_defensif ~ ~ ~ north` (la pointe part alors vers le sud), `/deco remove`,
`/tent remove` ; noms courts acceptés par les commandes : `pieu`, `stake`. Casser le bloc d'ancrage (au pied) rend
l'objet. Le pieu ne bouge jamais.

**Collisions** : trois petites boîtes en escalier le long du tronc (du sol à la bande de fer ; la première trop haute
pour qu'on monte dessus d'un pas) : joueurs et mobs s'y cognent. La pointe elle-même n'a pas de collision.

**Dégâts** (seul accessoire du mod qui « tick », et seulement sur le serveur) : le JSON du pieu a un champ
`"hazard": {"box": [...], "damage": 4.0, "knockback": 0.4, "cooldown": 20}` — la boîte est le **dernier bloc de la
pointe** (un peu élargi), en coordonnées du modèle, tournée avec l'orientation comme les boîtes de collision. Seuls les
blocs dont le type a un `hazard` reçoivent un *ticker* serveur (toutes les autres tentes et décorations restent sans
ticker). Tous les 5 ticks (décalés selon la position, pour qu'une rangée de pieux ne travaille pas au même tick), le
pieu demande au monde les entités vivantes dans cette petite boîte (pas de recherche sur une grande zone) et :

- blesse chaque **mob hostile** vivant (`Monster` : zombies, squelettes, creepers, araignées…) qui touche la pointe :
  dégâts du type `medievalships:stake` (« %1$s s'est empalé sur un pieu » / « %1$s was impaled on a stake ») et petit
  recul **vers l'extérieur, dans l'axe de la pointe** — seulement si le coup porte, comme en vanilla (pas de recul
  pendant l'invulnérabilité qui suit un coup plus fort, contre un mob invulnérable ou un bouclier qui pare tout) ;
- pas deux fois de suite : un délai par entité (`cooldownTicks`, 20 ticks = 1 s ; mémoire passagère dans l'entité de
  bloc, nettoyée, jamais sauvegardée) ;
- **épargne** les joueurs par défaut (réglage `damagePlayers` ; jamais en créatif ni en spectateur), et **toujours** les
  animaux, villageois, PNJ (les entités Easy NPC ne sont pas des `Monster`).

**Réglages serveur** (`config/medievalships.json`, section `"server"`), valeurs par défaut :

```json
"stake": {"damage": 4.0, "knockback": 0.4, "cooldownTicks": 20, "damagePlayers": false}
```

`damage` en demi-cœurs (0 à 100), `knockback` = force du recul vanilla (0 à 4 ; 0,4 = un coup d'épée), `cooldownTicks`
(1 à 1200), `damagePlayers` (les joueurs en survie / aventure aussi). Les valeurs hors bornes sont ramenées dans les
bornes. Ces réglages valent pour **tous** les pieux du serveur : ils remplacent les valeurs du JSON du modèle (qui sont
les mêmes valeurs par défaut). Côté code : `ConfigManager.server().stake` (`StakeSettings`), modifiable à chaud (le test
en jeu s'en sert).

**Coût** : un pieu posé ne fait rien d'autre qu'une requête d'entités sur une boîte d'environ 0,7 × 1 × 1,1 bloc tous les
5 ticks (et rien du tout côté client, en dehors du rendu de ses 71 cubes) ; des dizaines de pieux restent négligeables.
Sûr sur serveur dédié (aucune classe client sur ce chemin).

## Tests

- JUnit `StakeTest` (1.24.0) : le JSON du pieu se charge (neuvième décoration, noms, genre « posé », atlas 64 × 64),
  modèle statique léger avec l'os `detail`, une emprise d'un bloc de large, la pointe vers l'arrière, des boîtes en
  escalier le long du tronc et rien sur la pointe, la boîte de dégâts au bout de la pointe seulement (loin du pied,
  au-dessus du sol), sa rotation avec l'orientation (et sa direction vers l'extérieur), la lecture du champ `hazard`
  (bornes, valeurs par défaut), les réglages `stake` (défauts, lecture, bornes, ancien fichier, `null`), le type de dégâts
  et les messages de mort.
- En jeu `StakeGameTest` (plateforme x 1300 z 80) : pieu posé par `/deco place`, bloc / orientation / entité de bloc,
  un ticker serveur pour lui et aucun pour une autre décoration ou une tente, le tronc collisionne, la place de la
  pointe est libre ; un zombie (NoAI, casque contre le soleil) mis à la pointe est blessé en moins de 10 ticks et
  repoussé vers l'extérieur, pas blessé de nouveau avant le délai, de nouveau après ; un zombie au pied (collé à la face
  avant de la première boîte du tronc), un contre le flanc du tronc à mi-longueur et un villageois à la pointe ne le
  sont jamais ; le joueur de test en survie (sa Résistance V, qui annulerait tout dégât, retirée le temps de l'essai puis
  rendue) à la pointe n'est ni blessé ni touché par le pieu par défaut, l'est avec `damagePlayers = true` (posé par
  l'API, puis rétabli) ; trois pieux côte à côte à un bloc d'écart
  se posent tous ; captures ; un pieu cassé rend son objet.
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
