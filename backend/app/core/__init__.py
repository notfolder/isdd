# coreパッケージ初期化
#
# 要件トレーサビリティ:
#   要件ID: RQ-NF-SECURITY-PASSWORD, RQ-NF-SECURITY-ROLE
#   設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD, DS-FN-VERIFY-JWT-NF-SECURITY-ROLE
#   要件概要: セキュリティ基盤パッケージ
#   設計概要: bcryptハッシュとJWT処理を提供するcoreパッケージ
#   呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
#   呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
