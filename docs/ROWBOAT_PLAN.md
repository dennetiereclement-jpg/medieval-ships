# La Petite Barque (`rowboat`) — analyse, plan et guide du joueur

Référence : le quart bas-droit de la planche « quatre petits véhicules » (`rowboat_ref.png`, une seule vue en
perspective, par trois quarts avant-bâbord, légèrement plongeante). Une petite barque de pêche en bois brun
naturel, à clins, à deux pointes, qui flotte sur l'eau devant un quai ; une rame posée dans ses tolets, un
cordage d'amarrage tourné sur le montant d'étrave, pendant à l'extérieur et lové sur l'eau.

Comparaison référence / rendu du modèle : [`comparaison_rowboat.png`](comparaison_rowboat.png).

## 1. Mesures sur la référence

Il n'y a qu'une vue, en perspective : les mesures sont des rapports, pris sur l'image de 768 × 512 px, et
l'échelle vient de la consigne (4 à 5 blocs de long, 2 de large) et de la rame (une rame de barque fait
environ 1,8 fois la largeur de la coque, ce que l'image confirme : 330 px de rame pour ~190 px de largeur
apparente au banc avant).

| Élément | Sur l'image | Retenu (blocs) |
|---|---|---|
| Longueur hors tout, montant d'étrave → montant d'étambot | 135 → 640 px (diagonale) | **5,45** (bordé 5,0 ; montants à z ±2,72) |
| Largeur maximale (au banc du milieu) | ~190 px apparents | **2,0** |
| Rapport longueur / largeur | ≈ 2,5 – 2,7 | 2,5 (bordé) |
| Franc-bord au milieu (plat-bord → eau), 5 à 6 virures visibles | 150 px pour 190 de largeur | **0,78** au milieu (6 virures) |
| Relevé des extrémités (le plat-bord monte vers les pointes) | +40 % à l'étrave, +35 % à l'étambot | plat-bord à 1,15 (proue) et 1,10 (poupe) |
| Tirant d'eau (sous la flottaison) | invisible | 0,32 (quille), 0,08 aux pointes (tonture de quille) |
| Plat-bord | épais, clair, cerclé de fer (6 bandes visibles) | madrier 0,22 × 0,14, 5 bandes de fer par bord |
| Bancs (traverses) | 3, à une virure sous le plat-bord, + une petite planche de poupe | z = +1,25 / +0,05 / −1,15, dessus à 0,62 ; planche d'extrémité à z −2,0…−2,45 |
| Tolets | montants carrés par paires, 2 positions de nage par bord | paires à z = 0,35 (le rameur) et 1,55 |
| Rame | pale étroite, manche traversant la coque | 3,55 de long : 1,1 en dedans du tolet, 2,45 au dehors, pale 0,75 × 0,28 |
| Membrures | claires, serrées (~tous les 0,45), visibles de l'intérieur | 9 couples (varangue + 2 allonges par bord) |
| Fond intérieur | planches sombres entre les membrures | 3 planches de fond longitudinales à y −0,16 |
| Cordage | 2 tours sur le montant d'étrave, pend le long de l'étrave, lové | 2 tours, une ganse pendante, glène de 2 spires sur le plancher avant |

## 2. Structure du modèle (`tools/generate_rowboat.py`, ~300 cubes)

* **Coque** : 6 virures à clins par bord (chaque virure déborde de 0,02 sur celle du dessous : les laps font
  l'ombre horizontale de la référence), 12 tronçons entre 13 couples de construction, section ronde (profil
  `bottomSection` de `HullShape`, lissé) ; planche de quille, montants d'étrave et d'étambot légèrement
  élancés, dépassant le plat-bord comme sur l'image.
* **Plat-bord** : madrier clair arrondi (texture), bandes de fer, petites plaques rivetées sur la virure de
  tonture sous chaque bande ; serre-bauquière (lisse intérieure) à hauteur des bancs.
* **Intérieur** : 9 membrures claires, 3 planches de fond sombres, 3 bancs de 2 planches, planche triangulaire
  de poupe, 8 tolets.
* **Rames** : deux os `oar_l1` / `oar_r1` (pivot au tolet), animation `row` (attaque → traction dans l'eau →
  relevé → retour), jouée quand la barque avance, à la cadence de sa vitesse ; au repos les pales effleurent
  l'eau.
* **Cordage** : tours sur le montant d'étrave, ganse pendante à l'extérieur de la proue, glène sur le
  plancher avant (os `detail`, masqué de loin).
* Texture : `tools/rowboat_texture.py`, un atlas 128 × 128 (virures, plat-bord, membrures, bancs, fond, fer,
  cordage, rames).

## 3. Jeu

* Objet « Petite barque » : clic droit sur l'eau, placée comme une barque vanilla (eau d'un bloc suffit :
  la quille n'enfonce que de 0,32) ; `/ship give rowboat`, `/ship spawn rowboat`.
* **Clic droit n'importe où sur la barque** : on s'assoit — le premier venu aux rames (banc du milieu,
  place pilote, assis et non debout), le second sur le banc arrière. 2 places. Maj pour descendre : sur la
  terre ferme si elle est à portée, sinon dans l'eau à côté.
* Commandes classiques du mod : Z/S ramer avant/arrière, Q/D tourner, Espace/Ctrl allure. Barque légère :
  part et s'arrête vite, vire court, pivote presque sur place aux rames, vitesse modeste (2 / 3,5 / 5 blocs/s).
* Pilote automatique et routes : comme les autres bateaux (`/ship route ...`, `/ship goto`), rayons de
  passage réduits à la taille de la coque.
* Ambiance : éclaboussures aux pales à chaque attaque et sortie des rames, son de pagaie vanilla, grincement
  de tolet de temps en temps, petites gerbes à l'étrave en marche, roulis très léger.

## 4. Contraintes et choix

* Les bancs sont hauts (0,62 au-dessus de l'eau), comme sur la référence (une virure sous le plat-bord) : un
  joueur assis a les pieds juste au-dessus de la surface, il n'est donc pas « dans l'eau ».
* Pas de pont où marcher : le fond est sous la flottaison ; monter à bord assoit directement (la zone de
  « barre » couvre toute la coque).
* Pas de gouvernail : la direction vient des rames, aucune animation `steer`.
* Coût : ~300 cubes, une texture de 128 px, deux os animés.
