import json
import sys

import requests
from datetime import datetime, timezone, timedelta
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package, get_addons, get_package_details, send_api_request, unsubscribe
from app.client.ciam import get_auth_code
from app.service.bookmark import BookmarkInstance
from app.client.purchase.redeem import settlement_bounty, settlement_loyalty, bounty_allotment
from app.menus.util import clear_screen, pause, display_html
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.purchase import purchase_n_times, purchase_n_times_by_option_code
from app.menus.util import format_quota_byte, normalize_msisdn
from app.service.decoy import DecoyInstance

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    active_user = AuthInstance.active_user
    subscription_type = active_user.get("subscription_type", "")
    
    clear_screen()
    package = get_package(api_key, tokens, package_option_code)
    if not package:
        print("❌ Gagal memuat detail paket.")
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package.get("package_option", {}).get("tnc", ""))
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name","")
    family_name = package.get("package_family", {}).get("name","")
    variant_name = package.get("package_detail_variant", "").get("name","")
    
    title = f"{family_name} - {variant_name} - {option_name}".strip()
    if title == "-": title = option_name
    
    family_code = package.get("package_family", {}).get("package_family_code","")
    parent_code = package.get("package_addon", {}).get("parent_code","")
    if parent_code == "": parent_code = "N/A"
    
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    
    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]
    
    print("=" * 55)
    print(f"📦 {title}".center(55))
    print("=" * 55)
    print(f"💰 Harga       : Rp {price:,}")
    print(f"⏳ Masa Aktif  : {validity}")
    print(f"💎 Point       : {package['package_option']['point']}")
    print(f"📌 Plan Type   : {package['package_family']['plan_type']}")
    print(f"💳 Payment For : {payment_for}")
    print("-" * 55)
    print(f"📁 Family Code : {family_code}")
    print(f"📁 Parent Code : {parent_code}")
    print("-" * 55)
    
    print("🎁 Benefits:")
    benefits = package.get("package_option", {}).get("benefits", [])
    if benefits and isinstance(benefits, list):
        for benefit in benefits:
            name = benefit.get("name", "")
            data_type = benefit.get('data_type', 'N/A')
            total = benefit.get('total', 0)
            is_unlimited = benefit.get("is_unlimited", False)
            
            if total == 0 and not is_unlimited:
                continue

            short_name = name
            if "Daily Quota of Productivity Apps" in name:
                short_name = "Kuota Harian Aplikasi Produktivitas"
            elif "Call to XL" in name:
                short_name = "Nelp ke XL / AXIS / Smartfren"
            elif "Call to All" in name:
                short_name = "Telp ke Semua Operator"
            elif "Main Quota" in name and "Nasional" not in name:
                short_name = "Kuota Utama"
            elif "Local Quota" in name:
                short_name = "Kuota Lokal"

            if is_unlimited:
                kuota_str = "∞ Unlimited"
            elif data_type == "VOICE":
                kuota_str = f"{round(total/60)} Menit"
            elif data_type == "TEXT":
                kuota_str = f"{total} SMS"
            elif data_type == "DATA" or total > 1_000_000: 
                kuota_str = f"{format_quota_byte(total)}"
            else:
                kuota_str = f"{total}"

            print(f"  - {short_name:<36}:{kuota_str:>12}")
    
    print("-" * 55)
    
    addons_data = get_addons(api_key, tokens, package_option_code)
    if isinstance(addons_data, dict):
        bonuses = addons_data.get("bonuses", [])
        upsell = addons_data.get("upsell", [])
        
        if bonuses or upsell:
            print("🎉 Addons / Bonus Tersedia:")
            for b in bonuses:
                print(f"  - [Bonus] {b.get('name')}")
            for u in upsell:
                print(f"  - [Upsell] {u.get('name')}")
            print("-" * 55)

    print(f"📜 SnK MyXL:")
    print(f"{detail}")
    print("=" * 55)
    
    in_package_detail_menu = True
    while in_package_detail_menu:
        print("Pilih Metode Pembelian:")
        print(" 1. Beli dengan Pulsa")
        print(" 2. Beli dengan E-Wallet")
        print(" 3. Bayar dengan QRIS")
        print(" 4. Pulsa + Decoy")
        print(" 5. Pulsa + Decoy V2")
        print(" 6. QRIS + Decoy (+1K)")
        print(" 7. QRIS + Decoy V2")
        print(" 8. Pulsa N kali")
        
        if payment_for == "REDEEM_VOUCHER":
            print(" B. Ambil sebagai bonus")
            print("BA. Kirim bonus")
            print(" L. Beli dengan Poin")
        
        if option_order != -1:
            print(" 0. Tambah ke Bookmark")
        print("00. Kembali")

        choice = input("Pilihan: ")
        if choice == "00":
            return False
        elif choice == "0" and option_order != -1:
            # Add to bookmark
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                print("Paket berhasil ditambahkan ke bookmark.")
            else:
                print("Paket sudah ada di bookmark.")
            pause()
            continue
        
        elif choice == '1':
            settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True
            )
            input("Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '2':
            show_multipayment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '3':
            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '4':
            # Balance with Decoy            
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                False,
                overwrite_amount=overwrite_amount,
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        False,
                        overwrite_amount=valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("Purchase successful!")
            else:
                print("Purchase successful!")
            pause()
            return True
        elif choice == '5':
            # Balance with Decoy v2 (use token confirmation from decoy)
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=1
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=-1
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("Purchase successful!")
            else:
                print("Purchase successful!")
            pause()
            return True
        elif choice == '6':
            # QRIS decoy + Rpx
            decoy = DecoyInstance.get_decoy("qris")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            print("-"*55)
            print(f"Harga Paket Utama: Rp {price}")
            print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print("Silahkan sesuaikan amount (trial & error, 0 = malformed)")
            print("-"*55)

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '7':
            # QRIS decoy + Rp0
            decoy = DecoyInstance.get_decoy("qris0")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            print("-"*55)
            print(f"Harga Paket Utama: Rp {price}")
            print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print("Silahkan sesuaikan amount (trial & error, 0 = malformed)")
            print("-"*55)

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '8':
            #Pulsa N kali
            use_decoy_for_n_times = input("Use decoy package? (y/n): ").strip().lower() == 'y'
            n_times_str = input("Enter number of times to purchase (e.g., 3): ").strip()

            delay_seconds_str = input("Enter delay between purchases in seconds (e.g., 25): ").strip()
            if not delay_seconds_str.isdigit():
                delay_seconds_str = "0"

            try:
                n_times = int(n_times_str)
                if n_times < 1:
                    raise ValueError("Number must be at least 1.")
            except ValueError:
                print("Invalid number entered. Please enter a valid integer.")
                pause()
                continue
            purchase_n_times_by_option_code(
                n_times,
                option_code=package_option_code,
                use_decoy=use_decoy_for_n_times,
                delay_seconds=int(delay_seconds_str),
                pause_on_success=False,
                token_confirmation_idx=1
            )
        elif choice.lower() == 'b':
            settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice.lower() == 'ba':
            destination_msisdn = input("Masukkan nomor tujuan bonus ( 08xx / 628xx ): ").strip()
            destination_msisdn = normalize_msisdn(destination_msisdn)
            bounty_allotment(
                api_key=api_key,
                tokens=tokens,
                ts_to_sign=ts_to_sign,
                destination_msisdn=destination_msisdn,
                item_name=option_name,
                item_code=package_option_code,
                token_confirmation=token_confirmation,
            )
            pause()
            return True
        elif choice.lower() == 'l':
            settlement_loyalty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        else:
            print("Purchase cancelled.")
            return False
    pause()
    #sys.exit(0)
    return False 


def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("❌ No active user tokens found.")
        pause()
        return None
    
    print("Mengambil data family...")
    data = get_family(
        api_key,
        tokens,
        family_code,
        is_enterprise,
        migration_type
    )
    
    if not data:
        print(f"❌ Failed to load family data untuk code: {family_code}")
        pause()
        return None
        
    price_currency = "Rp"
    rc_bonus_type = data.get("package_family", {}).get("rc_bonus_type", "")
    if rc_bonus_type == "MYREWARDS":
        price_currency = "Poin"
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        
        packages = [] 
        
        family_name = data.get("package_family", {}).get("name", "N/A")
        family_type = data.get("package_family", {}).get("package_family_type", "N/A")
        package_variants = data.get("package_variants", [])
        
        print("=" * 55)
        print(f"🛍️  Family: {family_name}".center(55))
        print(f"🆔 Code  : {family_code}")
        print(f"📦 Type  : {family_type} | Variants: {len(package_variants)}")
        print("=" * 55)
        
        option_number = 1
        variant_number = 1
        
        for variant in package_variants:
            variant_name = variant.get("name", "N/A")
            variant_code = variant.get("package_variant_code", "N/A")
            
            print(f" 📂 Variant {variant_number}: {variant_name}")
            print(f"    Code: {variant_code}")
            print("-" * 55)
            
            for option in variant.get("package_options", []):
                option_name = option.get("name", "N/A")
                price = option.get("price", 0)
                
                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": price,
                    "code": option.get("package_option_code", ""),
                    "option_order": option.get("order", 0)
                })

                print(f"  {option_number:>2}. {option_name:<30} : {price_currency} {price:>9,}")
                option_number += 1
            
            variant_number += 1
            print("-" * 55)
            
        print("=" * 55)
        print(" 00. Kembali ke menu utama")
        print("=" * 55)
        
        pkg_choice = input("Pilih paket (nomor): ").strip()
        
        if pkg_choice == "00":
            in_package_menu = False
            return None
        
        if not pkg_choice.isdigit():
            print("❌ Input tidak valid. Silakan masukan nomor paket.")
            pause()
            continue
        
        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        
        if not selected_pkg:
            print("❌ Paket tidak ditemukan. Silakan masukan nomor yang benar.")
            pause()
            continue
        
        show_package_details(
            api_key,
            tokens,
            selected_pkg["code"],
            is_enterprise,
            option_order=selected_pkg["option_order"],
        )
        
    return packages


def fetch_my_packages():
    in_my_packages_menu = True
    while in_my_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        if not tokens:
            print("No active user tokens found.")
            pause()
            return None

        id_token = tokens.get("id_token")
        path = "api/v8/packages/quota-details"
        payload = {"is_enterprise": False, "lang": "en", "family_member_id": ""}

        print("Fetching my packages...")
        res = send_api_request(api_key, path, payload, id_token, "POST")
        
        if not isinstance(res, dict) or res.get("status") != "SUCCESS":
            print("Failed to fetch packages")
            pause()
            return None

        data = res.get("data") or {}
        quotas = data.get("quotas") or []
        if not quotas:
            print("No active packages.")
            pause()
            return None

        clear_screen()
        print("=" * 55)
        print("====================== My Packages ====================".center(55))
        print("=" * 55)
        
        my_packages = []
        num = 1
        for quota in quotas:
            quota_code = quota.get("quota_code", "")
            group_code = quota.get("group_code", "")
            quota_name = quota.get("name", "N/A")
            
            expired_at = quota.get("expired_at", 0)
            is_unlimited_exp = quota.get("is_expiration_unlimited", False)
            
            if is_unlimited_exp:
                expired_str = "Unlimited"
            elif expired_at > 0:
                wib = timezone(timedelta(hours=7))
                dt = datetime.fromtimestamp(expired_at, tz=timezone.utc).astimezone(wib)
                expired_str = dt.strftime("%d %b %Y %H:%M WIB")
            else:
                expired_str = "N/A"

            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")
            
            benefit_infos = []
            benefits = quota.get("benefits", [])
            if benefits:
                for benefit in benefits:
                    name = benefit.get("name", "")
                    data_type = benefit.get("data_type", "N/A")
                    
                    remaining = benefit.get("remaining", 0)
                    total = benefit.get("total", 0)
                    is_unlimited = benefit.get("is_unlimited", False)
                    
                    if total == 0 and not is_unlimited:
                        continue

                    short_name = name.strip() if name and name.strip() else "Kuota"
                    
                    if "Daily Quota of Productivity Apps" in name:
                        short_name = "Kuota Harian Aplikasi Produktivitas"
                    elif "Call to XL" in name:
                        short_name = "Nelp ke XL / AXIS / Smartfren"
                    elif "Call to All" in name:
                        short_name = "Telp ke Semua Operator"
                    elif "Main Quota" in name and "Nasional" not in name:
                        short_name = "Kuota Utama"
                    elif "Local Quota" in name:
                        short_name = "Kuota Lokal"

                    value_str = ""
                    if is_unlimited:
                        value_str = "∞ Unlimited"
                    elif data_type == "DATA":
                        value_str = f"{format_quota_byte(remaining)} / {format_quota_byte(total)}"
                    elif data_type == "VOICE":
                        if remaining == total:
                            value_str = f"{round(total/60)} Menit"
                        else:
                            value_str = f"{round(remaining/60)} / {round(total/60)} Menit"
                    elif data_type == "TEXT":
                        value_str = f"{remaining} / {total} SMS"
                    else:
                        value_str = f"{remaining} / {total}"
                        
                    benefit_infos.append(f"  - {short_name:<30}: {value_str}")

            family_code = "N/A"
            package_details = get_package(api_key, tokens, quota_code, silent=True)
            if isinstance(package_details, dict) and isinstance(package_details.get("package_family"), dict):
                family_code = package_details["package_family"].get("package_family_code", "N/A")

     #       print("=" * 55)
            print(f"📦 Package {num}: {quota_name}")
            print(f"📅 Quota Reset : {expired_str}") 
            print("-" * 55)
            print("🎁 Benefits:")
            if benefit_infos:
                for bi in benefit_infos:
                    print(bi)
            
            print("-" * 55)
            print(f"🔑 Quota Code : {quota_code}")
            print(f"👥 Group Code : {group_code}")
            print(f"📁 Family Code: {family_code}")
            print("=" * 55)

            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
            })
            num += 1

        print("Input package number to view detail.")
        print("Input del <package number> to unsubscribe from a package.")
        print("Input 00 to return to main menu.")
        choice = input("Choice: ").strip()

        if choice == "00":
            in_my_packages_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(my_packages):
            selected_pkg = next((pkg for pkg in my_packages if pkg["number"] == int(choice)), None)
            if not selected_pkg:
                print("Paket tidak ditemukan.")
                pause()
                continue
            _ = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)
            continue

        if choice.startswith("del "):
            parts = choice.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("Format: del <nomor paket>")
                pause()
                continue

            del_number = int(parts[1])
            del_pkg = next((pkg for pkg in my_packages if pkg["number"] == del_number), None)

            if not del_pkg:
                print(f"Paket nomor {del_number} tidak ditemukan.")
                pause()
                continue

            confirm = input(f"Yakin unsubscribe paket {del_number}. {del_pkg['name']}? (y/n): ").strip().lower()

            if confirm == "y":
                print(f"Unsubscribing {del_pkg['name']}...")
                success = unsubscribe(
                    api_key,
                    tokens,
                    del_pkg["quota_code"],
                    del_pkg["product_subscription_type"],
                    del_pkg["product_domain"],
                )
                print("✅ Unsubscribe sukses." if success else "❌ Unsubscribe gagal.")
            else:
                print("Dibatalkan.")
            pause()
            continue

        print("Pilihan tidak valid.")
        pause()