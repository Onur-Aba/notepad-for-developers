<p align="center">
  <img src="resources/devnest.svg" alt="DevNest" width="92" height="92">
</p>

<h1 align="center">DevNest</h1>

<p align="center">
  <strong>Notes, tasks and lightweight diagrams for developers.</strong><br>
  Native Windows desktop app · Offline-first · No account · No telemetry
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.2.3-2f81f7?style=flat-square">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="PySide6" src="https://img.shields.io/badge/PySide6-Qt%206-41CD52?style=flat-square&logo=qt&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/Windows-10%20%2F%2011-0078D4?style=flat-square&logo=windows11&logoColor=white">
  <img alt="Offline" src="https://img.shields.io/badge/works-offline-555?style=flat-square">
</p>

<p align="center">
  <a href="./dist/DevNest.exe"><strong>⬇ Download DevNest.exe</strong></a>
  &nbsp;·&nbsp;
  <a href="#turkce">Türkçe</a>
  &nbsp;·&nbsp;
  <a href="#english">English</a>
</p>

> **Windows kullanıcıları:** Sadece programı kullanmak istiyorsanız kaynak kodu kurmanıza gerek yok. Yukarıdaki **Download DevNest.exe** bağlantısından `dist/DevNest.exe` dosyasını indirip çalıştırabilirsiniz.

---

<a id="turkce"></a>

# Türkçe

## DevNest nedir?

DevNest; notlarını, yapılacak işlerini, teknik fikirlerini ve küçük yazılım diyagramlarını tek yerde tutmak isteyen geliştiriciler için hazırlanmış native bir masaüstü uygulamasıdır.

Tarayıcı açmaz, hesap istemez ve notlarınızı herhangi bir sunucuya göndermez. Veriler yerel SQLite veritabanında saklanır; arayüz PySide6 / Qt ile çalışır.

### Öne çıkan özellikler

| Alan | Özellikler |
|---|---|
| **Notlar** | Hızlı not oluşturma, arama, yeniden adlandırma, çoğaltma, sıralama |
| **Editör** | Bold, italic, underline, strikethrough, listeler, font / boyut / kalınlık kontrolleri |
| **Todo** | Tıklanabilir `☐ / ☑` görevler, otomatik üstü çizme, Auto Checkbox, nested task desteği |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` algılama; UTF-8 import/export |
| **Diagram** | Boyutu sürükleyerek belirlenen şekiller, text, yönlü connector, zoom, pan, resize |
| **Temalar** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist, System |
| **Veri güvenliği** | Autosave, Trash, Restore, kalıcı silme, SQLite `VACUUM` |
| **Gizlilik** | Offline çalışma, login yok, telemetry yok, cloud zorunluluğu yok |

## Hızlı kullanım

### Checkbox

Bir satırı görev haline getirmek için toolbar'daki checkbox düğmesini veya <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> kullanabilirsiniz.

```text
☐ API endpointlerini hazırla
☐ Database bağlantısını oluştur
☑ Login ekranını tamamla
```

İşaretlenen görevlerin metni otomatik olarak üstü çizili hale gelir. İşaret kaldırıldığında strikethrough da kaldırılır.

**Auto Checkbox** açıkken dolu bir görev satırında <kbd>Enter</kbd> yeni bir checkbox satırı oluşturur. Boş checkbox satırında tekrar <kbd>Enter</kbd> normal metne döner. <kbd>Tab</kbd> / <kbd>Shift</kbd> + <kbd>Tab</kbd> ile görev seviyesini değiştirebilirsiniz.

### TXT içe / dışa aktarma

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
- **Round** — yuvarlatılmış dikdörtgen.
- **Ellipse** — elips / oval.
- **Diamond** — karar / akış diyagramı şekli.
- **Text** — bağımsız metin öğesi.
- **Connect** — bir nesnenin üzerinde başlayıp başka bir nesnenin üzerinde biten yönlü bağlantı çizer.
- **Select** — nesneleri taşır; seçilen shape'in kenar ve köşe tutamaçlarıyla boyutunu değiştirir.
- **Orta mouse tuşu + sürükleme** — seçili araç ne olursa olsun canvas üzerinde gezinir.
- **Mouse wheel** — zoom.

Connector yalnızca geçerli bir nesneden başlayıp başka bir geçerli nesnede bitebilir. Boş canvas'a bırakılan bağlantı kaydedilmez. Ok başı bağlantının yönünü gösterir.

## Temalar

DevNest sekiz görünüm seçeneği sunar:

**Dark**
- Matte Black
- Midnight Slate
- Graphite

**Light**
- Clean Light
- Soft Gray
- Warm Paper
- Cool Mist

**System**
- İşletim sistemi renk şemasını kullanır.

Seçilen tema QSettings ile kaydedilir ve bir sonraki açılışta geri yüklenir.

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

## Sadece EXE kullanmak istiyorum

Kaynak kodla uğraşmak istemiyorsanız repository içindeki hazır Windows executable dosyasını indirebilirsiniz:

### **[⬇ DevNest.exe indir](./dist/DevNest.exe)**

Dosya yolu:

```text
dist\DevNest.exe
```

PyInstaller ile oluşturulan executable kendi Python runtime'ını ve gerekli Qt bileşenlerini içerir. Hedef bilgisayarda ayrıca Python veya PySide6 kurulması gerekmez.

> İmzalanmamış yeni uygulamalarda Windows SmartScreen uyarısı görülebilir. Geniş çaplı dağıtım yapılacaksa executable'ın bir code-signing sertifikasıyla imzalanması önerilir.

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

### Klasörlü build — geliştirme ve ilk test için önerilir

```powershell
.\build.ps1
```

Çıktı:

```text
dist\DevNest\DevNest.exe
```

Bu dağıtım şeklinde `dist\DevNest` klasörünün tamamını taşımanız gerekir.

### Tek dosya EXE — paylaşım için

```powershell
.\build.ps1 -OneFile
```

Çıktı:

```text
dist\DevNest.exe
```

Bu dosya tek başına başka bir Windows 10 / 11 64-bit bilgisayara taşınabilir.

## Veriler nerede saklanıyor?

DevNest kullanıcı verisini executable'ın bulunduğu klasöre yazmak zorunda değildir. SQLite veritabanı Qt'nin application-data konumunda tutulur.

Kesin veritabanı yolunu **Help → About DevNest** ekranında görebilirsiniz.

Loglar aynı application-data alanındaki `logs` klasöründe tutulur.

### Yedekleme

Yedek almadan önce DevNest'i kapatın ve `devnest.db` dosyasını güvenli bir konuma kopyalayın.

---

<a id="english"></a>

# English

## What is DevNest?

DevNest is a native desktop workspace for developers who want notes, checklists, technical ideas and lightweight software diagrams in one place.

It does not require a browser, an account or a network connection. Notes stay on your machine in a local SQLite database, while the interface is built with PySide6 / Qt.

### Highlights

| Area | Features |
|---|---|
| **Notes** | Fast note creation, search, rename, duplicate and sorting |
| **Editor** | Bold, italic, underline, strikethrough, lists, font / size / weight controls |
| **Tasks** | Clickable `☐ / ☑` items, automatic strikethrough, Auto Checkbox and nested tasks |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` detection with UTF-8 import/export |
| **Diagrams** | Drag-to-size shapes, text, directional connectors, zoom, pan and resize |
| **Themes** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist and System |
| **Data safety** | Autosave, Trash, Restore, permanent delete and SQLite `VACUUM` |
| **Privacy** | Offline operation, no login, no telemetry and no mandatory cloud service |

## Quick usage

### Checklists

Use the checkbox toolbar action or <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> to turn a line into a task.

```text
☐ Prepare API endpoints
☐ Create database connection
☑ Finish login screen
```

Completed tasks are struck through automatically. Unchecking a task removes the strikethrough.

With **Auto Checkbox** enabled, pressing <kbd>Enter</kbd> after a non-empty task creates another task with the same indentation. Pressing <kbd>Enter</kbd> on an empty task exits checklist mode. Use <kbd>Tab</kbd> and <kbd>Shift</kbd> + <kbd>Tab</kbd> for nesting.

### TXT import / export

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

TXT cannot retain rich formatting such as bold or italic. DevNest keeps the native rich-text version in SQLite, so formatting remains intact inside the application.

## Diagrams

Each note has its own diagram workspace.

- **Square** — press and drag to create a box at the exact width and height you want.
- **Round** — rounded rectangle.
- **Ellipse** — ellipse / oval.
- **Diamond** — decision / flowchart shape.
- **Text** — standalone text element.
- **Connect** — draw a directional connection from one existing object to another.
- **Select** — move objects and resize selected shapes using edge and corner handles.
- **Middle mouse button + drag** — pan the canvas regardless of the active tool.
- **Mouse wheel** — zoom.

A connector must start on a valid object and end on a different valid object. Connections released onto empty canvas are discarded. The arrowhead clearly marks the target direction.

## Themes

DevNest includes eight appearance modes:

**Dark**
- Matte Black
- Midnight Slate
- Graphite

**Light**
- Clean Light
- Soft Gray
- Warm Paper
- Cool Mist

**System**
- Follows the operating system color scheme.

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

## I only want the EXE

If you only want to use the application, you do not need to install Python or clone the development environment.

### **[⬇ Download DevNest.exe](./dist/DevNest.exe)**

Repository path:

```text
dist\DevNest.exe
```

The PyInstaller build bundles the Python runtime and required Qt components, so Python and PySide6 do not need to be installed on the target machine.

> Windows SmartScreen may warn about a newly distributed unsigned executable. For public distribution, signing the executable with a code-signing certificate is recommended.

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

### Folder build — recommended for initial testing

```powershell
.\build.ps1
```

Output:

```text
dist\DevNest\DevNest.exe
```

Distribute the complete `dist\DevNest` directory when using this build mode.

### Single-file build — convenient for distribution

```powershell
.\build.ps1 -OneFile
```

Output:

```text
dist\DevNest.exe
```

The resulting file can be copied to another 64-bit Windows 10 / 11 machine and run without a separate Python installation.

## Where is the data stored?

DevNest does not require user data to be stored next to the executable. The SQLite database is stored under Qt's application-data location for the current Windows user.

The exact database path is shown under **Help → About DevNest**.

Log files are stored in the `logs` directory inside the same application-data area.

### Backup

Close DevNest before creating a backup, then copy `devnest.db` to a safe location.

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
  <sub>DevNest 1.2.3 · Native desktop workspace for everyday development notes and planning.</sub>
</p>
