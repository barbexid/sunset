import json
import os

from app.client.engsel import get_family, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, format_quota_byte, pause, display_html
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem

WIDTH = 55

def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        
        hot_packages = []
        file_path = "hot_data/hot.json"
        
        if not os.path.exists(file_path):
            print(f"❌ File data tidak ditemukan: {file_path}")
            pause()
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Format JSON di {file_path} rusak/kosong.")
            pause()
            return None
            
        if not hot_packages:
            print("Belum ada data paket HOT.")
            pause()
            return None

        print("=" * WIDTH)
        print("🔥 Daftar Paket HOT 🔥".center(WIDTH))
        print("=" * WIDTH)
        
        for idx, p in enumerate(hot_packages):
            family = p.get('family_name', 'N/A')
            variant = p.get('variant_name', 'N/A')
            option = p.get('option_name', 'N/A')
            
            print(f"  {idx + 1:>2}. {family} - {variant}")
            print(f"      └─ {option}")
            print("-" * WIDTH)
            
        print(" 00. Kembali ke menu utama")
        print("=" * WIDTH)
        
        choice = input("Pilih paket (nomor): ").strip()
        if choice == "00":
            in_hot_menu = False
            return None
            
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm.get("family_code", "")
            is_enterprise = selected_bm.get("is_enterprise", False)
            
            print("\n Mengambil data family...")
            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print("❌ Gagal mengambil data family.")
                pause()
                continue
            
            package_variants = family_data.get("package_variants", [])
            option_code = None
            
            for variant in package_variants:
                if variant.get("name") == selected_bm.get("variant_name"):
                    for option in variant.get("package_options", []):
                        if option.get("order") == selected_bm.get("order"):
                            option_code = option.get("package_option_code")
                            break
            
            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)            
            else:
                print("❌ Gagal menemukan opsi paket (mungkin sudah tidak tersedia).")
                pause()
        else:
            print("❌ Input tidak valid. Silakan coba lagi.")
            pause()


def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        
        hot_packages = []
        file_path = "hot_data/hot2.json"
        
        if not os.path.exists(file_path):
            print(f"❌ File data tidak ditemukan: {file_path}")
            pause()
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Format JSON di {file_path} rusak/kosong.")
            pause()
            return None
            
        if not hot_packages:
            print("Belum ada data paket HOT-2.")
            pause()
            return None

        print("=" * WIDTH)
        print("🔥 Daftar Paket HOT-2 (Bundling) 🔥".center(WIDTH))
        print("=" * WIDTH)
        
        for idx, p in enumerate(hot_packages):
            name = p.get('name', 'N/A')
            price = p.get('price', 'N/A')
            detail = p.get('detail', '')
            
            print(f"  {idx + 1:>2}. {name}")
            print(f"      💰 Harga: {price}")
            if detail:
                print(f"      📝 Info : {detail}")
            print("-" * WIDTH)
            
        print(" 00. Kembali ke menu utama")
        print("=" * WIDTH)
        
        choice = input("Pilih paket (nomor): ").strip()
        if choice == "00":
            in_hot_menu = False
            return None
            
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            
            if not packages:
                print("❌ Paket tidak tersedia (list packages kosong).")
                pause()
                continue
            
            print("\n Mengambil data detail paket bundling...")
            payment_items = []
            main_package_detail = {}
            
            valid_packages = True
            for package in packages:
                try:
                    package_detail = get_package_details(
                        api_key,
                        tokens,
                        package.get("family_code", ""),
                        package.get("variant_code", ""),
                        package.get("order", 0),
                        package.get("is_enterprise", False),
                        package.get("migration_type", ""),
                    )
                except Exception as e:
                    print(f"❌ Exception: {e}")
                    package_detail = None
                
                if package == packages[0]:
                    main_package_detail = package_detail
                
                if not package_detail:
                    print(f"❌ Gagal mengambil detail paket untuk {package.get('family_code', '')}.")
                    valid_packages = False
                    break
                
                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )
            
            if not valid_packages:
                pause()
                continue
                
            # Tampilkan Detail Paket Utama
            clear_screen()
            print("=" * WIDTH)
            print(f"📦 Bundling: {selected_package.get('name', 'N/A')}".center(WIDTH))
            print(f"💰 Harga   : {selected_package.get('price', 'N/A')}")
            print("=" * WIDTH)
            
            price = main_package_detail["package_option"]["price"]
            detail_html = display_html(main_package_detail["package_option"]["tnc"])
            validity = main_package_detail["package_option"]["validity"]

            option_name = main_package_detail.get("package_option", {}).get("name","")
            family_name = main_package_detail.get("package_family", {}).get("name","")
            variant_name = main_package_detail.get("package_detail_variant", "").get("name","")
            
            title = f"{family_name} - {variant_name} - {option_name}".strip()
            
            family_code = main_package_detail.get("package_family", {}).get("package_family_code","")
            parent_code = main_package_detail.get("package_addon", {}).get("parent_code","")
            if parent_code == "": parent_code = "N/A"
            
            payment_for = selected_package.get("payment_for", main_package_detail["package_family"].get("payment_for", "BUY_PACKAGE"))
                
            print(f"📄 Nama       : {title}")
            print(f"⏳ Masa Aktif : {validity}")
            print(f"💳 Payment For: {payment_for}")
            print(f"📁 Family Code: {family_code}")
            print(f"📁 Parent Code: {parent_code}")
            print("-" * WIDTH)
            
            print("🎁 Benefits:")
            benefits = main_package_detail["package_option"]["benefits"]
            if benefits and isinstance(benefits, list):
                for benefit in benefits:
                    name = benefit.get('name', '')
                    data_type = benefit['data_type']
                    total = benefit['total']
                    
                    kuota_str = ""
                    if benefit.get("is_unlimited", False):
                        kuota_str = "∞ Unlimited"
                    elif data_type == "VOICE" and total > 0:
                        kuota_str = f"{total/60:.0f} menit"
                    elif data_type == "TEXT" and total > 0:
                        kuota_str = f"{total} SMS"
                    elif data_type == "DATA" and total > 0:
                        kuota_str = format_quota_byte(int(total))
                    elif data_type not in ["DATA", "VOICE", "TEXT"] and total > 0:
                        kuota_str = format_quota_byte(int(total))
                    
                    if kuota_str:
                        print(f"  - {name:<34} : {kuota_str}")

            print("-" * WIDTH)
            print(f"📜 SnK MyXL:\n{detail_html}")
            print("=" * WIDTH)
            
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)
            
            # Menu Pembayaran
            in_payment_menu = True
            while in_payment_menu:
                print("Pilih Metode Pembelian:")
                print(" 1. Beli dengan Pulsa")
                print(" 2. Beli dengan E-Wallet")
                print(" 3. Bayar dengan QRIS")
                print("00. Kembali ke menu sebelumnya")
                
                input_method = input("Pilih metode (nomor): ").strip()
                if input_method == "1":
                    if overwrite_amount == -1:
                        print(f"\n⚠️ Pastikan sisa balance KURANG DARI Rp{payment_items[-1]['item_price']:,}!!!")
                        balance_answer = input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ").strip().lower()
                        if balance_answer != "y":
                            print("Pembelian dibatalkan oleh user.")
                            pause()
                            continue

                    settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount=overwrite_amount,
                        token_confirmation_idx=token_confirmation_idx,
                        amount_idx=amount_idx,
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_hot_menu = False
                elif input_method == "2":
                    show_multipayment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_hot_menu = False
                elif input_method == "3":
                    show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_hot_menu = False
                elif input_method == "00":
                    in_payment_menu = False
                else:
                    print("❌ Metode tidak valid. Silakan coba lagi.")
                    pause()
        else:
            print("❌ Input tidak valid. Silakan coba lagi.")
            pause()