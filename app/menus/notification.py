from app.menus.util import clear_screen, pause
from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance

WIDTH = 55

def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
     #   print("Mengambil notifikasi...")
        
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        notifications_res = dashboard_segments(api_key, tokens)
        
        if not isinstance(notifications_res, dict):
            print("❌ Gagal terhubung ke server.")
            pause()
            return
            
        notifications = notifications_res.get("data", {}).get("notification", {}).get("data", [])
        
        if not notifications:
            print("=" * WIDTH)
            print("Belum ada notifikasi.".center(WIDTH))
            print("=" * WIDTH)
            pause()
            return
        
        print("=" * WIDTH)
        print("🔔 Pusat Notifikasi".center(WIDTH))
        print("=" * WIDTH)
        
        unread_count = 0
        for idx, notif in enumerate(notifications):
            is_read = notif.get("is_read", False)
            full_message = notif.get("full_message", "")
            brief_message = notif.get("brief_message", "")
            time_str = notif.get("timestamp", "")
            
            if time_str and "T" in time_str:
                try:
                    time_str = time_str.split(".")[0].replace("T", " ")
                except Exception:
                    pass
            
            if not is_read:
                status_icon = "🔴 UNREAD"
                unread_count += 1
            else:
                status_icon = "🟢 READ"

            print(f" {idx + 1:>2}. [{status_icon}] {brief_message}")
            print(f"      🕒 {time_str}")
            print(f"      📝 {full_message}")
            print("-" * WIDTH)
            
        print(f" Total: {len(notifications)} | Unread: {unread_count}")
        print("=" * WIDTH)
        print(" 1. Tandai Semua Dibaca")
        print("00. Kembali ke Menu Utama")
        print("=" * WIDTH)
        
        choice = input("Pilih opsi: ").strip()
        
        if choice == "1":
            if unread_count == 0:
                print("✅ Semua notifikasi sudah dibaca.")
                pause()
                continue
                
            print("⏳ Menandai semua notifikasi sebagai dibaca...")
            success_count = 0
            for notif in notifications:
                if notif.get("is_read", False):
                    continue
                    
                notification_id = notif.get("notification_id")
                if notification_id:
                    detail = get_notification_detail(api_key, tokens, notification_id)
                    if detail:
                        success_count += 1
                        
            print(f"✅ {success_count} notifikasi berhasil ditandai dibaca.")
            pause()
            
        elif choice == "00":
            in_notification_menu = False
        else:
            print("❌ Pilihan tidak valid.")
            pause()