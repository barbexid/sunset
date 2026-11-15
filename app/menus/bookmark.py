from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.service.bookmark import BookmarkInstance
from app.client.engsel import get_family

WIDTH = 55

def show_bookmark_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        print("=" * WIDTH)
        print("🔖 Daftar Bookmark Paket".center(WIDTH))
        print("=" * WIDTH)
        
        bookmarks = BookmarkInstance.get_bookmarks()
        if not bookmarks:
            print("Belum ada paket yang disimpan.".center(WIDTH))
            print("=" * WIDTH)
            pause()
            return None
        
        for idx, bm in enumerate(bookmarks):
            family_name = bm.get('family_name', 'N/A')
            variant_name = bm.get('variant_name', 'N/A')
            option_name = bm.get('option_name', 'N/A')
            
            print(f" {idx + 1:>2}. {family_name}")
            print(f"      └─ {variant_name} - {option_name}")
            print("-" * WIDTH)
            
        print(" 00. Kembali ke Menu Utama")
        print("000. Hapus Bookmark")
        print("=" * WIDTH)
        
        choice = input("Pilih bookmark (nomor): ").strip()
        
        if choice == "00":
            in_bookmark_menu = False
            return None
            
        elif choice == "000":
            del_choice = input("Masukan nomor bookmark yang ingin dihapus: ").strip()
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                del_bm = bookmarks[int(del_choice) - 1]
                BookmarkInstance.remove_bookmark(
                    del_bm["family_code"],
                    del_bm["is_enterprise"],
                    del_bm["variant_name"],
                    del_bm["order"],
                )
                print("✅ Bookmark dihapus.")
            else:
                print("❌ Input tidak valid.")
            pause()
            continue
            
        if choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            family_code = selected_bm.get("family_code")
            is_enterprise = selected_bm.get("is_enterprise", False)
            
            print(f"\nMengambil data terbaru untuk paket ini...")
            
            try:
                family_data = get_family(api_key, tokens, family_code, is_enterprise)
            except Exception as e:
                print(f"❌ Error: {e}")
                family_data = None
                
            if not family_data:
                print("❌ Gagal mengambil data family. Paket mungkin sudah tidak tersedia.")
                print("   Silakan hapus bookmark ini (menu 000).")
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
                print("❌ Detail paket tidak ditemukan. Kemungkinan paket sudah expired.")
                pause()
            
        else:
            print("❌ Input tidak valid. Silakan coba lagi.")
            pause()