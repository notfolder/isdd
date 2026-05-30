"""
パスワード処理モジュール。

要件ID: RQ-NF-LOW-SECURITY-POLICY
設計ID: DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
要件概要: 認証情報を平文で保持しないこと。
設計概要: SHA-256でハッシュ化し、比較時はハッシュ同士で検証する。
呼び出し先設計ID: なし
呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER, DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
"""

from __future__ import annotations

import hashlib


def hash_password(raw_password: str) -> str:
    """
    パスワードをハッシュ化する。

    Args:
        raw_password (str): 平文パスワード。

    Returns:
        str: ハッシュ値。

    要件ID: RQ-NF-LOW-SECURITY-POLICY
    設計ID: DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
    要件概要: パスワードの平文保存を防ぐこと。
    設計概要: SHA-256でハッシュ化しDBへ保存する。
    呼び出し先設計ID: なし
    呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER, DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT
    """
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """
    パスワード一致を検証する。

    Args:
        raw_password (str): 入力パスワード。
        hashed_password (str): 保存済みハッシュ。

    Returns:
        bool: 一致時True。

    要件ID: RQ-FT-AUTHENTICATE-USER
    設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
    要件概要: ログイン時にIDとパスワードで認証すること。
    設計概要: 入力値をハッシュ化して保存値と比較し認証結果を返す。
    呼び出し先設計ID: DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
    呼び出し元設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER
    """
    return hash_password(raw_password) == hashed_password
