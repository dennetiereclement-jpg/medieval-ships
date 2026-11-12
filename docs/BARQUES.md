# Barques des navires (1.30.0)

Les navires qui portent une barque en décor sur leur pont la mettent **réellement à l'eau** : c'est la **petite barque
du mod** (`medievalships:rowboat`, celle de l'objet « Petite barque »), avec ses deux places et ses rames, qu'on peut
piloter puis rembarquer.

## Navires concernés

| Navire | Barque | Où elle est rangée | Mise à l'eau |
|---|---|---|---|
| Grand galion (`galleon`) | la chaloupe | sur ses cales, au-dessus de l'écoutille avant du pont principal | le long de la coque, à hauteur de ses cales |
| Grand vaisseau de guerre (`warship`) | la chaloupe | sur ses chantiers, dans l'embelle, entre le grand mât et le mât de misaine | idem |
| Vieux Corsaire (`old_corsair`) | le canot | sur deux cales, sur la dunette | le long de la hanche, en avant de la galerie de poupe |
| Nautilus (`nautilus`) | le canot | dans son logement sur la plate-forme (aussi le levier devant) | idem ; en surface seulement |

Les autres navires (galère, galère rouge, voilier elfique, bateau à roue, frégate, sloop, navires de la cité, dirigeables,
léviathan, jonque, skiff, montgolfière) n'ont pas de barque sur leur pont. La « barque (décor) » (`barque_deco`) est un
décor à poser à terre, pas un navire : elle n'est pas concernée.

## Utilisation

* **Mettre à l'eau** : clic droit sur la barque rangée sur le pont (l'indication « Clic droit : mettre la chaloupe à
  l'eau » s'affiche). Elle est posée sur l'eau **du côté du joueur** (bâbord ou tribord), à l'écart de la coque ; s'il
  n'y a pas de place (quai, autre coque, berge), un peu plus loin ou un peu plus en avant / en arrière, puis de l'autre
  côté. La barque du décor disparaît du pont (ses cales restent).
* **Refus** (message en rouge) : navire pas à flot (échoué, soulevé), Nautilus en plongée, pas d'eau libre le long de la
  coque, barque déjà à l'eau (une seule par navire), manœuvre en cours (deux secondes après une mise à l'eau ou un
  rembarquement : deux joueurs qui cliquent en même temps ne la lancent pas puis la rembarquent aussitôt).
* **Rembarquer** : ramener la barque le long de la coque (à moins de « demi-largeur de la coque + 9 » blocs environ de
  ses cales), puis
  * clic droit sur ses cales depuis le pont, ou
  * depuis la barque elle-même, clic droit sur la coque du navire : la barque est hissée avec son équipage, qui est
    déposé sur le pont (à l'endroit où l'on monte à bord d'habitude).
  Trop loin : refus avec la distance à respecter. La barque du décor réapparaît.
* Le pont de la chaloupe du vaisseau de guerre (sur laquelle on peut marcher) disparaît avec elle tant qu'elle est à
  l'eau : on ne se cogne pas à une barque invisible.

## Robustesse

* L'identifiant de la barque est enregistré avec le navire, et celui du navire avec la barque : tout survit à un
  redémarrage du serveur.
* **Barque détruite** là où le serveur la voit (récupérée par un administrateur, tuée par commande...) : le navire s'en
  aperçoit en deux secondes et sa barque de décor revient.
* **Barque hors de portée du serveur** (zone déchargée, joueur déconnecté dedans) : le prochain rembarquement la passe
  par pertes (« une chaloupe de rechange a été embarquée ») et le décor revient ; si l'ancienne barque est rechargée un
  jour, elle **disparaît** d'elle-même (jamais deux barques). Les identifiants ainsi passés par pertes sont gardés dans les
  données du monde (les 512 derniers).
* **Navire récupéré** ou supprimé : sa barque à l'eau reste, devenue une petite barque ordinaire.
* Tout se passe sur le serveur ; le client ne fait que viser et afficher (serveur dédié compris).

## Commandes (administrateurs)

| Commande | Effet |
|---|---|
| `/ship barque lancer` | Met à l'eau la barque du navire visé (ou sur lequel on est). |
| `/ship barque rembarquer` | La rembarque (mêmes règles qu'au clic). Depuis la barque elle-même, vise son navire. |
| `/ship barque remplacer` | La rembarque où qu'elle soit, ou remet une barque neuve si elle est perdue. |
| `/ship nautilus canot lancer` / `rembarquer` / `remplacer` | Les mêmes pour le Nautilus (inchangées). |

## Pour les développeurs

* Description partagée : `core/ShipBoats` (navires, boîte de clic, points de mise à l'eau calculés depuis la forme de
  la coque, portée, bit `AWAY_BIT` des réglages synchronisés, boîte de pont du vaisseau de guerre). La hauteur de mise à
  l'eau vient de la **ligne de flottaison du navire lue à l'exécution** (`hull().waterlineY`) et de la surface réelle de
  l'eau.
* Serveur : `entity/ShipBoatHandling` (mise à l'eau, rembarquement, nettoyage une fois par seconde quand la barque est
  à l'eau, navire supprimé, barques passées par pertes). Le clic arrive par `PickKind.BOAT` (`ShipPicker`,
  `ShipInteractions`).
* Modèles : la barque du galion, du vaisseau de guerre et du corsaire partage un os avec le pont ; au chargement,
  `BbModel.Split` déplace ses éléments `boat_*` (sauf les cales `boat_chock*` / `boat_skid*`) dans un os `deco_boat`
  caché quand elle est à l'eau (l'image ne change pas). Le Nautilus a déjà son os `lifeboat`.
* Tests : JUnit `ShipBoatsTest` ; en jeu `ShipBoatGameTest` (galion, vaisseau, corsaire, solo et serveur dédié) et le
  scénario du Nautilus (dont le redémarrage).
