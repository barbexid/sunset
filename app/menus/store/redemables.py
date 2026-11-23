from app.client.store.redeemables import get_redeemables
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.package import show_package_details, get_packages_by_family
from datetime import datetime

WIDTH = 55

def show_redeemables_menu(is_enterprise: bool = False):
    in_redeemables_menu = True
    while in_redeemables_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        print("Mengambil katalog redeemables...")
        redeemables_res = get_redeemables(api_key, tokens, is_enterprise)
        
        if not isinstance(redeemables_res, dict) or redeemables_res.get("status") != "SUCCESS":
            print("❌ Gagal mengambil data redeemables.")
            pause()
            in_redeemables_menu = False
            continue
        
        categories = redeemables_res.get("data", {}).get("categories", [])
        
        clear_screen()
        print("=" * WIDTH)
        print("🎁 Katalog Penukaran Bonus / Redeemables".center(WIDTH))
        print("=" * WIDTH)
        
        packages = {}
        for i, category in enumerate(categories):
            category_name = category.get("category_name", "N/A")
            category_code = category.get("category_code", "N/A")
            redemables = category.get("redeemables", [])
            
            letter = chr(65 + i)  # A, B, C...
            print(f"📂 {letter}. {category_name}")
            print("-" * WIDTH)
            
            if len(redemables) == 0:
                print("   (Tidak ada bonus di kategori ini)")
                print("-" * WIDTH)
                continue
            
            for j, redemable in enumerate(redemables):
                name = redemable.get("name", "N/A")
                valid_until = redemable.get("valid_until", 0)
                
                if valid_until > 0:
                    try:
                        valid_until_date = datetime.fromtimestamp(valid_until).strftime("%d %b %Y")
                    except Exception:
                        valid_until_date = "N/A"
                else:
                    valid_until_date = "N/A"
                
                action_param = redemable.get("action_param", "")
                action_type = redemable.get("action_type", "")
                
                packages[f"{letter.lower()}{j + 1}"] = {
                    "action_param": action_param,
                    "action_type": action_type
                }
                
                print(f"  [{letter}{j + 1}] {name}")
                print(f"       ⏳ Valid s.d: {valid_until_date}")
                print("-" * WIDTH)
                
        print(" 00. Kembali ke Menu Utama")
        print("=" * WIDTH)
        print("Pilih kode bonus (contoh: A1, B2): ")
        
        choice = input().strip().lower()
        if choice == "00":
            in_redeemables_menu = False
            continue
            
        selected_pkg = packages.get(choice.upper()) or packages.get(choice)
        if not selected_pkg:
            print("❌ Kode tidak valid.")
            pause()
            continue
            
        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]
        
        if action_type == "PLP":
            get_packages_by_family(action_param, is_enterprise, "")
            
        elif action_type == "PDP":
            show_package_details(api_key, tokens, action_param, is_enterprise)
            
        elif action_type in ["LOYALTY", "MYPOINT_LANDING", "WEBVIEW", "URL"]:
            clear_screen()
            print("=" * WIDTH)
            print(f"📌 Fitur: {action_type}")
            print(f"🔗 Param: {action_param}")
            print("-" * WIDTH)
            print("⚠️ Menu ini merupakan halaman Web (Webview) di aplikasi MyXL.")
            print("   Biasanya digunakan untuk menukar Poin atau Reward.")
            print("   Aplikasi CLI saat ini belum bisa menampilkan halaman Web.")
            print("")
            print("👉 Silakan buka aplikasi MyXL resmi untuk mengakses menu ini.")
            print("=" * WIDTH)
            pause()
            
        else:
            print("=" * WIDTH)
            print(f"⚠️ Action Type '{action_type}' belum didukung.")
            print(f"   Param: {action_param}")
            pause()
