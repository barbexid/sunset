from datetime import datetime, timezone, timedelta
import json
from app.menus.package import get_packages_by_family, show_package_details
from app.menus.util import pause, clear_screen, format_quota_byte, normalize_msisdn
from app.client.circle import (
    get_group_data, get_group_members, create_circle, validate_circle_member,
    invite_circle_member, remove_circle_member, accept_circle_invitation,
    spending_tracker, get_bonus_data,
)
from app.service.auth import AuthInstance
from app.client.encrypt import decrypt_circle_msisdn

WIDTH = 55

def show_circle_creation(api_key: str, tokens: dict):
    clear_screen()
    print("=" * WIDTH)
    print("Buat Circle Baru".center(WIDTH))
    print("=" * WIDTH)
    
    parent_name = input("Nama Anda (Parent): ").strip()
    group_name = input("Nama Circle: ").strip()
    member_msisdn = input("Nomor anggota ( 08xx / 628xx ): ").strip()
    member_msisdn = normalize_msisdn(member_msisdn)
    member_name = input("Nama anggota: ").strip()
    
    print("\n⏳ Membuat Circle...")
    create_res = create_circle(api_key, tokens, parent_name, group_name, member_msisdn, member_name)
    
    if isinstance(create_res, dict) and create_res.get("status") == "SUCCESS":
        print("✅ Circle berhasil dibuat!")
    else:
        print(f"❌ Gagal membuat Circle: {create_res.get('message', 'Unknown Error')}")
    pause()

def show_bonus_list(api_key: str, tokens: dict, parent_subs_id: str, family_id: str):
    in_circle_bonus_menu = True
    while in_circle_bonus_menu:
        clear_screen()
        print("⏳ Mengambil data bonus...")
        bonus_data = get_bonus_data(api_key, tokens, parent_subs_id, family_id)
        
        if not isinstance(bonus_data, dict) or bonus_data.get("status") != "SUCCESS":
            print("❌ Gagal mengambil data bonus.")
            pause()
            return
        
        bonus_list = bonus_data.get("data", {}).get("bonuses", [])
        if not bonus_list:
            print("Belum ada data bonus.")
            pause()
            return
        
        print("=" * WIDTH)
        print("🎁 Circle Bonus List".center(WIDTH))
        print("=" * WIDTH)
        
        for idx, bonus in enumerate(bonus_list, start=1):
            bonus_name = bonus.get("name", "N/A")
            bonus_type = bonus.get("bonus_type", "N/A")
            action_type = bonus.get("action_type", "N/A")
            
            print(f"  {idx:>2}. {bonus_name} (Tipe: {bonus_type})")
            print("-" * WIDTH)
            
        print(" 00. Kembali")
        print("=" * WIDTH)
        
        choice = input("Pilih bonus (nomor): ").strip()
        if choice == "00":
            in_circle_bonus_menu = False
            continue
            
        if choice.isdigit() and 1 <= int(choice) <= len(bonus_list):
            selected_bonus = bonus_list[int(choice) - 1]
            action_type = selected_bonus.get("action_type", "N/A")
            action_param = selected_bonus.get("action_param", "N/A")
            
            if action_type == "PLP":
                get_packages_by_family(action_param)
            elif action_type == "PDP":
                show_package_details(api_key, tokens, action_param, False)
            else:
                print(f"⚠️ Action Type '{action_type}' belum didukung.")
                pause()
        else:
            print("❌ Pilihan tidak valid.")
            pause()

def show_circle_info(api_key: str, tokens: dict):
    in_circle_menu = True
    user = AuthInstance.get_active_user()
    my_msisdn = user.get("number", "") if user else ""

    while in_circle_menu:
        clear_screen()
    #    print("⏳ Mengambil data Circle...")
        group_res = get_group_data(api_key, tokens)
        
        if not isinstance(group_res, dict) or group_res.get("status") != "SUCCESS":
            print("❌ Gagal mengambil data Circle.")
            pause()
            return
        
        group_data = group_res.get("data", {})        
        group_id = group_data.get("group_id", "")

        if group_id == "":
            print("=" * WIDTH)
            print("Anda belum tergabung dalam Circle.".center(WIDTH))
            print("=" * WIDTH)
            
            create_new = input("Apakah Anda ingin membuat Circle baru? (y/n): ").strip().lower()
            if create_new == "y":
                show_circle_creation(api_key, tokens)
                continue
            else:
                pause()
                return
        
        group_status = group_data.get("group_status", "N/A")
        if group_status == "BLOCKED":
            print("❌ Circle ini sedang diblokir.")
            pause()
            return
        
        group_name = group_data.get("group_name", "N/A")
        owner_name = group_data.get("owner_name", "N/A")
        
        members_res = get_group_members(api_key, tokens, group_id)
        if not isinstance(members_res, dict) or members_res.get("status") != "SUCCESS":
            print("❌ Gagal mengambil data anggota Circle.")
            pause()
            return
        
        members_data = members_res.get("data", {})
        members = members_data.get("members", [])
        if not members:
            print("❌ Tidak ada anggota di Circle ini.")
            pause()
            return
        
        parent_member_id = ""
        parent_subs_id = ""
        parent_msisdn = ""
        
        for member in members:
            if member.get("member_role", "") == "PARENT":
                parent_member_id = member.get("member_id", "")
                parent_subs_id = member.get("subscriber_number", "")
                enc_msisdn = member.get("msisdn", "")
                parent_msisdn = decrypt_circle_msisdn(api_key, enc_msisdn)
        
        package = members_data.get("package", {})
        package_name = package.get("name", "N/A")
        benefit = package.get("benefit", {})
        allocation_byte = benefit.get("allocation", 0)
        remaining_byte = benefit.get("remaining", 0)
        
        formatted_alloc = format_quota_byte(allocation_byte)
        formatted_remain = format_quota_byte(remaining_byte)
        
        spending_res = spending_tracker(api_key, tokens, parent_subs_id, group_id)
        if isinstance(spending_res, dict) and spending_res.get("status") == "SUCCESS":
            spending_data = spending_res.get("data", {})
            spend = spending_data.get("spend", 0)
            target = spending_data.get("target", 0)
            spending_str = f"Rp {spend:,} / Rp {target:,}"
        else:
            spending_str = "N/A"
        
        clear_screen()
        print("=" * WIDTH)
        print("👥 Informasi Circle".center(WIDTH))
        print("=" * WIDTH)
        print(f"📌 Nama     : {group_name} ({group_status})")
        print(f"👑 Owner    : {owner_name} ({parent_msisdn})")
        print(f"📦 Paket    : {package_name}")
        print(f"📊 Sisa Kuota: {formatted_remain} / {formatted_alloc}")
        print(f"💸 Spending : {spending_str}")
        print("-" * WIDTH)
        print("👥 Daftar Anggota:")
        
        for idx, member in enumerate(members, start=1):
            enc_msisdn = member.get("msisdn", "")
            msisdn = decrypt_circle_msisdn(api_key, enc_msisdn)
            if not msisdn:
                msisdn = "<No Number>"
            
            member_role = member.get("member_role", "N/A")
            member_name = member.get("member_name", "N/A")
            member_status = member.get("status", "N/A")
            
            me_mark = "(Anda)" if str(msisdn) == str(my_msisdn) else ""
            member_type = "Parent" if member_role == "PARENT" else "Member"
            
            member_alloc = member.get("allocation", 0)
            member_remain = member.get("remaining", 0)
            member_used = max(0, member_alloc - member_remain)
            
            print(f"  {idx:>2}. {msisdn} ({member_name}) - {member_type} {me_mark}")
            print(f"      Status: {member_status} | Usage: {format_quota_byte(member_used)} / {format_quota_byte(member_alloc)}")
        
        print("=" * WIDTH)
        print("Menu:")
        print(" 1. Undang Anggota Baru")
        print(" 2. Lihat Bonus Circle")
        print(" del <nomor> : Hapus Anggota")
        print(" acc <nomor> : Terima Undangan Anggota")
        print("00. Kembali ke Menu Utama")
        print("=" * WIDTH)
        
        choice = input("Pilih opsi: ").strip()
        
        if choice == "00":
            in_circle_menu = False
            continue
            
        elif choice == "1":
            msisdn_to_invite = input("Masukkan nomor yang mau diundang: ").strip()
            msisdn_to_invite = normalize_msisdn(msisdn_to_invite)
            print(f"⏳ Memvalidasi {msisdn_to_invite}...")
            
            validate_res = validate_circle_member(api_key, tokens, msisdn_to_invite)
            if isinstance(validate_res, dict) and validate_res.get("status") == "SUCCESS":
                if validate_res.get("data", {}).get("response_code", "") != "200-2001":
                    print(f"❌ Tidak bisa mengundang: {validate_res.get('data', {}).get('message', 'Unknown error')}")
                    pause()
                    continue
            
            member_name = input("Masukkan nama anggota: ").strip()
            print("⏳ Mengirim undangan...")
            
            invite_res = invite_circle_member(api_key, tokens, msisdn_to_invite, member_name, group_id, parent_member_id)
            if isinstance(invite_res, dict) and invite_res.get("status") == "SUCCESS":
                print(f"✅ Undangan berhasil dikirim ke {msisdn_to_invite}.")
            else:
                print(f"❌ Gagal mengundang: {invite_res.get('message', 'Unknown Error')}")
            pause()
            
        elif choice == "2":
            show_bonus_list(api_key, tokens, parent_subs_id, group_id)
            
        elif choice.startswith("del "):
            parts = choice.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("❌ Format: del <nomor>")
                pause()
                continue
                
            member_num = int(parts[1])
            if member_num < 1 or member_num > len(members):
                print("❌ Nomor tidak valid.")
                pause()
                continue
                
            member_to_remove = members[member_num - 1]
            if member_to_remove.get("member_role", "") == "PARENT":
                print("❌ Tidak bisa menghapus Parent.")
                pause()
                continue
                
            if len(members) == 2:
                print("❌ Tidak bisa menghapus anggota terakhir.")
                pause()
                continue
            
            msisdn_to_remove = decrypt_circle_msisdn(api_key, member_to_remove.get("msisdn", ""))
            confirm = input(f"Yakin menghapus {msisdn_to_remove}? (y/n): ").strip().lower()
            if confirm != "y":
                print("Dibatalkan.")
                pause()
                continue
            
            member_id = member_to_remove.get("member_id", "")
            remove_res = remove_circle_member(api_key, tokens, member_id, group_id, parent_member_id, False)
            
            if isinstance(remove_res, dict) and remove_res.get("status") == "SUCCESS":
                print(f"✅ {msisdn_to_remove} berhasil dihapus.")
            else:
                print(f"❌ Gagal menghapus: {remove_res.get('message', 'Unknown Error')}")
            pause()
            
        elif choice.startswith("acc "):
            parts = choice.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("❌ Format: acc <nomor>")
                pause()
                continue
                
            member_num = int(parts[1])
            if member_num < 1 or member_num > len(members):
                print("❌ Nomor tidak valid.")
                pause()
                continue
                
            member_to_accept = members[member_num - 1]
            if member_to_accept.get("status", "") != "INVITED":
                print("❌ Anggota ini tidak dalam status INVITED.")
                pause()
                continue
                
            member_id = member_to_accept.get("member_id", "")
            msisdn_to_accept = decrypt_circle_msisdn(api_key, member_to_accept.get("msisdn", ""))
            confirm = input(f"Terima undangan untuk {msisdn_to_accept}? (y/n): ").strip().lower()
            if confirm != "y":
                print("Dibatalkan.")
                pause()
                continue
                
            accept_res = accept_circle_invitation(api_key, tokens, group_id, member_id)
            if isinstance(accept_res, dict) and accept_res.get("status") == "SUCCESS":
                print(f"✅ Undangan {msisdn_to_accept} diterima.")
            else:
                print(f"❌ Gagal menerima undangan: {accept_res.get('message', 'Unknown Error')}")
            pause()
        else:
            print("❌ Pilihan tidak valid.")
            pause()