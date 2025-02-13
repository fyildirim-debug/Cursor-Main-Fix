import os
import sys
import json
import uuid
import time
import random
import winreg
import subprocess
import psutil
import threading
from datetime import datetime
from pathlib import Path
import ctypes
from colorama import init, Fore, Back, Style

# Colorama'yı başlat
init()

# Dönen karakter animasyonu için karakterler
SPINNER_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
spinner_running = False

def spinner_animation():
    global spinner_running
    i = 0
    while spinner_running:
        sys.stdout.write(Fore.CYAN + SPINNER_CHARS[i % len(SPINNER_CHARS)] + 
                        Style.RESET_ALL + " İşlem devam ediyor... " +
                        Fore.YELLOW + "(Çıkış: CTRL+C)" + Style.RESET_ALL + '\r')
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)

def start_spinner():
    global spinner_running
    spinner_running = True
    threading.Thread(target=spinner_animation, daemon=True).start()

def stop_spinner():
    global spinner_running
    spinner_running = False
    sys.stdout.write('\r')
    sys.stdout.flush()

def translate_status(status_msg):
    translations = {
        # Genel durumlar
        "Success": "Başarılı",
        "OK": "TAMAM",
        "completed": "Tamamlandı",
        "processing": "İşleniyor",
        "waiting": "Bekleniyor",

        # UUID ve Kimlik ile ilgili
        "Generated UUID": "UUID Oluşturuldu",
        "Generated MAC address": "MAC Adresi Oluşturuldu",
        "getting_token": "Token Alınıyor",

        # Yama işlemleri
        "Replacing pattern": "Desen Değiştiriliyor",
        "Found already patched patterns": "Önceden Yamalanmış Desenler Bulundu",
        "Patching complete": "Yama Tamamlandı",
        "path": "Dosya Yolu",
        "from": "Kaynak",
        "to": "Hedef",
        "count": "Adet",
        "patched_count": "Yamalan Adet",

        # Dosya işlemleri
        "Creating backup": "Yedek Oluşturuluyor",
        "Backup exists": "Yedek Mevcut",
        "Saving file": "Dosya Kaydediliyor",
        "File saved successfully": "Dosya Başarıyla Kaydedildi",
        "file": "Dosya",
        "backup_file": "Yedek Dosya",

        # Tarayıcı ve hesap işlemleri
        "init_browser_starting": "Tarayıcı Başlatılıyor",
        "user_agent_set": "Kullanıcı Ajanı Ayarlandı",
        "user_agent": "Kullanıcı Ajanı",
        "signup_starting": "Kayıt İşlemi Başlatılıyor",
        "creating_email": "E-posta Oluşturuluyor",
        "email_created": "E-posta Oluşturuldu",
        "email": "E-posta",
        "uuid": "UUID",
        "mac": "MAC Adresi",

        # Doğrulama işlemleri
        "turnstile_starting": "Turnstile Doğrulaması Başlatılıyor",
        "turnstile_started": "Turnstile Doğrulaması Başladı",
        "turnstile_success": "Turnstile Doğrulaması Başarılı",
        "verification_starting": "Doğrulama Başlatılıyor",
        "checking_inbox": "Gelen Kutusu Kontrol Ediliyor",
        "code_found": "Doğrulama Kodu Bulundu",
        "code": "Kod",
        "attempt": "Deneme",
        "seconds_remaining": "Kalan Saniye",

        # Limit ve yetkilendirme
        "usage_limit": "Kullanım Limiti",
        "limit": "Limit",
        "auth_update_success": "Kimlik Bilgileri Güncellendi"
    }
    return translations.get(status_msg, status_msg)

def monitor_process_output(process):
    global spinner_running
    start_time = time.time()
    last_turnstile_time = None
    turnstile_count = 0
    last_print_time = 0
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
            
        try:
            data = json.loads(line)
            status = data.get("status", "")
            
            # Turnstile kontrolü
            if status in ["turnstile_starting", "turnstile_started"]:
                if last_turnstile_time is None:
                    last_turnstile_time = time.time()
                    turnstile_count = 1
                else:
                    current_time = time.time()
                    if current_time - last_turnstile_time < 5:
                        turnstile_count += 1
                        if turnstile_count >= 3:
                            stop_spinner()
                            print(Fore.YELLOW + "\n! Turnstile doğrulamasında takılma tespit edildi.")
                            print("! Program 1 dakika sonra otomatik olarak yeniden başlatılacak." + Style.RESET_ALL)
                            time.sleep(60)
                            os.execv(sys.executable, ['python'] + sys.argv)
                    else:
                        last_turnstile_time = current_time
                        turnstile_count = 1
            
            # Çıktıları kontrol et ve göster
            current_time = time.time()
            if current_time - last_print_time >= 0.1:
                translated_status = translate_status(status)
                
                # Spinner'ı durdur, mesajı yazdır ve spinner'ı tekrar başlat
                if spinner_running:
                    stop_spinner()
                
                if "data" in data:
                    data_str = ""
                    for key, value in data["data"].items():
                        translated_key = translate_status(key)
                        if isinstance(value, (list, dict)):
                            continue  # Karmaşık veri tiplerini atla
                        data_str += f"{translated_key}: {value}, "
                    
                    if data_str:
                        print(Fore.CYAN + f"→ {translated_status}" + Style.RESET_ALL + 
                              f" - {data_str[:-2]}")
                else:
                    print(Fore.CYAN + f"→ {translated_status}" + Style.RESET_ALL)
                
                # Spinner'ı tekrar başlat
                if spinner_running:
                    sys.stdout.write('\n')
                    start_spinner()
                
                last_print_time = current_time
                
        except json.JSONDecodeError:
            if line.strip() and "ReferenceError: gM is not defined" not in line:
                if spinner_running:
                    stop_spinner()
                print(line.strip())
                if spinner_running:
                    sys.stdout.write('\n')
                    start_spinner()

    return process.poll()

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.GREEN + """
╔═══════════════════════════════════════════════════════════╗
║                   CURSOR MANAGER v1.0                     ║
║                                                           ║
║  Bu program Cursor uygulamasını yönetmek için             ║
║  tasarlanmıştır                                           ║
╚═══════════════════════════════════════════════════════════╝""" + Style.RESET_ALL)
    print(Fore.YELLOW + "\nÇıkmak için CTRL+C tuşlarına basın" + Style.RESET_ALL)

def print_step(step_no, message):
    print(Fore.YELLOW + f"[Adım {step_no}] " + Style.RESET_ALL + message)

def print_success(message):
    print(Fore.GREEN + f"✓ {message}" + Style.RESET_ALL)

def print_error(message):
    print(Fore.RED + f"✗ {message}" + Style.RESET_ALL)

def print_warning(message):
    print(Fore.YELLOW + f"! {message}" + Style.RESET_ALL)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def generate_machine_id():
    template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
    result = ""
    for char in template:
        if char in ['x', 'y']:
            r = random.randint(0, 15)
            v = r if char == 'x' else (r & 0x3 | 0x8)
            result += format(v, 'x')
        else:
            result += char
    return result

def generate_random_id():
    return uuid.uuid4().hex + uuid.uuid4().hex

def backup_machine_guid():
    backup_dir = os.path.join(os.path.expanduser('~'), "MachineGuid_Backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"MachineGuid_{timestamp}.txt")
    counter = 0
    
    while os.path.exists(backup_file):
        counter += 1
        backup_file = os.path.join(backup_dir, f"MachineGuid_{timestamp}_{counter}.txt")
    
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        
        with open(backup_file, 'w') as f:
            f.write(value)
        return backup_file
    except Exception as e:
        print_error(f"MachineGuid yedeklenirken hata: {str(e)}")
        return None

def update_storage_json():
    storage_path = os.path.join(os.getenv('APPDATA'), "Cursor", "User", "globalStorage", "storage.json")
    
    if not os.path.exists(storage_path):
        print_error("storage.json dosyası bulunamadı!")
        return False
        
    try:
        # Dosya özelliklerini kaydet
        original_attributes = os.stat(storage_path)
        
        # Dosyayı okuma
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Yeni değerleri oluştur
        new_values = {
            "telemetry.machineId": generate_random_id(),
            "telemetry.macMachineId": generate_machine_id(),
            "telemetry.devDeviceId": str(uuid.uuid4()),
            "telemetry.sqmId": "{" + str(uuid.uuid4()).upper() + "}"
        }
        
        # Değerleri güncelle
        for key, value in new_values.items():
            data[key] = value
        
        # UTF-8 without BOM olarak kaydet
        with open(storage_path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(data, f, indent=2)
            
        # Dosya özelliklerini geri yükle
        os.chmod(storage_path, original_attributes.st_mode)
        
        return new_values
    except Exception as e:
        print_error(f"storage.json güncellenirken hata: {str(e)}")
        return False

def update_machine_guid():
    try:
        new_guid = str(uuid.uuid4())
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, new_guid)
        winreg.CloseKey(key)
        return new_guid
    except Exception as e:
        print_error(f"MachineGuid güncellenirken hata: {str(e)}")
        return None

def kill_cursor_processes(debug=False):
    if not debug:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == 'cursor.exe':
                    proc.kill()
                    print_success(f"Cursor process sonlandırıldı (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

def show_info_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + """
╔═══════════════════════════════════════════════════════════╗
║                  CURSOR MANAGER - BİLGİ                   ║
║                                                           ║
║  Bu program aşağıdaki işlemleri gerçekleştirecektir:      ║
║                                                           ║
║    1. Cursor uygulaması kapatılacak                       ║
║    2. Sistem kimlikleri yenilenecek                       ║
║    3. Gerekli yamalar uygulanacak                         ║
║    4. Yeni hesap oluşturulacak                            ║
║    5. Sistem kimlikleri sıfırlanacak                      ║
║    6. Cursor otomatik olarak başlatılacak                 ║
║                                                           ║
║  NOT: İşlem sırasında Cursor kapatılacaktır!              ║
╚═══════════════════════════════════════════════════════════╝""" + Style.RESET_ALL)
    print(Fore.YELLOW + "\nDevam etmek için ENTER'a basın, çıkmak için CTRL+C" + Style.RESET_ALL)

def check_cursor_processes():
    cursor_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == 'cursor.exe':
                cursor_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return cursor_processes

def ask_to_close_cursor():
    cursor_processes = check_cursor_processes()
    if cursor_processes:
        print(Fore.YELLOW + "\n! DİKKAT: Cursor şu anda çalışıyor!")
        print("! Devam etmek için tüm Cursor pencereleri kapatılacak.")
        print("! Lütfen açık projelerinizi kaydedin." + Style.RESET_ALL)
        
        while True:
            choice = input("\nDevam etmek istiyor musunuz? (E/H): ").lower()
            if choice == 'e':
                return True
            elif choice == 'h':
                return False
            else:
                print(Fore.RED + "Lütfen 'E' veya 'H' girin." + Style.RESET_ALL)
    return True

def main():
    debug_mode = "--debug" in sys.argv
    
    show_info_screen()
    
    if not ask_to_close_cursor():
        print(Fore.YELLOW + "\nProgram kullanıcı tarafından iptal edildi." + Style.RESET_ALL)
        sys.exit(0)
    
    print_header()
    
    try:
        print_step(1, "Cursor işlemleri kontrol ediliyor...")
        kill_cursor_processes(debug_mode)
        
        print_step(2, "MachineGuid yedekleniyor...")
        backup_file = backup_machine_guid()
        if backup_file:
            print_success(f"Yedek dosyası oluşturuldu: {backup_file}")
        
        print_step(3, "Sistem ID'leri güncelleniyor...")
        new_values = update_storage_json()
        if new_values:
            print_success("storage.json güncellendi:")
            for key, value in new_values.items():
                print(Fore.CYAN + f"  {key}: " + Fore.WHITE + value)
        
        new_machine_guid = update_machine_guid()
        if new_machine_guid:
            print_success(f"Yeni MachineGuid: {new_machine_guid}")
        
        print_step(4, "Cursor yamaları uygulanıyor...")
        try:
            start_spinner()
            process = subprocess.Popen([sys.executable, "patch_cursor.py"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            monitor_process_output(process)
            stop_spinner()
            print_success("Yamalar başarıyla uygulandı")
        except subprocess.CalledProcessError as e:
            stop_spinner()
            print_error(f"Yama uygulanırken hata: {str(e)}")
        
        print_step(5, "Cursor hesabı oluşturuluyor...")
        try:
            start_spinner()
            process = subprocess.Popen([sys.executable, "cursor_auth.py"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            monitor_process_output(process)
            stop_spinner()
            print_success("Hesap oluşturma işlemi tamamlandı")
        except subprocess.CalledProcessError as e:
            stop_spinner()
            print_error(f"Hesap oluşturulurken hata: {str(e)}")

        print_step(6, "Sistem kimliklerini sıfırlama...")
        try:
            start_spinner()
            # PowerShell komutunu düzenle
            powershell_command = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", os.path.join(os.getcwd(), "reset.ps1")
            ]
            
            process = subprocess.Popen(
                powershell_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Çıktıları gerçek zamanlı olarak oku
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    stop_spinner()
                    print(Fore.CYAN + "→ " + Style.RESET_ALL + output.strip())
                    start_spinner()
            
            # Hata çıktısını kontrol et
            stderr_output = process.stderr.read()
            if stderr_output:
                stop_spinner()
                print_error(f"PowerShell hatası: {stderr_output}")
                raise Exception(stderr_output)
            
            # İşlem durumunu kontrol et
            if process.returncode != 0:
                raise Exception(f"PowerShell script hata kodu ile sonlandı: {process.returncode}")
            
            stop_spinner()
            print_success("Sistem kimlikleri başarıyla sıfırlandı")
        except Exception as e:
            stop_spinner()
            print_error(f"Sistem kimlikleri sıfırlanırken hata: {str(e)}")
            print_warning("PowerShell script çalıştırılamadı, manuel olarak çalıştırmayı deneyin")
        
        print_step(7, "Cursor başlatılıyor...")
        cursor_path = os.path.join(os.getenv('LOCALAPPDATA'), "Programs", "cursor", "Cursor.exe")
        if os.path.exists(cursor_path):
            try:
                # Cursor'ı doğrudan aç
                os.startfile(cursor_path)
                print_success("Cursor başlatıldı")
                print("\n" + Fore.GREEN + "İşlem tamamlandı!" + Style.RESET_ALL)
                # Programı hemen kapat
                sys.exit(0)
            except Exception as e:
                print_error(f"Cursor başlatılırken hata: {str(e)}")
                print_warning("Lütfen Cursor'ı manuel olarak başlatın")
        else:
            print_error("Cursor.exe bulunamadı!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n" + Fore.YELLOW + "Program kullanıcı tarafından sonlandırıldı!" + Style.RESET_ALL)
        sys.exit(0)

if __name__ == "__main__":
    main() 