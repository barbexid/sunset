from datetime import datetime, timezone, timedelta
import json
from app.menus.util import pause, clear_screen, format_quota_byte, normalize_msisdn
from app.client.famplan import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn

WIDTH = 55

def show_family_info(api_key: str, tokens: dict):
    in_family_menu = True
    while in_family_menu:
        clear_screen()
        res = get_family_data(api_key, tokens)
        
        if not isinstance(res, dict) or not res.get("data"):
            print("❌ Gagal mengambil data Family Plan.")
            pause()
            return
        
        family_detail = res["data"]
        member_info = family_detail.get("member_info", {})
        plan_type = member_info.get("plan_type", "")
        
        if plan_type == "" or plan_type == "NO_ROLE":
            print("=" * WIDTH)
            print("Anda belum terdaftar sebagai anggota Family Plan.".center(WIDTH))
            print("=" * WIDTH)
            pause()
            return
        
        parent_msisdn = member_info.get("parent_msisdn", "N/A")
        members = member_info.get("members", [])
        empty_slots = [slot for slot in members if slot.get("msisdn") == ""]
        
        total_quota_byte = member_info.get("total_quota", 0)
        remaining_quota_byte = member_info.get("remaining_quota", 0)
        
        total_quota_human = format_quota_byte(total_quota_byte)
        remaining_quota_human = format_quota_byte(remaining_quota_byte)
        
        end_date_ts = member_info.get("end_date", 0)
        if end_date_ts > 0:
            end_date = datetime.fromtimestamp(end_date_ts).strftime("%d %b %Y")
        else:
            end_date = "N/A"
        
        clear_screen()
        print("=" * WIDTH)
        print("👨‍👩‍👧‍👦 Informasi Family Plan".center(WIDTH))
        print("=" * WIDTH)
        print(f"📌 Plan Type : {plan_type}")
        print(f"👑 Parent    : {parent_msisdn}")
        print(f"📊 Shared Kuota: {remaining_quota_human} / {total_quota_human}")
        print(f"📅 Aktif s.d : {end_date}")
        print(f"👥 Slot      : {len(members) - len(empty_slots)} / {len(members)} terisi")
        print("-" * WIDTH)
        print("👥 Daftar Anggota:")
        
        for idx, member in enumerate(members, start=1):
            msisdn = member.get("msisdn", "")
            if msisdn == "":
                formatted_msisdn = "<Slot Kosong>"
            else:
                formatted_msisdn = msisdn
                
            alias = member.get("alias", "N/A")
            member_type = "Parent" if member.get("member_type") == "PARENT" else "Member"
            
            quota_allocated_byte = member.get("usage", {}).get("quota_allocated", 0)
            quota_used_byte = member.get("usage", {}).get("quota_used", 0)
            
            quota_allocated_str = format_quota_byte(quota_allocated_byte)
            quota_used_str = format_quota_byte(quota_used_byte)
            
            print(f"  {idx:>2}. {formatted_msisdn:<15} ({alias}) - {member_type}")
            if msisdn != "":
                print(f"      📊 Usage: {quota_used_str} / {quota_allocated_str}")
        
        print("=" * WIDTH)
        print("Menu:")
        print(" 1. Ubah Anggota (Ganti Nomor di Slot Kosong)")
        print(" limit <Slot> <MB> : Set Limit Kuota (cth: limit 2 1024)")
        print(" del <Slot>        : Hapus Anggota (cth: del 3)")
        print("00. Kembali ke Menu Utama")
        print("=" * WIDTH)
        
        choice = input("Pilih opsi: ").strip()
        
        if choice == "1":
            slot_idx_str = input("Masukkan nomor slot: ").strip()
            target_msisdn = input("Masukkan nomor baru ( 08xx/628xx ): ").strip()
            target_msisdn = normalize_msisdn(target_msisdn)
            parent_alias = input("Masukkan alias Anda: ").strip()
            child_alias = input("Masukkan alias anggota baru: ").strip()
            
            try:
                slot_idx_int = int(slot_idx_str)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print("❌ Nomor slot tidak valid.")
                    pause()
                    continue
                
                if members[slot_idx_int - 1].get("msisdn") != "":
                    print("❌ Slot sudah terisi. Hapus dulu anggotanya.")
                    pause()
                    continue
                
                family_member_id = members[slot_idx_int - 1].get("family_member_id", "")
                slot_id = members[slot_idx_int - 1].get("slot_id", 0)
                
                print(f"\n⏳ Memvalidasi nomor {target_msisdn}...")
                validation_res = validate_msisdn(api_key, tokens, target_msisdn)
                
                if not isinstance(validation_res, dict) or validation_res.get("status", "").lower() != "success":
                    print(f"❌ Validasi gagal: {validation_res.get('message', 'Unknown Error')}")
                    pause()
                    continue
                    
                target_role = validation_res.get("data", {}).get("family_plan_role", "")
                if target_role != "NO_ROLE":
                    print(f"❌ Nomor sudah terdaftar di Family Plan lain (Role: {target_role}).")
                    pause()
                    continue

                confirm = input(f"Yakin menempatkan {target_msisdn} di slot {slot_idx_int}? (y/n): ").strip().lower()
                if confirm != "y":
                    print("Dibatalkan.")
                    pause()
                    continue
                
                change_res = change_member(
                    api_key, tokens, parent_alias, child_alias, slot_id, family_member_id, target_msisdn
                )
                
                if isinstance(change_res, dict) and change_res.get("status") == "SUCCESS":
                    print("✅ Anggota berhasil diubah/ditambahkan!")
                else:
                    print(f"❌ Gagal mengubah anggota: {change_res.get('message', 'Unknown Error')}")
                
            except ValueError:
                print("❌ Input tidak valid. Pastikan memasukkan angka.")
            pause()
            
        elif choice.startswith("del "):
            parts = choice.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("❌ Format salah. Contoh: del 3")
                pause()
                continue
                
            slot_idx_int = int(parts[1])
            if slot_idx_int < 1 or slot_idx_int > len(members):
                print("❌ Nomor slot tidak valid.")
                pause()
                continue
            
            member = members[slot_idx_int - 1]
            if member.get("msisdn") == "":
                print("❌ Slot sudah kosong.")
                pause()
                continue
            
            confirm = input(f"Yakin menghapus {member.get('msisdn')} dari slot {slot_idx_int}? (y/n): ").strip().lower()
            if confirm != "y":
                print("Dibatalkan.")
                pause()
                continue
            
            family_member_id = member.get("family_member_id", "")
            res_del = remove_member(api_key, tokens, family_member_id)
            
            if isinstance(res_del, dict) and res_del.get("status") == "SUCCESS":
                print("✅ Anggota berhasil dihapus.")
            else:
                print(f"❌ Gagal menghapus anggota: {res_del.get('message', 'Unknown Error')}")
            pause()
            
        elif choice.startswith("limit "):
            parts = choice.split()
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                print("❌ Format salah. Contoh: limit 2 1024")
                pause()
                continue
                
            slot_idx_int = int(parts[1])
            new_quota_mb_int = int(parts[2])
            
            if slot_idx_int < 1 or slot_idx_int > len(members):
                print("❌ Nomor slot tidak valid.")
                pause()
                continue
            
            member = members[slot_idx_int - 1]
            if member.get("msisdn") == "":
                print("❌ Slot kosong, tidak bisa set kuota.")
                pause()
                continue
            
            family_member_id = member.get("family_member_id", "")
            original_allocation_byte = member.get("usage", {}).get("quota_allocated", 0)
            new_allocation_byte = new_quota_mb_int * 1024 * 1024
            
            res_limit = set_quota_limit(
                api_key, tokens, original_allocation_byte, new_allocation_byte, family_member_id
            )
            
            if isinstance(res_limit, dict) and res_limit.get("status") == "SUCCESS":
                print("✅ Limit kuota berhasil diatur.")
            else:
                print(f"❌ Gagal set limit: {res_limit.get('message', 'Unknown Error')}")
            pause()
            
        elif choice == "00":
            in_family_menu = False
            return
        else:
            print("❌ Pilihan tidak valid.")
            pause()