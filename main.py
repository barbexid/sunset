from dotenv import load_dotenv

from app.service.git import check_for_updates
load_dotenv()

import sys, json
from datetime import datetime
from app.menus.util import clear_screen, pause, mask_phone_number, normalize_msisdn
from app.client.famplan import validate_msisdn
from app.menus.payment import show_transaction_history
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.client.registration import dukcapil, validate_puk
from app.service.auth import AuthInstance
from app.service.sentry import enter_sentry_mode
from app.service.profile import get_profile_data, invalidate_profile_cache

WIDTH = 55

def show_main_menu(profile, is_cached):
    clear_screen()
    print("=" * WIDTH)
    ts = profile.get("balance_expired_at") or 0
    expired_at_dt = datetime.fromtimestamp(ts).strftime("%d %b %Y") if ts else "N/A"
    
    cache_status = "(Cached)" if is_cached else "(Fresh)"
    
    masked_number = mask_phone_number(profile['number'])
    
    print(f"Nomor: {masked_number} | Type: {profile['subscription_type']}".center(WIDTH))
    print(f"Pulsa: Rp {profile['balance']} | Kuota: {profile.get('total_quota', '0 B')}".center(WIDTH))
    print(f"Aktif sampai: {expired_at_dt}".center(WIDTH)) # {cache_status}
    print(f"{profile['point_info']}".center(WIDTH))
    print("=" * WIDTH)
    print("Menu:")
    print(" 1. Login/Ganti akun")
    print(" 2. Lihat Paket Saya")
    print(" 3. Beli Paket 🔥 HOT 🔥")
    print(" 4. Beli Paket 🔥 HOT-2 🔥")
    print(" 5. Beli Paket Berdasarkan Option Code")
    print(" 6. Beli Paket Berdasarkan Family Code")
    print(" 7. Beli Semua Paket di Family Code (loop)")
    print(" 8. Riwayat Transaksi")
    print(" 9. Family Plan/Akrab Organizer")
    print("10. Circle")
    print("11. Store Segments")
    print("12. Store Family List")
    print("13. Store Packages")
    print("14. Redemables")
    print(" R. Registrasi Kartu")
    print(" P. Validasi PUK")
    print(" V. Validate msisdn")
    print(" N. Notifikasi")
    print(" F. Refresh Data (Pulsa & Kuota)")
 #   print(" S. Sentry Mode")
    print("00. Bookmark Paket")
    print("99. Tutup aplikasi")
    print("-------------------------------------------------------")


def main():
    while True:
        active_user = AuthInstance.get_active_user()

        if active_user is not None:
            profile, is_cached = get_profile_data(active_user)
            show_main_menu(profile, is_cached)

            choice = input("Pilih menu: ")

            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected = show_account_menu()
                if selected:
                    invalidate_profile_cache() 
                    if AuthInstance.set_active_user(selected):
                        get_profile_data(AuthInstance.get_active_user(), force=True)
                    else:
                        print("Gagal berganti akun. Kemungkinan token expired atau jaringan bermasalah.")
                        pause()
                else:
                    print("No user selected.")
                continue
            
            elif choice.lower() == "f":
                print("Memaksa refresh data...")
                get_profile_data(active_user, force=True)
                continue

            elif choice == "2":
                fetch_my_packages()
                invalidate_profile_cache()
                continue
                
            elif choice == "3":
                show_hot_menu()
                invalidate_profile_cache()
                continue
            elif choice == "4":
                show_hot_menu2()
                invalidate_profile_cache()
                continue
            elif choice == "5":
                oc = input("Enter option code (or '99' to cancel): ").strip()
                if oc == "99":
                    continue
                show_package_details(AuthInstance.api_key, active_user["tokens"], oc, False)
                invalidate_profile_cache()
                continue
            elif choice == "6":
                fc = input("Enter family code (or '99' to cancel): ").strip()
                if fc == "99":
                    continue
                get_packages_by_family(fc)
                invalidate_profile_cache()
                continue
            elif choice == "7":
                fc = input("Enter family code (or '99' to cancel): ").strip()
                if fc == "99":
                    continue
                try:
                    start_from = int(input("Start from option (default 1): ") or "1")
                except ValueError:
                    start_from = 1
                use_decoy = input("Use decoy package? (y/n): ").lower() == "y"
                pause_ok = input("Pause on success? (y/n): ").lower() == "y"
                try:
                    delay = int(input("Delay seconds (0 = none): ") or "0")
                except ValueError:
                    delay = 0
                purchase_by_family(fc, use_decoy, pause_ok, delay, start_from)
                invalidate_profile_cache()
                continue
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "11":
                is_ent = input("Is enterprise store? (y/n): ").lower() == "y"
                show_store_segments_menu(is_ent)
            elif choice == "12":
                is_ent = input("Is enterprise? (y/n): ").lower() == "y"
                show_family_list_menu(profile["subscription_type"], is_ent)
            elif choice == "13":
                is_ent = input("Is enterprise? (y/n): ").lower() == "y"
                show_store_packages_menu(profile["subscription_type"], is_ent)
            elif choice == "14":
                is_ent = input("Is enterprise? (y/n): ").lower() == "y"
                show_redeemables_menu(is_ent)
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                print("Exiting.")
                sys.exit(0)
            elif choice.lower() == "r":
                clear_screen()
                print("=" * WIDTH)
                print("Registrasi Kartu XL/Axis".center(WIDTH))
                print("=" * WIDTH)
                
                msisdn = input("Enter msisdn (08xx / 628xx): ").strip()
                msisdn = normalize_msisdn(msisdn)
                if not msisdn.startswith("628") or not msisdn.isdigit() or len(msisdn) < 10 or len(msisdn) > 14:
                    print("Format MSISDN salah!")
                    pause()
                    continue

                nik = input("Enter NIK (16 digit): ").strip()
                if not nik.isdigit() or len(nik) != 16:
                    print("NIK harus berupa 16 digit angka!")
                    pause()
                    continue
                    
                kk = input("Enter KK (16 digit): ").strip()
                if not kk.isdigit() or len(kk) != 16:
                    print("KK harus berupa 16 digit angka!")
                    pause()
                    continue
                
                print("\nMemproses registrasi...")
                res = dukcapil(AuthInstance.api_key, msisdn, kk, nik)
                
                if isinstance(res, dict) and res.get("status") == "SUCCESS":
                    print("\n✅ Registrasi Berhasil!")
                    print("Data Dukcapil cocok dengan data kartu.")
                    if "data" in res and "message" in res["data"]:
                        print(f"Info: {res['data']['message']}")
                else:
                    print("\n❌ Registrasi Gagal!")
                    if isinstance(res, dict):
                        error_msg = res.get("message", "Unknown Error")
                        code = res.get("code", "N/A")
                        print(f"Kode: {code} | Pesan: {error_msg}")
                    else:
                        print("Error: Gagal terhubung ke server.")
                pause()
            elif choice.lower() == "p":
                msisdn = input("Enter msisdn (08xx / 628xx): ").strip()
                msisdn = normalize_msisdn(msisdn)
                puk = input("Enter PUK (8 digit): ").strip()
                
                if not puk.isdigit() or len(puk) != 8:
                    print("PUK harus 8 digit angka!")
                    pause()
                    continue
                    
                print("\nMemvalidasi PUK...")
                res = validate_puk(AuthInstance.api_key, msisdn, puk)
                
                if isinstance(res, dict) and res.get("status") == "SUCCESS":
                    print("\n✅ PUK Valid!")
                else:
                    print(f"\n❌ PUK Tidak Valid: {res.get('message', 'Error')}")
                pause()
            elif choice.lower() == "v":
                msisdn = input("Enter msisdn (08xx / 628xx): ").strip()
                msisdn = normalize_msisdn(msisdn)
                res = validate_msisdn(AuthInstance.api_key, active_user["tokens"], msisdn)
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice.lower() == "s":
                enter_sentry_mode()
            else:
                print("Invalid choice.")
                pause()
        else:
            selected = show_account_menu()
            if selected:
                AuthInstance.set_active_user(selected)
            else:
                print("No user selected.")


if __name__ == "__main__":
    try:
        print("Checking for updates...")
        if check_for_updates():
            pause()
        main()
    except KeyboardInterrupt:
        print("\nExiting.")