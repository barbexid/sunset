from datetime import datetime, timezone, timedelta
from app.client.engsel import get_transaction_history
from app.menus.util import clear_screen, pause

def show_transaction_history(api_key, tokens):
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()
        print("=" * 55)
        print("================== Riwayat Transaksi ==================".center(55))
        print("=" * 55)

        data = None
        history = []
        try:
            data = get_transaction_history(api_key, tokens)
            if isinstance(data, dict):
                history = data.get("list", [])
        except Exception as e:
            print(f"❌ Gagal mengambil riwayat transaksi: {e}")
            history = []
        
        if not history:
            print("Belum ada riwayat transaksi.")
        else:
            for idx, trx in enumerate(history, start=1):
                formatted_time = trx.get("formated_date", "").strip()
                if not formatted_time:
                    transaction_timestamp = trx.get("timestamp", 0)
                    if transaction_timestamp > 0:
                        dt = datetime.fromtimestamp(transaction_timestamp, tz=timezone.utc)
                        formatted_time = dt.strftime("%d %B %Y | %H:%M WIB")
                    else:
                        formatted_time = "N/A"

                title = trx.get("title", "N/A")
                price = trx.get("price", "N/A")
                
                if price.startswith("IDR "):
                    try:
                        raw_price = int(price.replace("IDR ", "").replace(",", ""))
                        price = f"Rp {raw_price:,}".replace(",", ".")
                    except ValueError:
                        pass

                status = trx.get("status", "N/A")
                payment_status = trx.get("payment_status", "N/A")
                payment_method = trx.get("payment_method_label", "N/A")

                icon_status = "✅" if status == "SUCCESS" else "❌"
                if "SUCCESS" in str(payment_status):
                    icon_pay = "✅"
                elif "PENDING" in str(payment_status):
                    icon_pay = "⏳"
                else:
                    icon_pay = "❌"

                print(f"{idx}. {title}")
                print(f"   💰 Harga    : {price}")
                print(f"   📅 Tanggal  : {formatted_time}")
                print(f"   💳 Metode   : {payment_method}")
                print(f"   📌 Status   : {icon_status} {status}")
                print(f"   🏦 Payment  : {icon_pay} {payment_status}")
                print("-" * 55)

        print("=" * 55)
        print(" 0. 🔄 Refresh Data")
        print("00. Kembali ke Menu Utama")
        print("=" * 55)
        
        choice = input("Pilih opsi: ").strip()
        if choice == "0":
            continue
        elif choice == "00":
            in_transaction_menu = False
        else:
            print("Opsi tidak valid. Silakan coba lagi.")
            pause()