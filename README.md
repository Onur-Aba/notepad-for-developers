<p align="center">
  <img src="resources/devnest.svg" alt="DevNest" width="96" height="96">
</p>

<h1 align="center">DevNest</h1>

<p align="center">
  <strong>Notes, tasks and lightweight diagrams for developers.</strong><br>
  Native desktop app for Windows · Offline-first · No account · No telemetry
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.2.4-2f81f7?style=flat-square">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="PySide6" src="https://img.shields.io/badge/PySide6-Qt%206-41CD52?style=flat-square&logo=qt&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/Windows-10%20%2F%2011-0078D4?style=flat-square&logo=windows11&logoColor=white">
  <img alt="Offline" src="https://img.shields.io/badge/offline-ready-555?style=flat-square">
</p>

<p align="center">
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe">
    <strong>⬇ Download DevNest.exe</strong>
  </a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest">Latest Release</a>
  &nbsp;·&nbsp;
  <a href="#turkce">Türkçe</a>
  &nbsp;·&nbsp;
  <a href="#english">English</a>
</p>

> **Windows users:** If you only want to use the application, you do not need to install the source code. Download `DevNest.exe` using the **Download DevNest.exe** button above and run it directly.
>
> **Windows kullanıcıları:** Sadece programı kullanmak istiyorsanız kaynak kodu kurmanıza gerek yok. Yukarıdaki **Download DevNest.exe** bağlantısından `DevNest.exe` dosyasını indirip doğrudan çalıştırabilirsiniz.

---

<a id="turkce"></a>

# 🇹🇷 Türkçe

## DevNest nedir?

DevNest; notlarını, yapılacak işlerini, teknik fikirlerini ve küçük yazılım diyagramlarını tek yerde tutmak isteyen geliştiriciler için hazırlanmış native bir masaüstü uygulamasıdır.

Tarayıcı açmaz, hesap istemez ve notlarınızı herhangi bir sunucuya göndermez. Veriler yerel SQLite veritabanında saklanır; arayüz PySide6 / Qt ile çalışır.

### Öne çıkan özellikler

| Alan | Özellikler |
|---|---|
| **Notlar** | Hızlı not oluşturma, arama, yeniden adlandırma, çoğaltma, sıralama |
| **Editör** | Bold, italic, underline, strikethrough, listeler, font / boyut / kalınlık kontrolleri; checkbox ve liste marker'ları da font ayarlarını takip eder |
| **Todo** | Tıklanabilir `☐ / ☑` görevler, otomatik üstü çizme, Auto Checkbox, nested task desteği, isteğe bağlı Enter sonrası boş satır |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` algılama; UTF-8 import/export |
| **Diagram** | Sürükleyerek boyutlandırılan şekiller, text, yönlü connector, zoom, pan, resize |
| **Temalar** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist, System |
| **Veri güvenliği** | Autosave, Trash, Restore, kalıcı silme, SQLite `VACUUM` |
| **Gizlilik** | Offline çalışma, login yok, telemetry yok, zorunlu cloud servisi yok |

## Hızlı indirme

Kaynak kodla uğraşmadan yalnızca uygulamayı kullanmak istiyorsanız hazır Windows executable dosyasını indirebilirsiniz:

<p align="center">
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe">
    <strong>⬇ DevNest.exe indir</strong>
  </a>
</p>

Bu bağlantı repository içindeki büyük binary dosya önizleme sayfasına değil, GitHub Releases üzerindeki en güncel `DevNest.exe` dosyasına gider.

> PyInstaller build'i gerekli Python runtime ve Qt bileşenlerini paketler. Hedef Windows bilgisayarda ayrıca Python veya PySide6 kurulu olması gerekmez.

## Checkbox kullanımı

Bir satırı görev haline getirmek için toolbar'daki checkbox düğmesini veya <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> kullanabilirsiniz.

```text
☐ API endpointlerini hazırla
☐ Database bağlantısını oluştur
☑ Login ekranını tamamla
```

İşaretlenen görevlerin metni otomatik olarak üstü çizili hale gelir. İşaret kaldırıldığında strikethrough da kaldırılır.

**Auto Checkbox** açıkken dolu bir görev satırında <kbd>Enter</kbd> yeni bir checkbox satırı oluşturur. Boş checkbox satırında tekrar <kbd>Enter</kbd> normal metne döner. <kbd>Tab</kbd> / <kbd>Shift</kbd> + <kbd>Tab</kbd> ile görev seviyesini değiştirebilirsiniz.

## TXT içe / dışa aktarma

DevNest aşağıdaki biçimlerin tamamını tanır:

```text
[ ] Backend
[x] Database
[X] Authentication
☐ Frontend
☑ Login
✓ Deploy
```

Dışa aktarılan checklist'ler taşınabilir bir biçimde yazılır:

```text
[ ] Backend
    [ ] API
    [x] Database
```

TXT formatı bold / italic gibi rich-text özelliklerini taşımaz. Bu biçimler uygulamanın SQLite veritabanındaki native not içeriğinde korunur.

## Diagram kullanımı

Diagram alanı her not için ayrı saklanır.

- **Square** — sol mouse tuşuna basılı tutup sürükleyerek istediğiniz genişlik ve yükseklikte kutu oluşturur.
- **Round** — yuvarlatılmış dikdörtgen oluşturur.
- **Ellipse** — elips / oval oluşturur.
- **Diamond** — karar / akış diyagramı şekli oluşturur.
- **Text** — bağımsız metin öğesi ekler.
- **Connect** — bir nesnenin üzerinde başlayıp başka bir nesnenin üzerinde biten yönlü bağlantı çizer.
- **Select** — nesneleri taşır; seçilen shape'in kenar ve köşe tutamaçlarıyla boyutunu değiştirir.
- **Orta mouse tuşu + sürükleme** — aktif araçtan bağımsız olarak canvas üzerinde gezinir.
- **Mouse wheel** — zoom yapar.

Connector yalnızca geçerli bir nesneden başlayıp başka bir geçerli nesnede bitebilir. Boş canvas'a bırakılan bağlantı kaydedilmez. Ok başı bağlantının yönünü gösterir.

## Temalar

DevNest farklı çalışma ortamlarına uygun tema seçenekleri sunar.

### Dark

- Matte Black
- Midnight Slate
- Graphite

### Light

- Clean Light
- Soft Gray
- Warm Paper
- Cool Mist

### System

İşletim sisteminin renk tercihine göre görünüm uygular.

Seçilen tema QSettings ile kaydedilir ve uygulama tekrar açıldığında geri yüklenir.

## Klavye kısayolları

| İşlem | Kısayol |
|---|---|
| Yeni not | <kbd>Ctrl</kbd> + <kbd>N</kbd> |
| Not içinde bul | <kbd>Ctrl</kbd> + <kbd>F</kbd> |
| Geri al | <kbd>Ctrl</kbd> + <kbd>Z</kbd> |
| Yinele | <kbd>Ctrl</kbd> + <kbd>Y</kbd> |
| Bold | <kbd>Ctrl</kbd> + <kbd>B</kbd> |
| Italic | <kbd>Ctrl</kbd> + <kbd>I</kbd> |
| Underline | <kbd>Ctrl</kbd> + <kbd>U</kbd> |
| Checkbox | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> |
| TXT export | <kbd>Ctrl</kbd> + <kbd>E</kbd> |
| Sidebar aç / kapat | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>B</kbd> |
| Editor | <kbd>Ctrl</kbd> + <kbd>1</kbd> |
| Diagram | <kbd>Ctrl</kbd> + <kbd>2</kbd> |
| Diagram öğesini çoğalt | <kbd>Ctrl</kbd> + <kbd>D</kbd> |
| Seçili diagram öğesini sil | <kbd>Delete</kbd> |

## Kaynak koddan çalıştırma

### Gereksinimler

- Windows 10 / 11
- Python 3.12+
- PowerShell

Repository'yi indirdikten sonra proje klasöründe PowerShell açın.

```powershell
python --version
```

Virtual environment oluşturun:

```powershell
python -m venv .venv
```

Aktifleştirin:

```powershell
.\.venv\Scripts\Activate.ps1
```

PowerShell izin vermezse yalnızca mevcut terminal oturumu için:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Bağımlılıkları kurun:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Testleri çalıştırın:

```powershell
python -m pytest -q
```

Uygulamayı başlatın:

```powershell
python main.py
```

## Windows EXE oluşturma

Projede hazır `build.ps1` ve `DevNest.spec` bulunur.

### Klasörlü build

Geliştirme ve ilk dağıtım testi için:

```powershell
.\build.ps1
```

Çıktı:

```text
dist\DevNest\DevNest.exe
```

Bu build tipinde `dist\DevNest` klasörünün tamamını dağıtmanız gerekir.

### Tek dosya EXE

Tek `DevNest.exe` üretmek için:

```powershell
.\build.ps1 -OneFile
```

Çıktı:

```text
dist\DevNest.exe
```

GitHub Releases'a yüklenecek dosya bu tek dosyalık build olabilir.

## GitHub Release yayınlama

Yeni bir sürüm yayınlarken:

1. GitHub repository sayfasında **Releases** bölümünü açın.
2. **Draft a new release** seçin.
3. Örneğin `v1.2.4` şeklinde bir tag oluşturun.
4. Release başlığını örneğin `DevNest 1.2.4` yapın.
5. `dist\DevNest.exe` dosyasını release asset olarak yükleyin.
6. Release'i yayınlayın.

README'deki indirme bağlantısı:

```text
https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe
```

olduğu için sonraki sürümlerde README bağlantısını değiştirmeniz gerekmez. Release asset adı `DevNest.exe` olarak kaldığı sürece buton en güncel release dosyasını indirir.

## Veriler nerede saklanıyor?

DevNest kullanıcı verisini executable'ın yanına yazmak zorunda değildir. SQLite veritabanı Qt'nin application-data konumunda tutulur.

Kesin veritabanı yolunu **Help → About DevNest** ekranında görebilirsiniz.

Loglar aynı application-data alanındaki `logs` klasöründe tutulur.

### Yedekleme

Yedek almadan önce DevNest'i kapatın ve `devnest.db` dosyasını güvenli bir konuma kopyalayın.

### Windows SmartScreen

İmzalanmamış yeni executable dosyalarında Windows SmartScreen uyarısı görülebilir. Uygulamayı geniş çapta dağıtacaksanız `DevNest.exe` dosyasını bir code-signing sertifikasıyla imzalamak daha profesyonel bir dağıtım sağlar.

---

<a id="english"></a>

# 🇬🇧 English

## What is DevNest?

DevNest is a native desktop workspace for developers who want notes, checklists, technical ideas and lightweight software diagrams in one place.

It does not require a browser, an account or a network connection. Notes stay on your machine in a local SQLite database, while the interface is built with PySide6 / Qt.

### Highlights

| Area | Features |
|---|---|
| **Notes** | Fast note creation, search, rename, duplicate and sorting |
| **Editor** | Bold, italic, underline, strikethrough, lists, font / size / weight controls; checkbox and list markers follow font formatting |
| **Tasks** | Clickable `☐ / ☑` items, automatic strikethrough, Auto Checkbox and nested tasks |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` detection with UTF-8 import/export |
| **Diagrams** | Drag-to-size shapes, text, directional connectors, zoom, pan and resize |
| **Themes** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist and System |
| **Data safety** | Autosave, Trash, Restore, permanent delete and SQLite `VACUUM` |
| **Privacy** | Offline operation, no login, no telemetry and no mandatory cloud service |

## Quick download

If you only want to use DevNest and do not need the source code, download the ready-to-run Windows executable:

<p align="center">
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe">
    <strong>⬇ Download DevNest.exe</strong>
  </a>
</p>

This link goes directly to the latest `DevNest.exe` asset published under GitHub Releases instead of opening GitHub's large binary file preview page.

> The PyInstaller build bundles the required Python runtime and Qt components. Python and PySide6 do not need to be installed separately on the target Windows machine.

## Checklists

Use the checkbox toolbar action or <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> to turn a line into a task.

```text
☐ Prepare API endpoints
☐ Create database connection
☑ Finish login screen
```

Completed tasks are struck through automatically. Unchecking a task removes the strikethrough.

With **Auto Checkbox** enabled, pressing <kbd>Enter</kbd> after a non-empty task creates another task with the same indentation. Pressing <kbd>Enter</kbd> on an empty task exits checklist mode. Use <kbd>Tab</kbd> and <kbd>Shift</kbd> + <kbd>Tab</kbd> for nesting.

## TXT import / export

DevNest recognizes all of the following forms:

```text
[ ] Backend
[x] Database
[X] Authentication
☐ Frontend
☑ Login
✓ Deploy
```

Portable TXT export uses:

```text
[ ] Backend
    [ ] API
    [x] Database
```

TXT cannot retain rich formatting such as bold or italic. DevNest keeps the native rich-text version in SQLite so formatting remains intact inside the application.

## Diagrams

Each note has its own diagram workspace.

- **Square** — press and drag to create a box at the exact width and height you want.
- **Round** — create a rounded rectangle.
- **Ellipse** — create an ellipse / oval.
- **Diamond** — create a decision / flowchart shape.
- **Text** — add a standalone text element.
- **Connect** — draw a directional connection from one existing object to another.
- **Select** — move objects and resize selected shapes using edge and corner handles.
- **Middle mouse button + drag** — pan the canvas regardless of the active tool.
- **Mouse wheel** — zoom.

A connector must start on a valid object and end on a different valid object. Connections released onto empty canvas are discarded. The arrowhead marks the target direction.

## Themes

DevNest includes several appearance presets for different environments.

### Dark

- Matte Black
- Midnight Slate
- Graphite

### Light

- Clean Light
- Soft Gray
- Warm Paper
- Cool Mist

### System

Follows the operating system color preference.

The selected theme is stored with QSettings and restored on the next launch.

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| New note | <kbd>Ctrl</kbd> + <kbd>N</kbd> |
| Find in note | <kbd>Ctrl</kbd> + <kbd>F</kbd> |
| Undo | <kbd>Ctrl</kbd> + <kbd>Z</kbd> |
| Redo | <kbd>Ctrl</kbd> + <kbd>Y</kbd> |
| Bold | <kbd>Ctrl</kbd> + <kbd>B</kbd> |
| Italic | <kbd>Ctrl</kbd> + <kbd>I</kbd> |
| Underline | <kbd>Ctrl</kbd> + <kbd>U</kbd> |
| Checkbox | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> |
| Export TXT | <kbd>Ctrl</kbd> + <kbd>E</kbd> |
| Toggle sidebar | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>B</kbd> |
| Editor | <kbd>Ctrl</kbd> + <kbd>1</kbd> |
| Diagram | <kbd>Ctrl</kbd> + <kbd>2</kbd> |
| Duplicate diagram item | <kbd>Ctrl</kbd> + <kbd>D</kbd> |
| Delete selected diagram item | <kbd>Delete</kbd> |

## Run from source

### Requirements

- Windows 10 / 11
- Python 3.12+
- PowerShell

Open PowerShell in the project directory and verify Python:

```powershell
python --version
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the test suite:

```powershell
python -m pytest -q
```

Start DevNest:

```powershell
python main.py
```

## Build a Windows executable

The repository includes `build.ps1` and `DevNest.spec`.

### Folder build

Recommended for development and initial distribution testing:

```powershell
.\build.ps1
```

Output:

```text
dist\DevNest\DevNest.exe
```

Distribute the complete `dist\DevNest` directory when using this mode.

### Single-file EXE

To create one standalone executable:

```powershell
.\build.ps1 -OneFile
```

Output:

```text
dist\DevNest.exe
```

This single-file build can be uploaded as the GitHub Release asset.

## Publishing a GitHub Release

When publishing a new version:

1. Open **Releases** in the GitHub repository.
2. Select **Draft a new release**.
3. Create a tag such as `v1.2.4`.
4. Use a release title such as `DevNest 1.2.4`.
5. Upload `dist\DevNest.exe` as a release asset.
6. Publish the release.

The README download button points to:

```text
https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe
```

As long as the release asset remains named `DevNest.exe`, the README button automatically downloads the executable from the latest published release. You do not need to update the README link for every version.

## Where is the data stored?

DevNest does not require user data to be stored next to the executable. The SQLite database is stored under Qt's application-data location for the current Windows user.

The exact database path is shown under **Help → About DevNest**.

Log files are stored in the `logs` directory inside the same application-data area.

### Backup

Close DevNest before creating a backup, then copy `devnest.db` to a safe location.

### Windows SmartScreen

Windows SmartScreen may warn about a newly distributed unsigned executable. If DevNest is distributed publicly, signing `DevNest.exe` with a code-signing certificate provides a more professional Windows distribution experience.

---

## Technology

```text
Python 3.12+
PySide6 / Qt 6
SQLite
QSettings
PyInstaller
```

DevNest is designed to work locally without a web server, browser frontend, mandatory cloud account or telemetry.

<p align="center">
  <sub>DevNest 1.2.4 · Native desktop workspace for everyday development notes and planning.</sub>
</p>
