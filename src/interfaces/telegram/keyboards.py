from __future__ import annotations

import hashlib

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_idempotency_key(approval_id: str, decision: str) -> str:
    digest = hashlib.sha256(f"{approval_id}:{decision}".encode("utf-8")).hexdigest()[:12]
    return f"tg-{decision[:1]}-{digest}"


def encode_approval_callback(approval_id: str, decision: str) -> str:
    return f"ap:{decision}:{approval_id}:{build_idempotency_key(approval_id, decision)}"


def decode_approval_callback(data: str) -> dict[str, str]:
    prefix, decision, approval_id, idempotency_key = data.split(":", 3)
    if prefix != "ap":
        raise ValueError("unsupported callback payload")
    return {
        "decision": decision,
        "approval_id": approval_id,
        "idempotency_key": idempotency_key,
    }


def build_approval_keyboard(approval_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Onayla", callback_data=encode_approval_callback(approval_id, "approved")),
                InlineKeyboardButton("Reddet", callback_data=encode_approval_callback(approval_id, "rejected")),
            ],
            [
                InlineKeyboardButton("Revize / Iptal", callback_data=encode_approval_callback(approval_id, "cancelled")),
            ],
        ]
    )
