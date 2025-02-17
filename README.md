# Cursor Manager v1.0

Bu program, Cursor uygulamasını yönetmek ve yeni hesap oluşturmak için tasarlanmış bir araçtır.


## ⚠️ Önemli Uyarı / Important Warning

### 🇹🇷 Türkçe Uyarı
Bu proje **SADECE EĞİTİM AMAÇLIDIR** ve otomatik hesap oluşturma sürecinin teknik olarak nasıl çalıştığını göstermek için hazırlanmıştır. Bu aracın kullanılması etik değildir ve Cursor'un hizmet şartlarına aykırıdır.

**Cursor'u desteklemek ve en iyi deneyimi yaşamak için lütfen resmi web sitesinden lisans satın alın: [cursor.sh](https://cursor.sh)**

Bu projenin amacı:
- Eğitim ve öğrenme
- Teknik süreçleri anlama
- Otomasyon mantığını kavrama

Bu projenin amacı **KESİNLİKLE**:
- Cursor'u ücretsiz kullanmak
- Hizmet şartlarını ihlal etmek
- Ticari kazanç elde etmek **DEĞİLDİR**

## 🚀 Özellikler

- Cursor uygulamasını otomatik kapatma ve başlatma
- Sistem kimliklerini otomatik yenileme
- Gerekli yamaları otomatik uygulama
- Yeni hesap oluşturma
- Sistem kimliklerini sıfırlama
- Otomatik yedekleme

## 📋 Gereksinimler

```
Python 3.8 veya üzeri
Windows 10/11
```

### 📦 Python Paketleri

```
requests==2.31.0
beautifulsoup4==4.12.2
DrissionPage==4.1.0.17
imaplib2==3.6
pathlib==1.0.1
colorama==0.4.6
psutil==5.9.8
```

## 💻 Kurulum

1. Bu depoyu bilgisayarınıza indirin
2. Gerekli Python paketlerini yükleyin:
   ```
   pip install -r requirements.txt
   ```

## 🎯 Kullanım

1. Programı yönetici olarak çalıştırın:
   ```
   python run_as_admin.py
   ```

2. Program otomatik olarak şu adımları gerçekleştirecektir:
   - Cursor uygulamasını kapatma
   - Sistem kimliklerini yenileme
   - Gerekli yamaları uygulama
   - Yeni hesap oluşturma
   - Sistem kimliklerini sıfırlama
   - Cursor'ı otomatik başlatma

## ⚠️ Önemli Notlar

- Program çalıştırılmadan önce açık Cursor projelerinizi kaydettiğinizden emin olun
- Program yönetici hakları gerektirir
- İşlem sırasında Cursor otomatik olarak kapatılacaktır
- Tüm sistem kimlikleri ve MachineGuid değerleri otomatik olarak yedeklenir

## 🔄 Yedekleme

- MachineGuid yedekleri `~/MachineGuid_Backups` klasöründe saklanır
- Her yedek benzersiz bir zaman damgası ile kaydedilir

## 🛠️ Sorun Giderme

1. "Cursor.exe bulunamadı" hatası:
   - Cursor'ın doğru şekilde yüklendiğinden emin olun
   - Varsayılan kurulum dizinini kontrol edin

2. "Yetki hatası" durumunda:
   - Programı yönetici olarak çalıştırdığınızdan emin olun
   - Windows güvenlik duvarı izinlerini kontrol edin

3. PowerShell script çalışmazsa:
   - PowerShell execution policy ayarlarını kontrol edin
   - `reset.ps1` dosyasının doğru konumda olduğundan emin olun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/yeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeniOzellik`)
5. Pull Request oluşturun 
