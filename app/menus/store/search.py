from app.client.store.search import get_family_list, get_store_packages
from app.menus.package import get_packages_by_family, show_package_details
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance

WIDTH = 55

def show_family_list_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    in_family_list_menu = True
    while in_family_list_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        print("Fetching family list...")
        family_list_res = get_family_list(api_key, tokens, subs_type, is_enterprise)
        if not family_list_res:
            print("No family list found.")
            in_family_list_menu = False
            continue
        
        family_list = family_list_res.get("data", {}).get("results", [])
        
        clear_screen()
        print("=" * WIDTH)
        print("🏪 Daftar Family (Katalog)".center(WIDTH))
        print("=" * WIDTH)
        
        for i, family in enumerate(family_list):
            family_name = family.get("label", "N/A")
            family_code = family.get("id", "N/A")
            
            print(f"  {i + 1:>2}. {family_name}")
            print(f"      └─ ID: {family_code}")
            print("-" * WIDTH)
        
        print(" 00. Kembali ke Menu Utama")
        print("=" * WIDTH)
        choice = input("Pilih nomor family: ").strip()
        
        if choice == "00":
            in_family_list_menu = False
            return
        
        if choice.isdigit() and 1 <= int(choice) <= len(family_list):
            selected_family = family_list[int(choice) - 1]
            family_code = selected_family.get("id", "")
            family_name = selected_family.get("label", "N/A")
            
            print(f"\n Mengambil paket untuk family: {family_name}...")
            get_packages_by_family(family_code)
        else:
            print("❌ Input tidak valid.")
            pause()
    
    pause()

def show_store_packages_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    print("Fetching store packages...")
    store_packages_res = get_store_packages(api_key, tokens, subs_type, is_enterprise)
    if not store_packages_res:
        print("❌ No store packages found.")
        pause()
        return
        
    store_packages = store_packages_res.get("data", {}).get("results_price_only", [])
    if not store_packages:
        print("❌ Katalog paket kosong.")
        pause()
        return

    page = 1
    items_per_page = 15
    total_pages = (len(store_packages) + items_per_page - 1) // items_per_page
    
    in_store_packages_menu = True
    while in_store_packages_menu:
        clear_screen()
        print("=" * WIDTH)
        print(f"🏪 Store Packages (Hal {page}/{total_pages})".center(WIDTH))
        print("=" * WIDTH)
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = store_packages[start_idx:end_idx]
        
        packages = {}
        for i, package in enumerate(page_items):
            title = package.get("title", "N/A")
            original_price = package.get("original_price", 0)
            discounted_price = package.get("discounted_price", 0)
            
            price = discounted_price if discounted_price > 0 else original_price
            validity = package.get("validity", "N/A")
            family_name = package.get("family_name", "N/A")
            
            action_type = package.get("action_type", "")
            action_param = package.get("action_param", "")
            
            global_num = start_idx + i + 1
            packages[str(global_num)] = {
                "action_type": action_type,
                "action_param": action_param
            }
            
            print(f"  {global_num:>3}. {title}")
            print(f"       🏷️  {family_name} | ⏳ {validity}")
            print(f"       💰 Rp {price:>10,}".replace(",", "."))
            print("-" * WIDTH)
        
        print(f" [n] Next | [p] Prev | [00] Kembali")
        print("=" * WIDTH)
        choice = input("Pilih nomor paket / navigasi: ").strip().lower()
        
        if choice == "00":
            in_store_packages_menu = False
            return
        
        if choice == "n" and page < total_pages:
            page += 1
            continue
        elif choice == "p" and page > 1:
            page -= 1
            continue
            
        if choice in packages:
            selected_package = packages[choice]
            action_type = selected_package["action_type"]
            action_param = selected_package["action_param"]
            
            if action_type == "PDP":
                _ = show_package_details(api_key, tokens, action_param, is_enterprise)
            else:
                print("=" * WIDTH)
                print(f"⚠️ Action Type '{action_type}' belum didukung.")
                pause()
        else:
            print("❌ Pilihan tidak valid.")
            pause()