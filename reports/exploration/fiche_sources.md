# Fiche de sources : IEEE-CIS Fraud Detection

| Attribut | train_transaction.csv | train_identity.csv |
|---|---|---|
| Format | CSV | CSV |
| Lignes | 590,540 | 144,233 |
| Colonnes | 394 | 41 |
| Cle de jointure | TransactionID | TransactionID |
| Doublons sur la cle | 0 | 0 |
| Colonnes > 50 % manquantes | 174 | 12 |
| Proprietaire | Vesta Corporation (Kaggle) | Vesta Corporation (Kaggle) |
| Sensibilite RGPD | Anonymise | Anonymise |

## Indicateurs cles
- Taux de fraude : 3.50 % (20,663 fraudes)
- Couverture de la jointure (transactions avec identite) : 24.4 %
- Periode couverte : 182 jours (date de depart fictive : 2017-12-01)
- Montant moyen : 135.03 | median : 68.77

## Points d'attention
- Forte proportion de valeurs manquantes, surtout dans les colonnes id_* et V*.
- TransactionDT est un delta en secondes, pas une vraie date.
- Aucun identifiant client explicite : reconstruction a partir de card1, addr1, P_emaildomain.
