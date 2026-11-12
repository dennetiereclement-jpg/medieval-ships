# Plusieurs joueurs sur un navire en marche (1.30.0)

## Le problème

Chaque client dessine la coque quelques ticks en retard sur le serveur (délai réseau + interpolation). Le client
porte son propre joueur avec la coque qu'il dessine : la position qu'il envoie est juste pour *sa* coque, pas pour
celle du serveur. En marche, la copie serveur du joueur reculait sur le pont de « vitesse × délai » (un ou deux blocs)
et les autres joueurs le voyaient glisser et trembler (positions de joueur envoyées un tick sur deux, interpolées à
part de la coque).

## La solution : coordonnées de pont

- **Repère du client** (`DeckFramePayload`) : avant chaque paquet de mouvement, le client envoie la pose de la coque
  avec laquelle il porte son joueur (seulement quand elle change). Le serveur place le joueur au même point de *sa*
  coque (`DeckSync.onMove`) et le porte avec elle entre deux paquets, comme un mob. La copie serveur est exactement à
  sa place sur le pont, quel que soit le ping : interactions, filets de sécurité, sauvegarde, tout voit le bon point.
- **Position de pont des autres** (`DeckPosPayload`) : le serveur envoie aux joueurs qui le voient la position du
  joueur dans le repère du navire (seulement quand elle change, et une fois par seconde). Les clients le dessinent sur
  la coque telle qu'ils la dessinent, interpolé en coordonnées de pont : plus de glissement ni de tremblement.
  L'animation de marche ne suit que la marche sur le pont, pas le mouvement du navire.
- **Téléportations sur un pont** (`DeckTeleportPayload`) : descendre d'un siège, revenir à bord, commande… le client
  atterrit au bon endroit de la coque qu'il dessine (plus dans un mur ni par-dessus le bastingage).
- Le client porte son joueur avant qu'il marche si la coque a déjà bougé ce tick (joueur recréé après les navires,
  par exemple après une réapparition).
- La vitesse de l'entité navire n'est plus envoyée à chaque tick (les clients ne s'en servent pas).

Coût : quelques opérations par joueur et par tick, des paquets seulement quand quelqu'un marche sur un pont.

## Retour à bord après une déconnexion

L'endroit où un joueur se tient (ou est assis) à bord est gardé dans **ses propres données** (attachement persistant
`medievalships:deck_anchor` du joueur : navire, dimension, position et orientation locales), mis à jour pendant qu'il
est à bord et effacé quand il en descend. À la reconnexion, s'il était à bord d'un navire qui a continué sa route, il
revient sur son pont au même endroit dès que le navire est chargé (le navire note sa position tant que des joueurs se
sont déconnectés à bord, pour charger son chunk). Si le navire n'existe plus : sur le pont d'un navire proche ou sur
la terre ferme la plus proche, jamais dans la mer.

## Compatibilité Nexus Characters (plusieurs personnages par compte)

Nexus remplace tout le fichier du joueur (même UUID de compte pour tous les personnages) et peut recréer l'entité
joueur. Rien n'est donc gardé par compte : l'ancrage voyage avec chaque personnage (il est dans son fichier), l'état
de synchronisation vit dans l'entité joueur elle-même (une entité recréée repart de zéro), l'ancien enregistrement
par compte des versions précédentes est lu une fois puis oublié (ignoré si Nexus est présent). Pas de dépendance :
le mod fonctionne avec ou sans Nexus. Le retour à bord attend que Nexus ait restauré le personnage (10 ticks).
