"""Callback data constants shared between keyboards and handlers."""
from __future__ import annotations

# Main menu
CB_ACCOUNTS = "menu:accounts"
CB_ADD_ACCOUNT = "menu:add_account"
CB_CLEAN_FOLLOWING = "menu:clean_following"
CB_CLEAN_FOLLOWERS = "menu:clean_followers"
CB_STATS = "menu:stats"
CB_SETTINGS = "menu:settings"
CB_HELP = "menu:help"
CB_OWNER_PANEL = "menu:owner_panel"
CB_BACK_TO_MENU = "menu:back"

# Account management
CB_ACCOUNT_SELECT = "acct:select:"
CB_ACCOUNT_ACTIONS = "acct:actions:"
CB_ACCOUNT_INFO = "acct:info:"
CB_ACCOUNT_DELETE = "acct:delete:"
CB_ACCOUNT_DELETE_CONFIRM = "acct:delete_confirm:"
CB_ACCOUNT_SWITCH = "acct:switch:"
CB_ACCOUNT_LOGOUT = "acct:logout:"
CB_ACCOUNT_BACK = "acct:back"

# Login flow
CB_LOGIN_QR = "login:qr"
CB_LOGIN_CREDENTIALS = "login:credentials"
CB_LOGIN_CANCEL = "login:cancel"
CB_LOGIN_REFRESH_QR = "login:refresh_qr"

# Operations
CB_OP_PLAN_FOLLOWING = "op:plan:following"
CB_OP_PLAN_FOLLOWERS = "op:plan:followers"
CB_OP_START = "op:start:"
CB_OP_STOP = "op:stop:"
CB_OP_CANCEL_PLAN = "op:cancel_plan"

# Owner panel
CB_OWNER_STATS = "owner:stats"
CB_OWNER_USERS = "owner:users"
CB_OWNER_ACCOUNTS = "owner:accounts"
CB_OWNER_BLOCKED = "owner:blocked"
CB_OWNER_BROADCAST = "owner:broadcast"
CB_OWNER_LOGS = "owner:logs"
CB_OWNER_SETTINGS = "owner:settings"
