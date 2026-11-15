import time
from app.client.engsel import get_balance, get_tiering_info, get_total_quota_byte
from app.menus.util import format_tier, format_quota_byte
from app.service.auth import AuthInstance

_PROFILE_CACHE = {"data": None, "at": 0}
_PROFILE_TTL = 300  # 5 Menit (300 detik)

def get_profile_data(active_user, force=False):
    now = time.time()
    
    if _PROFILE_CACHE["data"] and str(_PROFILE_CACHE["data"].get("number")) != str(active_user["number"]):
        force = True

    if not force and _PROFILE_CACHE["data"] and (now - _PROFILE_CACHE["at"]) < _PROFILE_TTL:
        return _PROFILE_CACHE["data"], True  # True = Data Cache
        
    api_key = AuthInstance.api_key
    id_token = active_user["tokens"]["id_token"]
    
    balance = get_balance(api_key, id_token) or {}
    
    tiering = None
    if active_user["subscription_type"] == "PREPAID":
        tiering = get_tiering_info(api_key, active_user["tokens"])
        
    if tiering is None and _PROFILE_CACHE["data"]:
        print("Gagal ambil tier, pakai data sebelumnya.")
        return _PROFILE_CACHE["data"], True
        
    if tiering is None:
        tiering = {}

    total_quota_byte = get_total_quota_byte(api_key, active_user["tokens"])
    
    balance_remaining = balance.get("remaining", 0)
    balance_expired_at = balance.get("expired_at", 0)
    
    tier_id = tiering.get("tier", 0)
    current_point = tiering.get("current_point", 0)
    spending = tiering.get("current_spending", 0)
    
    if current_point == 0 and tier_id == 0:
        point_info = "Points: N/A | Tier: N/A"
    else:
        point_info = (
            f"Points: {current_point} | Tier: {format_tier(tier_id)} | "
            f"Spend: Rp {spending:,}"
        )

    profile = {
        "number": active_user["number"],
        "subscriber_id": active_user["subscriber_id"],
        "subscription_type": active_user["subscription_type"],
        "balance": balance_remaining,
        "balance_expired_at": balance_expired_at,
        "total_quota": format_quota_byte(total_quota_byte),
        "point_info": point_info,
    }
    
    _PROFILE_CACHE["data"] = profile
    _PROFILE_CACHE["at"] = now
    return profile, False  # False = Data Fresh

def invalidate_profile_cache():
    _PROFILE_CACHE["at"] = 0
    _PROFILE_CACHE["data"] = None
