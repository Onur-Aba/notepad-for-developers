# Live Review / Decisions UX Fix

Bu paket, DevNest 2.1 UX sürümünün üzerine aşağıdaki davranış ve kullanılabilirlik düzeltmelerini ekler.

## İncelenecekler

- Aynı bilgi öğesi aynı depodaki birden fazla dosya/klasöre bağlıysa artık tek inceleme kartında birleştirilir.
- Aynı commit SHA birden fazla kaynaktan veya bağlantıdan geldiyse yalnızca bir kez gösterilir.
- Eski cache kayıtlarındaki yinelenen commitler de gösterim sırasında tekilleştirilir.
- A / M / D / R gibi Git durum harfleri kullanıcıya gösterilmez; bunun yerine "Yeni dosya eklendi", "Dosyanın içeriği değişti", "Dosya silindi" ve "Dosyanın adı/yeri değişti" gibi açıklamalar kullanılır.
- Değişiklik ayrıntıları bağlı dosyaları, tüm depo değişikliklerinden ayırır.

## Canlı yenileme

- Yerel Git depolarının HEAD commit'i uygulama açıkken arka planda yaklaşık 2 saniyede bir izlenir.
- HEAD değiştiğinde İncelenecekler, Dashboard, Kararlar, Notlar, Mimari ve proje özetleri sayfa değiştirmenize gerek kalmadan yenilenir.
- Uygulama terminal/editor kullanımından sonra tekrar öne geldiğinde de kontrol hemen tetiklenir.
- Bir kontrol devam ederken yeni kontrol isteği gelirse istek kaybolmaz; mevcut kontrol bitince tekrar çalışır.

## Kararlar

- Karar ekranında "Karar ne işe yarar?" anlatımı sadeleştirildi: karar, kodun ne yaptığını değil, bir teknik seçimin neden yapıldığını saklar.
- Karar listesinde bağlı depo ve kod takip durumu gösterilir.
- Bir karara kod bağlandıktan sonra DevNest, değişiklikleri karşılaştırabilmek için başlangıç commit'i gerektiğini açıklar ve "Takibi şimdi başlat" seçeneğini önerilen varsayılan olarak sunar.
- Takip durumları ayrı olarak gösterilir: bağlı kod yok, takip başlatılmadı, güncel, yeniden kontrol et, karşılaştırılamıyor.
- Karar yaşam döngüsü durumu (Önerildi/Kabul edildi vb.) ile kod takip durumu birbirinden ayrılır.

## Türkçe arayüz

- Aktif dosya/klasör seçiciler, inceleme ayrıntıları, karar oluşturma/kaydetme, not işlemleri, çöp kutusu, GitHub bağlantı işlemleri ve önemli onay/hata popup'ları Türkçe/İngilizce dil seçimine göre açılır.
- Diyagram üzerindeki metin giriş popup'ları da aktif dile göre gösterilir.
