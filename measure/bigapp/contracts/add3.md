
## 依頼 3 で足す接点（社員の状態）

- `POST /employees/set_status`（入力欄 `employee_no`、`status`）で、社員の状態を変える。`status` の値は `active`（在籍）、`leave`（休職中）、`retired`（退職）。成功したら 200 か 302、値が正しくないときや社員が見つからないときは 400。総務の担当者だけができる。
- `GET /employees.json` の `status` には、休職中の社員は `leave` と出す。
- `POST /employees/retire` はこれまでどおり使える。
