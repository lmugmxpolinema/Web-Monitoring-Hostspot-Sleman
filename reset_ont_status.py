#!/usr/bin/env python3
"""
Script untuk reset status semua ONT ke ON
Berguna untuk testing sistem ping
"""

import json
import os

def reset_ont_status():
    """Reset semua status ONT ke ON"""
    try:
        # Baca file onts.json
        with open("onts.json", "r", encoding='utf-8') as f:
            onts = json.load(f)
        
        print(f"🔄 Reset status {len(onts)} ONT...")
        
        # Reset semua status ke ON
        for ont in onts:
            ont['status'] = "ON"
            ont['rto_count'] = 0
            print(f"✅ {ont.get('name', 'Unknown')} ({ont.get('ip', 'N/A')}) → ON")
        
        # Simpan kembali ke file
        with open("onts.json", "w", encoding='utf-8') as f:
            json.dump(onts, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Berhasil reset {len(onts)} ONT ke status ON")
        print("💾 File onts.json telah diperbarui")
        
        # Tampilkan statistik
        online_count = len([ont for ont in onts if ont['status'] == 'ON'])
        print(f"📊 Statistik: {online_count} ONLINE, 0 OFFLINE")
        
    except FileNotFoundError:
        print("❌ File onts.json tidak ditemukan!")
        print("💡 Pastikan file onts.json ada di direktori yang sama")
    except json.JSONDecodeError:
        print("❌ File onts.json tidak valid!")
        print("💡 Pastikan format JSON benar")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_current_status():
    """Tampilkan status ONT saat ini"""
    try:
        with open("onts.json", "r", encoding='utf-8') as f:
            onts = json.load(f)
        
        print("📋 STATUS ONT SAAT INI:")
        print("=" * 60)
        
        online_count = 0
        offline_count = 0
        
        for ont in onts[:10]:  # Tampilkan 10 pertama
            status = ont.get('status', 'Unknown')
            if status == 'ON':
                online_count += 1
                status_icon = "✅"
            else:
                offline_count += 1
                status_icon = "❌"
            
            print(f"{status_icon} {ont.get('name', 'Unknown')} ({ont.get('ip', 'N/A')}) → {status}")
        
        if len(onts) > 10:
            print(f"... dan {len(onts) - 10} ONT lainnya")
        
        print("=" * 60)
        print(f"📊 Total: {len(onts)} ONT")
        print(f"✅ Online: {online_count}")
        print(f"❌ Offline: {offline_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🔄 ONT STATUS RESET TOOL")
    print("=" * 40)
    
    # Tampilkan status saat ini
    show_current_status()
    
    print("\n" + "=" * 40)
    
    # Tanya user apakah ingin reset
    choice = input("Apakah Anda ingin reset semua status ke ON? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes', 'ya']:
        print("\n🔄 Memulai reset...")
        reset_ont_status()
    else:
        print("❌ Reset dibatalkan")
    
    print("\n💡 Langkah selanjutnya:")
    print("1. Jalankan sistem ping: python ping_check.py")
    print("2. Atau test ping manual: python test_ping_simple.py")
    print("3. Monitor di browser: http://localhost:5000")

if __name__ == "__main__":
    main()
