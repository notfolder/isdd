# 要件定義書: 生物種情報データベース（Species Information Database）

## 1. 目的・前提

- システムの目的: 種（species）ごとの生物情報を、Web 画面で閲覧・検索・絞り込み・登録・修正・削除できるようにする。
- 用語集

  | 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 |
  |---|---|---|---|
  | 種（Species） | 生物の分類単位。1 件の生物情報の対象 | 登録・閲覧・検索の単位 | 生物種 |
  | 学名（Scientific name） | 属名と種小名からなる国際的な名称（例: Panthera leo） | 必須。重複を許さない | ― |
  | 一般名（Common name） | 日常で使う名称（例: Lion） | 必須。一覧の主表示 | 和名（和名の意味で使わない） |
  | 綱（Class） | 分類の階層のひとつ | 選択式。6 種の固定リスト | ― |
  | 生息環境（Habitat） | 主に暮らす環境 | 選択式。7 種の固定リスト | ― |
  | 食性（Diet） | 主な食べ物の種類 | 選択式。4 種の固定リスト | ― |
  | 保全状況（Conservation status） | IUCN レッドリストの区分 | 選択式。6 種の固定リスト | ― |

- システムの形態: GUI（Web 画面）。ブラウザから利用する。他のシステムへの API 提供、バッチ、CUI は無い。

### 1-1. 技術制約（前提として記録する。要件ではないため ID は付与しない）

| 制約項目 | 内容 | 出どころ（誰がいつ答えたか） |
|---|---|---|
| 既存コードベース | 無し（新規開発） | 依頼文（既存コードへの言及が無い） |
| 配備先 | ローカルマシンで `run.sh` により起動する Web サーバー。コンテナは使わない | 契約書 contract.md |
| チームの技術 | 特に無い（依頼者の指定なし。Python 3.12 と Node.js 24 が使える環境とのみ契約書にある） | 契約書 contract.md |
| ライセンスとコスト | 無料のライブラリのみ。外部サービスと有償 API は使わない | 契約書 contract.md |
| 性能と規模の目安 | 種の件数は 1,000 件以下、同時利用は 5 人程度（1-2 の決め事） | エージェントの最小案（1-2 参照） |

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 外部連携の有無 | 外部連携は無い | 依頼文に外部システムの言及が無いため（開始ゲートの問い 1 に対する推測） | 未確認 |
| 既存ソースコードの有無 | 既存コードは無い（新規フロー） | 依頼文に既存コードの言及が無いため | 未確認 |
| 生物情報の項目 | 種 1 件に次の項目を持つ: 学名、一般名、綱、科、生息環境、食性、保全状況、平均寿命（年）、成体の平均体重（kg）、説明 | 依頼の「biological information」を表す最小の項目。画面から使える範囲に限った | 未確認 |
| 必須項目 | 学名、一般名、綱、生息環境、食性、保全状況 は必須。科、平均寿命、平均体重、説明は任意 | 検索と絞り込みに使う項目を必須にし、残りは任意にする最小案 | 未確認 |
| 固定リストの内容 | 綱: Mammalia、Aves、Reptilia、Amphibia、Actinopterygii、Insecta。生息環境: Terrestrial、Freshwater、Marine、Forest、Grassland、Desert、Wetland。食性: Herbivore、Carnivore、Omnivore、Insectivore。保全状況: LC、NT、VU、EN、CR、DD（IUCN の区分） | 一般的な分類の範囲。フリー入力だと絞り込みが成り立たないため固定リストにする。「その他」は無い | 未確認 |
| 入力の検査 | 学名は 2〜100 文字、一般名は 1〜100 文字、科は 100 文字以下、平均寿命は 1〜300 の整数、平均体重は 0 より大きく 200000 以下の数（小数点以下 2 桁まで）、説明は 1000 文字以下。空欄や範囲外の入力は保存せず、項目ごとにエラー文言を表示する | 既定の上限値を決める必要があったための最小案 | 未確認 |
| 学名の重複 | 学名は大文字小文字を区別せず一意。重複は登録・修正を拒否し「This scientific name is already registered.」と表示する | 同じ種の二重登録を防ぐ業務ルール（RQ-FT-UNIQUE-SCIENTIFIC-NAME） | 未確認 |
| 検索の方法 | 学名と一般名のどちらかに、入力文字列を含む（大文字小文字を区別しない）種を表示する。空の検索は全件表示 | 依頼の「search for specific data」の最小の解釈 | 未確認 |
| 絞り込みの方法 | 綱・生息環境・食性・保全状況の 4 つを選択式で絞り込む。複数を選んだ場合は全部に合う種だけを表示する（AND）。「All」を選ぶとその条件は無視する | 依頼の「filter data based on different criteria」の最小の解釈 | 未確認 |
| 一覧の並び順 | 一般名の昇順（英字の大文字小文字を区別しない） | 最小案。並び替えの画面は作らない | 未確認 |
| 一覧の件数表示 | 「Showing N of M species」を表示する（N は絞り込み後、M は全件） | 絞り込み結果の把握のため。最小案 | 未確認 |
| 検索条件の引き継ぎ | 一覧の検索条件を詳細画面へ持ち越し、詳細画面の「Back to results」で同じ条件の一覧に戻る | 一覧から詳細へ行って戻ったとき条件が消えないため（操作の最小限の配慮） | 未確認 |
| 削除の扱い | 削除は確認ダイアログの後に完全に削除する（復元の仕組みは作らない）。削除後は一覧に「Species deleted.」を表示する | 依頼に無い復元機能を作らないための最小案 | 未確認 |
| 見本データ | DATA_DIR に初めてデータベースを作ったときだけ、見本の種 12 件を投入する。以後は投入しない（全件削除後に再投入しない） | 契約書（初期データ）を満たす最小案 | 未確認 |
| 見本データの内容 | 12 種（ライオン、ニホンザル、ジャイアントパンダ、スズメ、コイ等）。保全状況・平均寿命・平均体重は画面の動作確認のための例示値で、公式情報としては扱わない（README に注意書き） | 契約書「sample species」を満たすため。値の正確さを保証できないため例示と明記する | 未確認 |
| 認証と権限 | ログイン・利用者の区別は無い。誰でも登録・修正・削除できる | 依頼に認証の指定が無く、社内の単一利用者を想定した最小案 | 未確認 |
| 同時更新 | 排他制御は行わない。後から保存した内容で上書きする（最後の保存が有効） | 同時利用 5 人程度で、衝突の業務影響が小さいための最小案 | 未確認 |
| 利用者の入口 | 起動後、ブラウザで http://127.0.0.1:PORT を開く。ホーム画面を入口にする | 契約書（ルート URL から操作される） | 未確認 |
| 画面の色 | 背景（ベース）はリネン（#FAF0E6）。ナビゲーション、ボタン、表の見出し、リンク、フォーカス枠などのコンポーネントはマルーン（#800000）。本文の文字色は黒に近い濃い色（#2B1D1D）。文字色は依頼に無いため読みやすさの最小案 | 依頼の「linen base color」「maroon for all components」 | 未確認 |
| 見込み経営効果 | 算定しない（理由: 依頼に業務の数値・金額が無く、効果を算定できないため） | 依頼に業務データが無い | 未確認 |
| 性能 | 一覧・検索の応答は 1 秒以内（種 1,000 件以下） | 性能の目安を決める必要があったため | 未確認 |

## 2. 業務

- 対象業務一覧

  | RQ-BZ-ID | 業務名 | 業務の範囲 | 担当者 |
  |---|---|---|---|
  | `RQ-BZ-SPECIES-INFO-MANAGEMENT` | 種の生物情報の管理 | 種の生物情報を閲覧・検索・絞り込み・登録・修正・削除する | 利用者（誰でも。1-2 参照） |

- 業務フロー

  ```mermaid
  flowchart TD
      A[利用者が種の情報を探す] --> B{一覧で見つかるか}
      B -->|検索・絞り込み| C[一覧で候補を絞る]
      C --> D[詳細を見る]
      B -->|無い| E[新しい種を登録する]
      D --> F{修正か削除か}
      F -->|修正| G[情報を修正する]
      F -->|削除| H[種を削除する]
  ```

### 2-1. 業務の問題（あるべき姿と現状のギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 種ごとの生物情報を探すのに時間がかかる | `RQ-BZ-SPECIES-INFO-MANAGEMENT` | 必要な種の情報を、検索と絞り込みで素早く見つけられる | 不明（依頼に現状の情報源と探索時間が無い） | 不明（既存の台帳の探索時間を未計測のため） | 不明 |
| 種の情報の登録・修正・削除が統一された場所で行われていない | `RQ-BZ-SPECIES-INFO-MANAGEMENT` | 種の情報を 1 か所で登録・修正・削除し、記録を保つ | 不明（依頼に現状の管理方法が無い） | 不明（件数と更新の頻度を未計測のため） | 不明 |

### 2-2. 業務課題一覧（必須）

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| `RQ-BK-FIND-SPECIES-INFO` | 種の生物情報を、一覧・検索・絞り込み・詳細で探せるようにする | 種ごとの生物情報を探すのに時間がかかる | 目標値は未設定（現状を計測していないため） | `RQ-BZ-SPECIES-INFO-MANAGEMENT` |
| `RQ-BK-MAINTAIN-SPECIES-INFO` | 種の生物情報を Web 上で登録・修正・削除できるようにする | 種の情報の登録・修正・削除が統一されていない | 目標値は未設定（現状を計測していないため） | `RQ-BZ-SPECIES-INFO-MANAGEMENT` |

### 2-3. 見込み経営効果

見込み経営効果は算定しない（理由: 依頼に業務の金額・時間の数値が無く、効果の見込みを算定する根拠が無いため）。

## 3. 機能要件

- 入力データ: 利用者が画面のフォームから入力する（人手入力）。外部データの入力は無い。出力データは画面に表示する。
- 利用フロー（全機能）

  ```mermaid
  flowchart LR
      H[ホーム] --> L[種の一覧]
      H --> N[種の登録]
      L --> D[種の詳細]
      L --> N
      D --> E[種の修正]
      E --> D
      D --> X[削除を実行]
      X --> L
      N --> D
  ```

- 機能一覧

  | RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか |
  |---|---|---|---|---|
  | `RQ-FT-BROWSE-SPECIES` | 業務機能 | 種の一覧を表示する | `RQ-BK-FIND-SPECIES-INFO` | 登録されている種を全体として見渡せない |
  | `RQ-FT-SEARCH-SPECIES` | 業務機能 | 学名または一般名で種を検索する | `RQ-BK-FIND-SPECIES-INFO` | 特定の種の情報を探せない |
  | `RQ-FT-FILTER-SPECIES` | 業務機能 | 綱・生息環境・食性・保全状況で種を絞り込む | `RQ-BK-FIND-SPECIES-INFO` | 条件に合う種の集まりを作れない |
  | `RQ-FT-VIEW-SPECIES-DETAIL` | 業務機能 | 種の生物情報の詳細を表示する | `RQ-BK-FIND-SPECIES-INFO` | 一覧に無い項目（説明、平均寿命など）を確かめられない |
  | `RQ-FT-CREATE-SPECIES` | 業務機能 | 新しい種を登録する | `RQ-BK-MAINTAIN-SPECIES-INFO` | 新しく分かった種の情報を残せない |
  | `RQ-FT-UPDATE-SPECIES` | 業務機能 | 種の生物情報を修正する | `RQ-BK-MAINTAIN-SPECIES-INFO` | 誤りや更新された情報を直せない |
  | `RQ-FT-DELETE-SPECIES` | 業務機能 | 種を削除する | `RQ-BK-MAINTAIN-SPECIES-INFO` | 登録の誤りを取り除けない |
  | `RQ-FT-UNIQUE-SCIENTIFIC-NAME` | 業務機能 | 学名の重複を登録させない（業務ルール） | `RQ-BK-MAINTAIN-SPECIES-INFO` | 同じ種が二重に登録され、検索結果が混乱する |
  | `RQ-OP-SAMPLE-DATA-ON-FIRST-RUN` | 運用 | 初回起動時に見本データを投入する | `RQ-BK-MAINTAIN-SPECIES-INFO` | 初めて起動したとき、何も操作できる内容が無い |

### 3-1. 帳票・出力ファイル

帳票・出力ファイルは無い（画面だけで情報を表示する）。

### 3-2. 業務ルール

| RQ-ID | ルール名 | 内容（条件と結果） | 違反時・エラー時の業務上の扱い | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| `RQ-FT-UNIQUE-SCIENTIFIC-NAME` | 学名の一意性 | 登録・修正のとき、学名が既存の別の種と大文字小文字を区別せず同じなら、保存しない | 「This scientific name is already registered.」を学名の欄に表示し、入力を保持して再入力させる | `RQ-BK-MAINTAIN-SPECIES-INFO` |

### 3-3. 外部連携

外部連携は無い。

## 4. データ

### 4-1. データ要件一覧

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-DT-SPECIES-STORAGE` | 内部データ | 種の情報は内部データとして、データディレクトリ（環境変数 DATA_DIR）の中の SQLite ファイルに保存する。外部データは扱わない | `RQ-BK-MAINTAIN-SPECIES-INFO` | 起動のたびに登録内容が消え、登録の意味が無くなる |
| `RQ-DT-SPECIES-RETENTION` | データ保持 | 保持期間は無期限。利用者が削除するまで残す | `RQ-BK-MAINTAIN-SPECIES-INFO` | 利用者が必要な情報を残せず、登録の意味が無くなる |

データベースが必要か: 必要。種の件数は 1,000 件以下、検索と絞り込みを行うため、ファイル形式の DB（SQLite）を使う（件数の増加は年間数十件程度を想定。増加率は依頼から不明のため、件数上限は 1,000 件として性能要件に含める）。

### 4-2. 業務エンティティとデータ項目

| RQ-ID | カテゴリ | 業務エンティティ名 | 対応業務課題ID（RQ-BK-*） | この業務エンティティが無いと何が困るか |
|---|---|---|---|---|
| `RQ-DT-SPECIES-ENTITY` | マスタ | 種（Species） | `RQ-BK-FIND-SPECIES-INFO`, `RQ-BK-MAINTAIN-SPECIES-INFO` | 生物情報を 1 件ずつ管理できない |

| エンティティ名 | 項目名 | 業務上の意味 | 必須 | 形式・桁 | 値の範囲・制約 | 例 |
|---|---|---|---|---|---|---|
| 種 | 学名 | 国際的な学名 | 必須 | 文字列 2〜100 文字 | 大文字小文字を区別せず一意 | Panthera leo |
| 種 | 一般名 | 日常で使う名称 | 必須 | 文字列 1〜100 文字 | ― | Lion |
| 種 | 綱 | 分類の綱 | 必須 | 固定リストから 1 つ | Mammalia、Aves、Reptilia、Amphibia、Actinopterygii、Insecta | Mammalia |
| 種 | 科 | 分類の科 | 任意 | 文字列 0〜100 文字 | ― | Felidae |
| 種 | 生息環境 | 主な生息環境 | 必須 | 固定リストから 1 つ | Terrestrial、Freshwater、Marine、Forest、Grassland、Desert、Wetland | Grassland |
| 種 | 食性 | 主な食べ物の種類 | 必須 | 固定リストから 1 つ | Herbivore、Carnivore、Omnivore、Insectivore | Carnivore |
| 種 | 保全状況 | IUCN レッドリストの区分 | 必須 | 固定リストから 1 つ | LC、NT、VU、EN、CR、DD | VU |
| 種 | 平均寿命（年） | 野生での平均寿命の目安 | 任意 | 整数 | 1〜300 | 14 |
| 種 | 成体の平均体重（kg） | 成体の平均体重 | 任意 | 数（小数点以下 2 桁まで） | 0 より大きく 200000 以下 | 190 |
| 種 | 説明 | 種の特徴の説明文 | 任意 | 文字列 0〜1000 文字 | ― | Large social cat of the African savanna. |

固定リストの表示名: 保全状況の LC は「Least Concern」、NT は「Near Threatened」、VU は「Vulnerable」、EN は「Endangered」、CR は「Critically Endangered」、DD は「Data Deficient」。食性は Herbivore 等をそのまま表示する。

### 4-3. CRUD テーブル（必須）

| エンティティ名 | Create | Read（一覧） | Read（詳細） | 検索 | Update | Delete | 備考 |
|---|---|---|---|---|---|---|---|
| 種（Species） | ○ | ○ | ○ | ○ | ○ | ○ | 検索の条件: 学名・一般名の部分一致（大文字小文字を区別しない）と、綱・生息環境・食性・保全状況の絞り込み（AND）。トランザクション: 1 件の登録・修正・削除は 1 操作で完結する。同時更新の排他制御は行わない（1-2 参照） |

### 4-4. 状態遷移

状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI の場合のみ）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| `RQ-UI-HOME-SCREEN` | ホーム画面 | 種:Read（一覧）の入口 | 登録件数と保全状況が VU・EN・CR の件数、一覧と登録への入口を示す | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-UI-SPECIES-LIST-SCREEN` | 種の一覧・検索画面 | 種:Read（一覧）、種:検索 | 検索欄と 4 つの絞り込みで種を探し、一覧を表示する | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-UI-SPECIES-DETAIL-SCREEN` | 種の詳細画面 | 種:Read（詳細）、種:Delete | 種の全項目を表示し、修正と削除への入口を示す | `RQ-BK-FIND-SPECIES-INFO`, `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-UI-SPECIES-CREATE-SCREEN` | 種の登録画面 | 種:Create | 種の項目を入力して登録する | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-UI-SPECIES-EDIT-SCREEN` | 種の修正画面 | 種:Update | 登録済みの種の項目を変更して保存する | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-UI-NOT-FOUND-SCREEN` | 見つからない種の画面 | 種:Read（詳細） | 存在しない種の URL を開いたときに案内を表示する | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-UI-NAVIGATION-MENU` | 共通の案内メニュー | 種:Read（一覧）、種:Create | すべての画面の上部に、ホーム・種の一覧・種の登録へのメニューを表示する | `RQ-BK-FIND-SPECIES-INFO`, `RQ-BK-MAINTAIN-SPECIES-INFO` |

#### 画面ごとの仕様（GUI 5 項目）

- ホーム画面: 目的は全体の把握と入口。主要要素は見出し、件数の表示 2 つ（Total species、Threatened species = VU・EN・CR の件数）、ボタン「Browse species」「Add species」。入力項目は無い。エラー時は無い。
- 種の一覧・検索画面: 目的は種を探すこと。主要要素は検索欄（Search by name）、絞り込みの選択 4 つ（Class、Habitat、Diet、Conservation status。先頭は「All」）、ボタン「Search」「Clear」、件数表示、表（Common name、Scientific name、Class、Habitat、Diet、Conservation status）。種の一般名をクリックすると詳細へ移る。0 件のときは「No species match your search.」を表示する。
- 種の詳細画面: 目的は 1 件の全情報を見ること。主要要素は見出し（一般名）、学名、全項目の表示、「Back to results」「Edit」「Delete」。削除は確認ダイアログ「Delete this species? This cannot be undone.」の後に実行する。
- 種の登録・修正画面: 目的は項目の入力と保存。入力項目は 4-2 の全項目（綱・生息環境・食性・保全状況は選択式、「Select」を初期値とする）。ボタン「Save」「Cancel」。エラー時は、エラーの一覧を画面の上部に表示し、該当する欄の下にも同じ文言を表示する。入力内容は保持する。
- 見つからない種の画面: 「Species not found.」と「Back to species list」を表示する。

## 5. 非機能要件

- 利用者の種別と経路: 利用者は社内の利用者（一般公開はしない）。ローカルマシンまたは社内ネットワークからブラウザで利用する。`RQ-NF-USER-ACCESS`
- 性能: 一覧・検索・絞り込みの応答は、種 1,000 件以下で 1 秒以内。`RQ-NF-RESPONSE-TIME`
- 利用人数: 同時接続 5 人程度。`RQ-NF-CONCURRENT-USERS`
- 可用性: 可用性の要求は無い（業務の停止時間の要求が依頼に無いため）。
- 移行性: 移行は無い（既存のデータは無い）。
- セキュリティ:
  - 認証方式: 無し（1-2 参照）。権限制御の粒度は無し。
  - 利用者の入力は画面に表示するときに HTML の特殊文字をエスケープする。`RQ-NF-ESCAPE-USER-INPUT`
  - 監査証跡の改ざん防止: 不要（監査証跡の要求が無いため）。
- 見た目: 背景はリネン（#FAF0E6）、すべてのコンポーネントはマルーン（#800000）で統一する。`RQ-NF-COLOR-THEME`
- 言語: 画面の言語は英語。`RQ-NF-ENGLISH-UI`

| RQ-ID | カテゴリ | 非機能要件名 | 対応業務課題ID（RQ-BK-*） | この非機能要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-NF-USER-ACCESS` | 利用者 | 社内の利用者が、ローカルまたは社内ネットワークからブラウザで利用する | `RQ-BK-FIND-SPECIES-INFO` | 利用者の範囲と公開の可否が決まらず、設計と実装の方針が定まらない |
| `RQ-NF-RESPONSE-TIME` | 性能 | 一覧・検索・絞り込みを 1 秒以内に応答する（種 1,000 件以下） | `RQ-BK-FIND-SPECIES-INFO` | 探す操作が遅く、一覧を使わなくなる |
| `RQ-NF-CONCURRENT-USERS` | 利用人数 | 同時接続 5 人程度に耐える | `RQ-BK-FIND-SPECIES-INFO` | 同時に使うと応答が止まる |
| `RQ-NF-ESCAPE-USER-INPUT` | セキュリティ | 利用者の入力を HTML として解釈させず、表示時にエスケープする | `RQ-BK-MAINTAIN-SPECIES-INFO` | 入力された文字列が画面で意図しない表示や動作を起こす |
| `RQ-NF-COLOR-THEME` | 見た目 | 背景をリネン、すべてのコンポーネントをマルーンで表示する | `RQ-BK-FIND-SPECIES-INFO`, `RQ-BK-MAINTAIN-SPECIES-INFO` | 依頼された配色で表示されない |
| `RQ-NF-ENGLISH-UI` | 言語 | 画面の文言をすべて英語で表示する | `RQ-BK-FIND-SPECIES-INFO`, `RQ-BK-MAINTAIN-SPECIES-INFO` | 契約書の言語の条件を満たさない |

## 6. 運用要件

- ログ: 一般的な動作ログ・エラーログ以外は不要。ログの内容と保存期間の記述は行わない。
- 監査ログ: 不要（1-2 参照）。
- 監視・アラート: 監視・アラートは必要ないため、監視・アラートの内容と対応方法の記述は行わない。
- バックアップと復旧: バックアップは必要ない（DATA_DIR のファイルを利用者が手動で複製する）。

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-OP-START-SCRIPTS` | 起動 | `bash setup.sh` で依存を準備し、`PORT=任意 bash run.sh` で Web サーバーを前面で起動する。PORT の既定値は 8000、データは環境変数 DATA_DIR の下に作る（既定値は `./data`） | `RQ-BK-MAINTAIN-SPECIES-INFO` | 契約書どおりに起動できず、採点対象として動かせない |
| `RQ-OP-SAMPLE-DATA-ON-FIRST-RUN` | 初期データ | DATA_DIR にデータベースが無い状態で起動したとき、見本の種 12 件を投入する。以後は投入しない | `RQ-BK-MAINTAIN-SPECIES-INFO` | 初回に画面が空で、全機能を試せない |

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| `RQ-TS-OPEN-HOME-AND-MENU` | ホーム画面と案内メニューが開けること | 空の DATA_DIR で起動し見本データが入っている | 1. ルート URL を開く 2. メニューの「Species」「Add species」「Home」を順に押す | 各画面が開き、ホームに件数（Total species、Threatened species）が表示される | `RQ-UI-HOME-SCREEN`, `RQ-UI-NAVIGATION-MENU`, `RQ-NF-ENGLISH-UI`, `RQ-NF-COLOR-THEME` | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-TS-SAMPLE-DATA-ON-FIRST-RUN` | 初回起動で見本データが入ること | DATA_DIR が空 | 1. 起動する 2. 一覧を開く | 見本の種 12 件が表示され、件数表示が「Showing 12 of 12 species」になる | `RQ-OP-SAMPLE-DATA-ON-FIRST-RUN`, `RQ-OP-START-SCRIPTS` | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-TS-BROWSE-SPECIES-LIST` | 一覧に種が表示されること | 見本データがある | 1. 一覧を開く | 一般名の昇順で全件の表が表示される | `RQ-FT-BROWSE-SPECIES`, `RQ-UI-SPECIES-LIST-SCREEN` | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-TS-SEARCH-SPECIES-BY-NAME` | 学名・一般名の部分一致で検索できること | 見本データがある | 1. 検索欄に「lion」と入力し Search を押す 2. 検索欄に「Panthera」と入力し Search を押す | 1. Lion が表示される 2. 学名が Panthera の種が表示される | `RQ-FT-SEARCH-SPECIES`, `RQ-UI-SPECIES-LIST-SCREEN` | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-TS-FILTER-SPECIES` | 絞り込みが AND で働くこと | 見本データがある | 1. Class を Aves に選び Search を押す 2. Habitat を Forest に追加して Search を押す 3. Clear を押す | 1. 鳥類のみ表示 2. 鳥類かつ森林の種のみ表示 3. 全件に戻る | `RQ-FT-FILTER-SPECIES`, `RQ-UI-SPECIES-LIST-SCREEN` | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-TS-NO-MATCH-MESSAGE` | 該当が無いとき案内が出ること | 見本データがある | 1. 検索欄に「zzzz」と入力し Search を押す | 「No species match your search.」が表示され、件数は「Showing 0 of 12 species」 | `RQ-FT-SEARCH-SPECIES`, `RQ-UI-SPECIES-LIST-SCREEN` | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-TS-VIEW-SPECIES-DETAIL` | 詳細画面で全項目を見られること、一覧へ戻れること | 一覧で絞り込みをしている | 1. 一覧で種の行を押す 2. 「Back to results」を押す | 詳細に全項目が表示され、戻ると同じ絞り込みの一覧に戻る | `RQ-FT-VIEW-SPECIES-DETAIL`, `RQ-UI-SPECIES-DETAIL-SCREEN` | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-TS-CREATE-SPECIES` | 新しい種を登録できること | 見本データがある | 1. Add species を開く 2. 必須項目と任意項目を入力して Save を押す | 「Species saved.」の後、詳細画面に入力内容が表示され、一覧の件数が 13 になる | `RQ-FT-CREATE-SPECIES`, `RQ-UI-SPECIES-CREATE-SCREEN` | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-TS-VALIDATE-SPECIES-INPUT` | 空欄・範囲外の入力が保存されないこと | 登録画面を開いている | 1. 学名を空、平均寿命に 0、平均体重に -1 を入力して Save を押す | 保存されず、各項目の下にエラー文言が出る。入力内容は保持される | `RQ-FT-CREATE-SPECIES`, `RQ-UI-SPECIES-CREATE-SCREEN` | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-TS-UNIQUE-SCIENTIFIC-NAME` | 学名の重複が拒否されること | 学名「Panthera leo」が登録済み | 1. 登録画面で学名を「panthera LEO」として Save を押す | 保存されず、「This scientific name is already registered.」が学名の欄に出る | `RQ-FT-UNIQUE-SCIENTIFIC-NAME`, `RQ-FT-CREATE-SPECIES` | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-TS-UPDATE-SPECIES` | 種の情報を修正できること | 見本データがある | 1. Lion の詳細で Edit を押す 2. 説明を変更して Save を押す | 「Species saved.」の後、詳細に新しい説明が表示される | `RQ-FT-UPDATE-SPECIES`, `RQ-UI-SPECIES-EDIT-SCREEN` | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-TS-DELETE-SPECIES` | 種を確認の後に削除できること | 見本データがある | 1. 種の詳細で Delete を押し、確認ダイアログで取り消す 2. 再度 Delete を押し、確認する | 1. 種は残る 2. 「Species deleted.」が一覧に表示され、件数が 11 になる | `RQ-FT-DELETE-SPECIES`, `RQ-UI-SPECIES-DETAIL-SCREEN` | `RQ-BK-MAINTAIN-SPECIES-INFO` |
| `RQ-TS-UNKNOWN-SPECIES` | 存在しない種の URL で案内が出ること | 存在しない ID | 1. /species/99999 を開く | 「Species not found.」と一覧へのリンクが表示される | `RQ-UI-NOT-FOUND-SCREEN` | `RQ-BK-FIND-SPECIES-INFO` |
| `RQ-TS-ESCAPE-USER-INPUT` | 入力の HTML が表示されないこと | 見本データがある | 1. 登録画面で説明に「<b>bold</b>」を入力して保存する 2. 詳細を開く | 「<b>bold</b>」の文字がそのまま表示され、太字にならない | `RQ-NF-ESCAPE-USER-INPUT` | `RQ-BK-MAINTAIN-SPECIES-INFO` |
