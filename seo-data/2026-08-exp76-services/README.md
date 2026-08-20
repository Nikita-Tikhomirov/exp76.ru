# Semantic-core scope

This directory defines the read-only scope for semantic collection for exp76.ru.

## Approved services

| ID | Service | Existing URL |
| --- | --- | --- |
| S1 | Ландшафтное проектирование | https://exp76.ru/services/landshaftnoe-proektirovanie/ |
| S2 | Газон посевной и рулонный | https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/ |
| S3 | Посадка деревьев и кустарников | https://exp76.ru/services/posadka-derevev-i-kustarnikov/ |
| S4 | Уход за садом | https://exp76.ru/services/ukhod-za-sadom/ |
| S5 | Планировка территории | https://exp76.ru/services/planirovka-territorii/ |
| S6 | Подпорные стенки | https://exp76.ru/services/podpornye-stenki/ |
| S7 | Уличное и ландшафтное освещение участка | https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/ |
| S8 | Въезд и заезд на участок через канаву | https://exp76.ru/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/ |

## Frozen category hubs

These six existing directions and their child content are immutable in this phase:

- https://exp76.ru/category/drenazh-uchastka/
- https://exp76.ru/category/otmostka-vokrug-doma/
- https://exp76.ru/category/ukladka-trotuarnoy-plitki/
- https://exp76.ru/category/osushenie-uchastka/
- https://exp76.ru/category/livnevaya-kanalizatsiya/
- https://exp76.ru/category/avtopoliv-na-uchastke/

Raw source files are immutable. This phase never writes to WordPress, FTP, Yandex settings, or published URLs. Secrets, credentials, and tokens are prohibited in this directory.

Later tasks add these read-only CLI commands, which must preserve this boundary:

- `validate-scope`
- `register-source`
- `ingest`
- `classify`
- `cluster`
- `export`
- `qa`
