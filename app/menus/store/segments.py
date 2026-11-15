import json
from app.client.store.segments import get_segments
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.menus.package import show_package_details

WIDTH = 55

def show_store_segments_menu(is_enterprise: bool = False):
    in_store_segments_menu = True
    while in_store_segments_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        print("Fetching store segments...")
        segments_res = get_segments(api_key, tokens, is_enterprise)
        if not segments_res:
            print("No segments found.")
            in_store_segments_menu = False
            continue
        
        segments = segments_res.get("data", {}).get("store_segments", [])
        
        clear_screen()
        print("=" * WIDTH)
        print("🎯 Store Segments (Promo Spesial)".center(WIDTH))
        print("=" * WIDTH)
        
        packages = {}
        for i, segment in enumerate(segments):
            name = segment.get("title", "N/A")
            banners = segment.get("banners", [])
            
            letter = chr(65 + i)
            print(f"📌 {letter}. {name}")
            print("-" * WIDTH)
            
            for j, banner in enumerate(banners):
                discounted_price = banner.get("discounted_price", "N/A")
                title = banner.get("title", "N/A")
                validity = banner.get("validity", "N/A")
                family_name = banner.get("family_name", "N/A")
                
                action_param = banner.get("action_param", "")
                action_type = banner.get("action_type", "")
                
                packages[f"{letter.lower()}{j + 1}"] = {
                    "action_param": action_param,
                    "action_type": action_type
                }
                
                print(f"  [{letter}{j + 1}] {family_name} - {title}")
                print(f"       💰 Rp {discounted_price} | ⏳ {validity}")
                print("-" * WIDTH)
            
        print(" 00. Kembali ke Menu Utama")
        print("=" * WIDTH)
        choice = input("Pilih kode paket (contoh: A1, B2): ").strip().lower()
        
        if choice == "00":
            in_store_segments_menu = False
            continue
        
        selected_pkg = packages.get(choice.upper()) or packages.get(choice)
        if not selected_pkg:
            print("❌ Kode tidak valid.")
            pause()
            continue
        
        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]
        
        if action_type == "PDP":
            _ = show_package_details(api_key, tokens, action_param, is_enterprise)
        else:
            print("=" * WIDTH)
            print(f"⚠️ Action Type '{action_type}' belum didukung.")
            pause()