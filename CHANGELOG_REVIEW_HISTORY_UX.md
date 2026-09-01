# DevNest Review History & Decision UX Update

Bu paket, DevNest-live-review-decisions-tr-fix sürümünün üzerine uygulanmıştır.

## İncelenecekler / Geçmiş
- Bir kararın İncelenecekler'e düşmesi için Kararlar sayfasının açık olması gerekmez.
- Takibi başlatılmış resource linkleri arka planda izlenmeye devam eder.
- İncelenecekler sayfasına `Proje Geçmişi` sekmesi eklendi.
- Local Git repository'lerinde proje commit geçmişi en yeniden eskiye gösterilir.
- Her commit altında eklenen, değiştirilen, silinen ve taşınan dosyalar insan dilinde açıklanır.
- GitHub-only repository'lerde commit metadata'sı arka planda alınır; dosya ayrıntıları gerektiğinde yüklenir.

## Kararlar
- Kararın gerçek başlığı artık ana başlıktır; `DEC-001` kalıcı teknik kimlik olarak ikincil gösterilir.
- Karar listesindeki sağ tık menüsüne aç/düzenle, başlığı değiştir ve sil eklendi.
- Ana karar ekranına açık bir silme butonu eklendi.
- Silinen DEC kimlikleri yeniden kullanılmaz.

## Navigasyon ve görünüm
- Notlar sayfasındaki Diagram sekmesi kaldırıldı. Mimari diyagramlar Architecture/Mimari bölümünde yaşar.
- Sağ üst alan GitHub bağlı değilse `GitHub'ı bağla` gösterir.
- GitHub bağlıysa aynı alanda tema değiştirme menüsü gösterilir.

## Diğer yaşam döngüsü işlemleri
- Mimari listesinde sağ tıkla yeniden adlandırma ve diyagramı silme eklendi.
- Proje detayındaki repository bağlantısı projeden kaldırılabilir; kaynak kod veya GitHub repository'si silinmez.
- Project kartlarına düzenleme eklendi.
- Notes için var olan Trash/Restore/Delete davranışı korunur.

## Ayarlar
- Mevcut Preferences/Tercihler penceresi kaldırılmadı.
- Aynı temel tercihler ayrıca sağdaki Ayarlar sayfasına taşındı ve değişiklikler anında kaydedilir.
