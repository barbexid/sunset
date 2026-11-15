from app.client.ciam import get_otp, submit_otp
from app.menus.util import clear_screen, pause, normalize_msisdn
from app.service.auth import AuthInstance


def show_login_menu():
    clear_screen()
    print("-------------------------------------------------------")
    print("Login ke MyXL")
    print("-------------------------------------------------------")
    print("1. Request OTP")
    print("2. Submit OTP")
    print("99. Tutup aplikasi")
    print("-------------------------------------------------------")


def login_prompt(api_key: str):
    clear_screen()
    print("-------------------------------------------------------")
    print("Login ke MyXL")
    print("-------------------------------------------------------")
    print("Masukan nomor XL, ( 08xx / 628xx / +628xx ):")

    phone_number = input("Nomor: ").strip()
    phone_number = normalize_msisdn(phone_number)

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print("Nomor tidak valid.")
        return None, None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            print("Gagal mengirim OTP. Nomor mungkin tidak terdaftar / API down.")
            return None, None

        print("OTP Berhasil dikirim ke nomor Anda.")
        try_count = 5
        while try_count > 0:
            print(f"Sisa percobaan: {try_count}")
            otp = input("Masukkan OTP: ").strip()
            if not otp.isdigit() or len(otp) != 6:
                print("OTP harus 6 digit angka.")
                continue

            tokens = submit_otp(api_key, "SMS", phone_number, otp)
            if not tokens:
                print("OTP salah.")
                try_count -= 1
                continue

            print("Berhasil login!")
            return phone_number, tokens["refresh_token"]

        print("Gagal login setelah beberapa percobaan.")
        return None, None
    except Exception as e:
        print(f"Gagal login: {e}")
        return None, None


def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()

    in_account_menu = True
    add_user = False

    while in_account_menu:
        clear_screen()
        if active_user is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print("Gagal menambah akun.")
                pause()
                add_user = False
                continue

            try:
                num_int = int(number)
            except ValueError:
                print(f"Nomor tidak valid: {number}")
                pause()
                add_user = False
                continue

            if AuthInstance.add_refresh_token(num_int, refresh_token) is False:
                print("Gagal menambahkan akun.")
                pause()
                add_user = False
                continue

            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            add_user = False
            continue

        print("Akun Tersimpan:")
        if not users:
            print("Tidak ada akun tersimpan.")

        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            marker = "✅ Aktif" if is_active else ""
            num_str = str(user.get("number", ""))
            num_str = num_str + " " * (14 - len(num_str))
            sub_type = user.get("subscription_type", "").center(12)
            print(f"{idx + 1}. {num_str} [{sub_type}] {marker}")

        print("-" * 55)
        print("0: Tambah Akun")
        print("del <nomor urut> : Hapus akun")
        print("00: Kembali ke menu utama")
        print("-" * 55)
        input_str = input("Pilihan: ").strip()

        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None

        if input_str == "0":
            add_user = True
            continue

        if input_str.isdigit() and 1 <= int(input_str) <= len(users):
            return users[int(input_str) - 1]["number"]

        if input_str.startswith("del "):
            parts = input_str.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("Format: del <nomor urut>")
                pause()
                continue

            del_idx = int(parts[1])
            if not (1 <= del_idx <= len(users)):
                print("Nomor urut tidak valid.")
                pause()
                continue

            target = users[del_idx - 1]
            if active_user and target["number"] == active_user["number"]:
                print("Tidak bisa hapus akun aktif.")
                pause()
                continue

            confirm = input(f"Hapus akun {target['number']}? (y/n): ").strip().lower()
            if confirm == "y":
                AuthInstance.remove_refresh_token(target["number"])
                users = AuthInstance.refresh_tokens
                active_user = AuthInstance.get_active_user()
                print("Akun dihapus.")
            else:
                print("Dibatalkan.")
            pause()
            continue

        print("Input tidak valid.")
        pause()