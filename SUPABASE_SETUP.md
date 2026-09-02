# DevNest Supabase Kurulumu

DevNest, Supabase proje URL'sini ve istemci anahtarını kaynak koda gömmez. Çalıştırmadan önce ortam değişkenleri ile verin.

## 1. Supabase veritabanını hazırla

Supabase Dashboard -> **SQL Editor** bölümünü açın ve `supabase/devnest_schema.sql` dosyasının tamamını çalıştırın.

> Daha önce DevNest'in eski Supabase SQL dosyasını çalıştırdıysanız da bu yeni dosyanın **tamamını yeniden çalıştırın**. Dosya idempotent olacak şekilde hazırlanmıştır ve mevcut veriyi silmeden yeni revision/conflict alanlarını, otomatik rol hiyerarşisini ve hızlı ekip snapshot RPC'lerini ekler.

Authentication -> Providers altında Email/Password oturum açmanın etkin olduğundan emin olun.

## 2. Gerekli değerleri alın

Supabase projenizin Project URL değerini ve Publishable key değerini alın. Eski projelerde legacy anon key de desteklenir.

`service_role`, `sb_secret_...` veya başka bir server secret anahtarını DevNest'e vermeyin ve desktop uygulamasına gömmeyin.

## 3. PowerShell ile çalıştırma

```powershell
$env:DEVNEST_SUPABASE_URL="https://PROJE_ID.supabase.co"
$env:DEVNEST_SUPABASE_PUBLISHABLE_KEY="sb_publishable_..."
python main.py
```

Legacy anon key kullanılıyorsa:

```powershell
$env:DEVNEST_SUPABASE_URL="https://PROJE_ID.supabase.co"
$env:DEVNEST_SUPABASE_ANON_KEY="ANON_KEY"
python main.py
```

GitHub entegrasyonu da kullanılacaksa aynı terminal oturumunda GitHub ortam değişkenlerini de ayarlayabilirsiniz:

```powershell
$env:DEVNEST_GITHUB_CLIENT_ID="KEY"
$env:DEVNEST_GITHUB_APP_SLUG="devnest-local-onur"
$env:DEVNEST_SUPABASE_URL="https://PROJE_ID.supabase.co"
$env:DEVNEST_SUPABASE_PUBLISHABLE_KEY="sb_publishable_..."
python main.py
```

## Online yedekleme davranışı

DevNest local-first çalışır. Bir projeyi, notu, kararı veya mimari içeriği değiştirmek **otomatik upload başlatmaz**. Online'a gönderim yalnızca **Online Yedekleme -> Seçilenleri online'a yedekle** düğmesine basıldığında yapılır.

İlk sütunda işaretlediğiniz içerikler Supabase'e gönderilir. Yalnızca tek bir not seçseniz bile notun ait olduğu projenin adı/kimliği üst kayıt olarak online tarafta tutulur. Yerel klasör yolları, parolalar ve API anahtarları yedek payload'ına eklenmez.

Her online proje/kaynakta `revision`, `updated_at` ve `updated_by` alanları bulunur. Aynı note veya decision başka bir ekip üyesi tarafından online tarafta değişmişse DevNest sonraki manuel yedekleme öncesinde bunu algılar. Çakışma penceresinde:

- hangi alanların değiştiği,
- metindeki eklenen/çıkarılan satırlar,
- online revision ve zaman,
- mümkünse değişikliği yapan kullanıcı

gösterilir. Kullanıcı online sürümü yerelde kullanabilir, yerel sürümü online'a yüklemeyi seçebilir veya öğeyi şimdilik atlayabilir. Revision kontrolü upload anında da tekrar yapılır; pencere açıkken üçüncü bir değişiklik gelirse stale veri ezilmez.

## Ekip rolleri

Rol düzenleme ekranında manuel "hiyerarşi seviyesi" yoktur. İç rank sunucuda verilen izinlerden otomatik hesaplanır. Kullanıcıya özel allow/deny override'ları da efektif hiyerarşiyi etkiler. `manage_roles` yetkisi olan biri yine de kendisini, eşit seviyedeki veya daha üstteki üyeleri/rolleri değiştiremez.

## Güvenlik notu

DevNest parolayı kendi veritabanında tutmaz; kimlik doğrulama Supabase Auth üzerinden yapılır. Veritabanı erişim sınırı RLS/policy ve server-side RPC kontrolleridir. İstemci tarafında yapılan kontroller tek başına güvenlik sınırı kabul edilmemelidir.

İstemci PostgREST/Auth çağrılarını JSON ve URL parametreleriyle yapar; uygulama kullanıcı girdilerinden ham SQL üretmez. Buna rağmen güvenliğin temel katmanı Supabase RLS ve `SECURITY DEFINER` RPC kontrolleridir. Desktop istemciye asla service-role/secret key verilmemelidir.
