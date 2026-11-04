# 対応表: 設計 ID とコードの対応

粒度: function（ファイル・公開関数まで）。書式は trace-map-rules.md に従う。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-SERVER` | `src/server.js` | モジュール |
| `DS-FN-START-SERVER` | `src/server.js::startServer` | 公開関数 |
| `DS-MD-ROUTES` | `src/routes.js` | モジュール |
| `DS-FN-ROUTE-REQUEST` | `src/routes.js::handleRequest` | 公開関数 |
| `DS-FN-SERVE-STATIC-FILE` | `src/routes.js::serveStaticFile` | 公開関数 |
| `DS-IF-API-SPIN` | `src/routes.js::handleSpin` | POST /api/spin |
| `DS-IF-API-PRIZES` | `src/routes.js::handlePrizes` | GET /api/prizes |
| `DS-IF-API-WINNINGS` | `src/routes.js::handleWinnings` | GET /api/winnings |
| `DS-MD-SPIN` | `src/spin.js` | モジュール |
| `DS-FN-VALIDATE-PLAYER-NAME` | `src/spin.js::validatePlayerName` | 公開関数 |
| `DS-FN-PICK-WEIGHTED-PRIZE` | `src/spin.js::pickWeightedPrize` | 公開関数 |
| `DS-FN-PERFORM-SPIN` | `src/spin.js::performSpin` | 公開関数 |
| `DS-MD-DB` | `src/db.js` | モジュール |
| `DS-FN-OPEN-DATABASE` | `src/db.js::openDatabase` | 公開関数 |
| `DS-FN-SEED-INITIAL-DATA` | `src/db.js::seedInitialData` | 公開関数 |
| `DS-FN-LIST-PRIZES` | `src/db.js::listPrizes` | 公開関数 |
| `DS-FN-INSERT-WINNING-RECORD` | `src/db.js::insertWinningRecord` | 公開関数 |
| `DS-FN-LIST-WINNINGS-BY-NAME` | `src/db.js::listWinningsByName` | 公開関数 |
| `DS-TS-SPIN-AND-RECORD-E2E` | `e2e/spin-and-record.test.js` | E2E |
| `DS-TS-NAME-VALIDATION-E2E` | `e2e/name-validation.test.js` | E2E |
| `DS-TS-VIEW-PRIZES-E2E` | `e2e/view-prizes.test.js` | E2E |
| `DS-TS-VIEW-OWN-WINNINGS-E2E` | `e2e/view-own-winnings.test.js` | E2E |
| `DS-TS-NAVIGATE-SCREENS-E2E` | `e2e/navigate-screens.test.js` | E2E |
| `DS-TS-INITIAL-DATA-E2E` | `e2e/initial-data.test.js` | E2E |
