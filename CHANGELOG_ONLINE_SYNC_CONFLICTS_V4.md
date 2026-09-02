# DevNest Online Sync / Teams UX Update

- Online Backup ağacı genişleyen ilk sütun + sabit tür sütunu kullanıyor; `...` olarak görünen içerik adları düzeltildi.
- Ekranın online/internet yedekleme olduğu açık bir banner ile anlatılıyor.
- Otomatik cloud upload kaldırıldı; online değişiklikler yalnız manuel backup düğmesiyle gönderiliyor.
- Backup sırasında yüzde ilerleme çubuğu ve işlem açıklaması eklendi.
- `cloud_projects` / `cloud_resources` için revision + updated_by optimistic concurrency eklendi.
- Aynı Note/Decision başka bir kullanıcı tarafından değiştirildiyse upload öncesi conflict dialog açılıyor; alan ve satır farkları gösteriliyor.
- Conflict dialog: online sürümü yerelde kullan / yerel sürümü online'a yükle / atla seçeneklerini sunuyor.
- TEAM Online Content sekmesi ile izinli ekip üyeleri online not/karar düzenleyebiliyor; stale edit revision filtresiyle engelleniyor.
- Teams ana ekranı tek `team_overview` RPC ve arka plan task ile yükleniyor; UI ağ isteği boyunca donmuyor.
- Team Detail tek `team_detail_snapshot` RPC ile proje/üye/rol/aktivite verisini topluyor.
- Manuel hierarchy rank alanı kaldırıldı; server rank'ı rol permission setinden otomatik türetiyor.
- Kişiye özel permission override'ları efektif hiyerarşi hesabına dahil edildi.
