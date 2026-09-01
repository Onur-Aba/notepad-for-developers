# DevNest 2.0.0 — Full Source

This file contains the complete text-source snapshot for DevNest 2.0.0. Binary icon files are included in the ZIP but intentionally not embedded here.

## `.gitignore`

````gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
build/
dist/
*.log
````

## `DevNest.spec`

````python
# -*- mode: python ; coding: utf-8 -*-
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--onefile", action="store_true")
options, _unknown = parser.parse_known_args()

project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(project_root / "resources"), "resources")],
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

common = dict(
    name="DevNest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "resources" / "devnest.ico"),
)

if options.onefile:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        upx_exclude=[],
        runtime_tmpdir=None,
        **common,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        **common,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="DevNest",
    )
````

## `GITHUB_SETUP.md`

````markdown
# DevNest 2.0 — GitHub App setup

DevNest stays local-first. GitHub is an optional read-only integration used to list repositories, inspect commits / pull requests, compare revisions, and decide whether linked documents need review.

## Required GitHub App settings

Create a GitHub App under **Settings → Developer settings → GitHub Apps → New GitHub App**.

Recommended settings:

- **GitHub App name:** DevNest (or a unique development name)
- **Homepage URL:** your DevNest repository / project page
- **Webhook:** disabled for the desktop-only architecture
- **Request user authorization (OAuth) during installation:** leave disabled; DevNest performs authorization separately with Device Flow
- **Device Flow:** enabled
- **Expire user authorization tokens:** leave enabled (DevNest refreshes Device Flow tokens)
- **Repository permissions:**
  - Contents: **Read-only**
  - Pull requests: **Read-only**
  - Metadata: GitHub provides the required read access for app metadata
- Do not request write permissions.
- For private development you can limit installation to your own account; for distribution choose the option that lets other accounts install the app.

After creating the app, copy its **Client ID** (not App ID). Put it in `app/constants.py`:

```python
GITHUB_APP_CLIENT_ID = "Iv1.xxxxxxxxxxxxxxxx"
GITHUB_APP_INSTALL_URL = "https://github.com/apps/<your-app-slug>/installations/new"
```

The Client ID and installation URL are public identifiers and may be shipped in the executable. Do **not** put a client secret or private key in the desktop application.

## End-user flow

1. Install/manage the DevNest GitHub App and choose the repositories DevNest may access.
2. In DevNest, choose **Project → Connect GitHub**.
3. DevNest shows a GitHub Device Flow code and opens the browser.
4. Approve the device.
5. Open **Project → GitHub Repositories** and import an allowed repository.

DevNest stores GitHub access/refresh credentials in **Windows Credential Manager**, not in SQLite.

## Local repositories

GitHub is not required for a local checkout. Create a project and select a local Git repository. DevNest uses the installed `git` executable to read HEAD, history and changed file paths. GitHub is only needed for remote-only repositories and GitHub-specific context such as pull requests.
````

## `README.md`

````markdown
<p align="center">
  <img src="resources/devnest.svg" alt="DevNest" width="96" height="96">
</p>

<h1 align="center">DevNest</h1>

<p align="center">
  <strong>Living engineering context for developers.</strong><br>
  Native Windows desktop app · Local-first · Git-aware · Optional read-only GitHub connection
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-2.0.0-2f81f7?style=flat-square">
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

### DevNest 2.0 Engineering Context

DevNest 2.0, mevcut not/editör/diyagram motorunu korurken projeleri gerçek Git repository bağlamına taşır. Her proje local Git checkout veya izin verilmiş bir GitHub repository ile ilişkilendirilebilir. Note ve Decision belgeleri repo, klasör, dosya veya seçili diagram node'larıyla bağlanabilir. DevNest bağlantı oluşturulduğu andaki commit SHA'yı baseline olarak saklar; bağlı kod daha sonra değişirse belgeyi **Needs Review** olarak işaretler. Bu kontrol AI kullanmaz: yalnızca Git commit geçmişi ve değişen dosya yolları kullanılır.

- Project bazlı çalışma alanı
- Note / Decision belge türleri
- Local Git repository algılama ve otomatik GitHub remote tanıma
- Repo / directory / file → document bağlantıları
- Diagram node → repo path bağlantıları
- Commit ve Pull Request referansları
- Baseline SHA + Current / Needs Review durumu
- Açılışta ve uygulama çalışırken sessiz repository taraması
- GitHub Device Flow + Windows Credential Manager
- GitHub tarafında yalnızca read-only API kullanımı

GitHub App hazırlığı için [`GITHUB_SETUP.md`](GITHUB_SETUP.md) dosyasına bakın.

| Alan | Özellikler |
|---|---|
| **Notlar** | Hızlı not oluşturma, arama, yeniden adlandırma, çoğaltma, sıralama |
| **Editör** | Bold, italic, underline, strikethrough, bullet listeleri, gerçek metin olarak `1. 2. 3.` yazan List Mode, font / boyut / kalınlık kontrolleri |
| **Todo** | Tıklanabilir `☐ / ☑` görevler, otomatik üstü çizme, Auto Checkbox, nested task desteği, toolbar'dan açılıp kapanan Double Enter |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` algılama; UTF-8 import/export |
| **Diagram** | Sürükleyerek boyutlandırılan şekiller, text, yönlü connector, zoom, pan, resize |
| **Temalar** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist, System |
| **Veri güvenliği** | Autosave, Trash, Restore, kalıcı silme, SQLite `VACUUM` |
| **Gizlilik** | DevNest hesabı yok, telemetry yok, zorunlu cloud servisi yok; GitHub bağlantısı isteğe bağlı ve read-only |

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

## List Mode ve Double Enter

Toolbar'daki **List Mode** açıldığında mevcut satıra `1. ` eklenir ve her <kbd>Enter</kbd> basışında `2. `, `3. `, `4. ` şeklinde sıra devam eder. Birden fazla satır seçiliyken List Mode açılırsa seçili satırlar 1'den başlayarak topluca numaralandırılır. Bu numaralar Qt'nin görsel liste marker'ları değil, doğrudan notun içindeki metin karakterleridir; bu yüzden <kbd>Ctrl</kbd> + <kbd>A</kbd>, kopyalama ve TXT dışa aktarmada numaralar da dahil edilir.

**Double Enter** açıkken tek bir <kbd>Enter</kbd> iki satır aşağı ilerler ve arada bir boş satır bırakır. List Mode ile birlikte kullanıldığında sonraki sıra numarası boş satırdan sonra oluşturulur.

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
| Not içinde bul (editör içi arama, tüm eşleşmeler vurgulanır) | <kbd>Ctrl</kbd> + <kbd>F</kbd> |
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


### Editör içi arama

`Ctrl+F` ayrı bir pencere açmak yerine editörün sağ üstünde arama çubuğunu gösterir. Yazarken bütün eşleşmeler anında vurgulanır. **Down** veya **Up** yönlerinden yalnızca biri seçilebilir; **Find** veya Enter ile aynı sorgunun sonraki/önceki eşleşmesine geçilir. Uzun notlarda eşleşme konumları dikey scrollbar üzerinde de aktif temaya uygun küçük işaretlerle gösterilir.

- Aynı sorguda tekrar Find kullanmak aynı eşleşmede kalmaz; seçilen yönde ilerler.
- Arama varsayılan olarak büyük/küçük harf duyarsızdır.
- Esc veya × ile kapatıldığında geçici vurgular temizlenir.

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
3. Örneğin `v2.0.0` şeklinde bir tag oluşturun.
4. Release başlığını örneğin `DevNest 2.0.0` yapın.
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

### DevNest 2.0 Engineering Context

DevNest 2.0 keeps the existing editor, task and diagram engine while attaching documents to real Git repository context. A Note or Decision can link to a repository, directory, file, or selected diagram node. DevNest stores the current commit SHA as the review baseline. If linked paths change later, the document becomes **Needs Review**. No AI is involved; the signal comes only from Git history and changed file paths.

See [`GITHUB_SETUP.md`](GITHUB_SETUP.md) for the GitHub App configuration.

| Area | Features |
|---|---|
| **Notes** | Fast note creation, search, rename, duplicate and sorting |
| **Editor** | Bold, italic, underline, strikethrough, lists, font / size / weight controls; checkbox and list markers follow font formatting |
| **Tasks** | Clickable `☐ / ☑` items, automatic strikethrough, Auto Checkbox and nested tasks |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` detection with UTF-8 import/export |
| **Diagrams** | Drag-to-size shapes, text, directional connectors, zoom, pan and resize |
| **Themes** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist and System |
| **Data safety** | Autosave, Trash, Restore, permanent delete and SQLite `VACUUM` |
| **Privacy** | No DevNest account, no telemetry, no mandatory cloud; GitHub connection is optional and read-only |

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
| Find in note (inline bar, all matches highlighted) | <kbd>Ctrl</kbd> + <kbd>F</kbd> |
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


### Inline Find

`Ctrl+F` opens a search bar inside the editor instead of a dialog. Matches are highlighted as you type. Choose **Down** or **Up** (mutually exclusive), then press **Find** or Enter to move to the next match in that direction. Long notes also show theme-aware match markers on the vertical scrollbar.

- The first query highlights every match immediately.
- Repeating Find advances to the next/previous occurrence instead of selecting the same one again.
- Search is case-insensitive by default.
- Esc or the × button closes the bar and clears temporary highlights.

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
3. Create a tag such as `v2.0.0`.
4. Use a release title such as `DevNest 2.0.0`.
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
  <sub>DevNest 2.0.0 · Native desktop workspace for everyday development notes and planning.</sub>
</p>
````

## `app/__init__.py`

````python
from app.constants import VERSION

__all__ = ["VERSION"]
````

## `app/constants.py`

````python
from __future__ import annotations

APP_NAME = "DevNest"
ORGANIZATION_NAME = "DevNest"
ORGANIZATION_DOMAIN = "devnest.local"
VERSION = "2.0.0"
DEFAULT_NOTE_TITLE = "Untitled Note"
DEFAULT_AUTOSAVE_DELAY_MS = 750
MIN_AUTOSAVE_DELAY_MS = 300
MAX_AUTOSAVE_DELAY_MS = 5000
TAB_SPACES = 4

# Fill these once after registering the DevNest GitHub App. Client IDs are public
# identifiers and are safe to ship in a desktop binary; never embed a client
# secret or private key. Leaving CLIENT_ID empty makes DevNest ask the developer
# for it on first GitHub connection, which is useful during development.
GITHUB_APP_CLIENT_ID = ""
GITHUB_APP_INSTALL_URL = ""

SHORTCUTS: dict[str, str] = {
    "New Note": "Ctrl+N",
    "Find in Note": "Ctrl+F",
    "Undo": "Ctrl+Z",
    "Redo": "Ctrl+Y",
    "Bold": "Ctrl+B",
    "Italic": "Ctrl+I",
    "Underline": "Ctrl+U",
    "Checkbox": "Ctrl+Shift+X",
    "Export TXT": "Ctrl+E",
    "Toggle Sidebar": "Ctrl+Shift+B",
    "Editor Tab": "Ctrl+1",
    "Diagram Tab": "Ctrl+2",
    "Duplicate Selected Diagram Item": "Ctrl+D",
    "Delete Selected Diagram Item": "Delete",
}
````

## `app/database.py`

````python
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.constants import DEFAULT_NOTE_TITLE
from app.models import ExternalRef, Note, NoteSummary, Project, Repository, ResourceLink


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DatabaseError(RuntimeError):
    pass


class Database:
    """SQLite persistence layer.

    Schema migrations are deliberately additive so databases created by DevNest
    1.x keep every note and diagram intact while gaining the project/repository
    context model.
    """

    SCHEMA_VERSION = 5

    def __init__(self, path: Path | str | None = None) -> None:
        if path is None:
            from app.paths import database_path

            self.path = database_path()
        else:
            self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.connection = sqlite3.connect(self.path, timeout=5.0)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA synchronous = NORMAL")
            self._migrate()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database could not be opened: {exc}") from exc

    def _migrate(self) -> None:
        try:
            version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
            if 0 < version < 2:
                self._backup_legacy_database()
            if version > self.SCHEMA_VERSION:
                raise DatabaseError(
                    f"Database schema {version} is newer than supported schema {self.SCHEMA_VERSION}."
                )
            if version < 1:
                with self.connection:
                    self.connection.executescript(
                        """
                        CREATE TABLE IF NOT EXISTS notes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            content_html TEXT NOT NULL DEFAULT '',
                            content_plain TEXT NOT NULL DEFAULT '',
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1))
                        );
                        CREATE INDEX IF NOT EXISTS idx_notes_deleted_updated
                            ON notes(is_deleted, updated_at DESC);
                        CREATE INDEX IF NOT EXISTS idx_notes_title
                            ON notes(title COLLATE NOCASE);
                        CREATE TABLE IF NOT EXISTS diagrams (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            note_id INTEGER NOT NULL UNIQUE,
                            data_json TEXT NOT NULL DEFAULT '{"items":[],"edges":[],"paths":[]}',
                            updated_at TEXT NOT NULL,
                            FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
                        );
                        CREATE TABLE IF NOT EXISTS settings (
                            key TEXT PRIMARY KEY,
                            value TEXT NOT NULL
                        );
                        PRAGMA user_version = 1;
                        """
                    )
                version = 1

            if version < 2:
                with self.connection:
                    self.connection.executescript(
                        """
                        CREATE TABLE IF NOT EXISTS projects (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            uuid TEXT NOT NULL UNIQUE,
                            name TEXT NOT NULL,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        CREATE TABLE IF NOT EXISTS repositories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            project_id INTEGER NOT NULL,
                            uuid TEXT NOT NULL UNIQUE,
                            provider TEXT NOT NULL DEFAULT 'git',
                            local_path TEXT,
                            github_owner TEXT,
                            github_repo TEXT,
                            default_branch TEXT,
                            last_seen_sha TEXT,
                            last_scanned_at TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                            UNIQUE(project_id, local_path),
                            UNIQUE(project_id, github_owner, github_repo)
                        );
                        CREATE INDEX IF NOT EXISTS idx_repositories_project ON repositories(project_id);
                        """
                    )
                    columns = {row[1] for row in self.connection.execute("PRAGMA table_info(notes)")}
                    if "uuid" not in columns:
                        self.connection.execute("ALTER TABLE notes ADD COLUMN uuid TEXT")
                    if "project_id" not in columns:
                        self.connection.execute("ALTER TABLE notes ADD COLUMN project_id INTEGER REFERENCES projects(id)")
                    if "note_kind" not in columns:
                        self.connection.execute("ALTER TABLE notes ADD COLUMN note_kind TEXT NOT NULL DEFAULT 'note'")

                    now = utc_now_iso()
                    existing = self.connection.execute("SELECT id FROM projects ORDER BY id LIMIT 1").fetchone()
                    if existing is None:
                        cur = self.connection.execute(
                            "INSERT INTO projects(uuid, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                            (uuid.uuid4().hex, "Personal", now, now),
                        )
                        default_project_id = int(cur.lastrowid)
                    else:
                        default_project_id = int(existing["id"])
                    self.connection.execute(
                        "UPDATE notes SET project_id = ? WHERE project_id IS NULL", (default_project_id,)
                    )
                    for row in self.connection.execute("SELECT id FROM notes WHERE uuid IS NULL OR uuid = ''").fetchall():
                        self.connection.execute("UPDATE notes SET uuid = ? WHERE id = ?", (uuid.uuid4().hex, row["id"]))
                    self.connection.executescript(
                        """
                        CREATE INDEX IF NOT EXISTS idx_notes_project_updated
                            ON notes(project_id, is_deleted, updated_at DESC);
                        PRAGMA user_version = 2;
                        """
                    )
                version = 2

            if version < 3:
                with self.connection:
                    self.connection.executescript(
                        """
                        CREATE TABLE IF NOT EXISTS resource_links (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            note_id INTEGER NOT NULL,
                            repository_id INTEGER NOT NULL,
                            resource_type TEXT NOT NULL CHECK(resource_type IN ('repository','directory','file')),
                            resource_value TEXT NOT NULL DEFAULT '',
                            display_label TEXT NOT NULL DEFAULT '',
                            diagram_item_id TEXT,
                            baseline_sha TEXT,
                            last_checked_sha TEXT,
                            needs_review INTEGER NOT NULL DEFAULT 0 CHECK(needs_review IN (0,1)),
                            change_count INTEGER NOT NULL DEFAULT 0,
                            last_changed_at TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                            FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                        );
                        CREATE INDEX IF NOT EXISTS idx_resource_links_note ON resource_links(note_id);
                        CREATE INDEX IF NOT EXISTS idx_resource_links_repo ON resource_links(repository_id);
                        CREATE TABLE IF NOT EXISTS external_refs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            note_id INTEGER NOT NULL,
                            repository_id INTEGER NOT NULL,
                            ref_type TEXT NOT NULL CHECK(ref_type IN ('pull_request','commit','branch')),
                            ref_value TEXT NOT NULL,
                            title TEXT NOT NULL DEFAULT '',
                            url TEXT,
                            created_at TEXT NOT NULL,
                            FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                            FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
                            UNIQUE(note_id, repository_id, ref_type, ref_value)
                        );
                        CREATE INDEX IF NOT EXISTS idx_external_refs_note ON external_refs(note_id);
                        CREATE TABLE IF NOT EXISTS repository_changes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            repository_id INTEGER NOT NULL,
                            from_sha TEXT,
                            to_sha TEXT NOT NULL,
                            changed_files_json TEXT NOT NULL DEFAULT '[]',
                            commit_count INTEGER NOT NULL DEFAULT 0,
                            detected_at TEXT NOT NULL,
                            FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                        );
                        CREATE INDEX IF NOT EXISTS idx_repository_changes_repo
                            ON repository_changes(repository_id, detected_at DESC);
                        PRAGMA user_version = 3;
                        """
                    )
                version = 3

            if version < 4:
                with self.connection:
                    self.connection.executescript(
                        """
                        CREATE TABLE IF NOT EXISTS review_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            note_id INTEGER NOT NULL,
                            repository_id INTEGER NOT NULL,
                            reviewed_sha TEXT NOT NULL,
                            reviewed_at TEXT NOT NULL,
                            FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                            FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                        );
                        CREATE INDEX IF NOT EXISTS idx_review_events_note
                            ON review_events(note_id, reviewed_at DESC);
                        PRAGMA user_version = 4;
                        """
                    )
                version = 4

            if version < 5:
                with self.connection:
                    columns = {row[1] for row in self.connection.execute("PRAGMA table_info(repositories)")}
                    if "github_installation_id" not in columns:
                        self.connection.execute("ALTER TABLE repositories ADD COLUMN github_installation_id INTEGER")
                    self.connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notes_uuid ON notes(uuid) WHERE uuid IS NOT NULL")
                    self.connection.execute("PRAGMA user_version = 5")
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database migration failed: {exc}") from exc

    def _backup_legacy_database(self) -> None:
        backup_path = self.path.with_name(f"{self.path.stem}.pre-v2.backup{self.path.suffix}")
        if backup_path.exists():
            return
        target = sqlite3.connect(backup_path)
        try:
            self.connection.backup(target)
        finally:
            target.close()

    @staticmethod
    def _note_from_row(row: sqlite3.Row) -> Note:
        keys = set(row.keys())
        return Note(
            id=int(row["id"]), title=str(row["title"]), content_html=str(row["content_html"]),
            content_plain=str(row["content_plain"]), created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]), is_deleted=bool(row["is_deleted"]),
            uuid=str(row["uuid"] or "") if "uuid" in keys else "",
            project_id=int(row["project_id"]) if "project_id" in keys and row["project_id"] is not None else None,
            note_kind=str(row["note_kind"] or "note") if "note_kind" in keys else "note",
        )

    @staticmethod
    def _project_from_row(row: sqlite3.Row) -> Project:
        return Project(int(row["id"]), str(row["uuid"]), str(row["name"]), str(row["created_at"]), str(row["updated_at"]))

    @staticmethod
    def _repo_from_row(row: sqlite3.Row) -> Repository:
        return Repository(
            id=int(row["id"]), project_id=int(row["project_id"]), uuid=str(row["uuid"]),
            provider=str(row["provider"]), local_path=str(row["local_path"]) if row["local_path"] else None,
            github_owner=str(row["github_owner"]) if row["github_owner"] else None,
            github_repo=str(row["github_repo"]) if row["github_repo"] else None,
            github_installation_id=int(row["github_installation_id"]) if "github_installation_id" in row.keys() and row["github_installation_id"] is not None else None,
            default_branch=str(row["default_branch"]) if row["default_branch"] else None,
            last_seen_sha=str(row["last_seen_sha"]) if row["last_seen_sha"] else None,
            last_scanned_at=str(row["last_scanned_at"]) if row["last_scanned_at"] else None,
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _resource_from_row(row: sqlite3.Row) -> ResourceLink:
        return ResourceLink(
            id=int(row["id"]), note_id=int(row["note_id"]), repository_id=int(row["repository_id"]),
            resource_type=str(row["resource_type"]), resource_value=str(row["resource_value"]),
            display_label=str(row["display_label"]), diagram_item_id=str(row["diagram_item_id"]) if row["diagram_item_id"] else None,
            baseline_sha=str(row["baseline_sha"]) if row["baseline_sha"] else None,
            last_checked_sha=str(row["last_checked_sha"]) if row["last_checked_sha"] else None,
            needs_review=bool(row["needs_review"]), change_count=int(row["change_count"]),
            last_changed_at=str(row["last_changed_at"]) if row["last_changed_at"] else None,
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        )

    def create_project(self, name: str) -> Project:
        now = utc_now_iso()
        safe = name.strip() or "Untitled Project"
        with self.connection:
            cur = self.connection.execute(
                "INSERT INTO projects(uuid,name,created_at,updated_at) VALUES (?,?,?,?)",
                (uuid.uuid4().hex, safe, now, now),
            )
        return self.get_project(int(cur.lastrowid))  # type: ignore[return-value]

    def list_projects(self) -> list[Project]:
        return [self._project_from_row(r) for r in self.connection.execute("SELECT * FROM projects ORDER BY name COLLATE NOCASE").fetchall()]

    def get_project(self, project_id: int) -> Project | None:
        row = self.connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return self._project_from_row(row) if row else None

    def rename_project(self, project_id: int, name: str) -> None:
        with self.connection:
            self.connection.execute("UPDATE projects SET name=?, updated_at=? WHERE id=?", (name.strip() or "Untitled Project", utc_now_iso(), project_id))

    def delete_project(self, project_id: int) -> None:
        count = int(self.connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0])
        if count <= 1:
            raise DatabaseError("DevNest must keep at least one project.")
        fallback = self.connection.execute("SELECT id FROM projects WHERE id<>? ORDER BY id LIMIT 1", (project_id,)).fetchone()
        if fallback is None:
            raise DatabaseError("No fallback project exists.")
        with self.connection:
            self.connection.execute("UPDATE notes SET project_id=? WHERE project_id=?", (int(fallback["id"]), project_id))
            self.connection.execute("DELETE FROM projects WHERE id=?", (project_id,))

    def add_repository(self, project_id: int, *, local_path: str | None = None, github_owner: str | None = None,
                       github_repo: str | None = None, github_installation_id: int | None = None,
                       default_branch: str | None = None, provider: str = "git") -> Repository:
        now = utc_now_iso()
        with self.connection:
            cur = self.connection.execute(
                """INSERT INTO repositories(project_id,uuid,provider,local_path,github_owner,github_repo,github_installation_id,default_branch,
                   created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (project_id, uuid.uuid4().hex, provider, local_path, github_owner, github_repo, github_installation_id, default_branch, now, now),
            )
        return self.get_repository(int(cur.lastrowid))  # type: ignore[return-value]

    def list_repositories(self, project_id: int) -> list[Repository]:
        return [self._repo_from_row(r) for r in self.connection.execute("SELECT * FROM repositories WHERE project_id=? ORDER BY id", (project_id,)).fetchall()]

    def get_repository(self, repository_id: int) -> Repository | None:
        row = self.connection.execute("SELECT * FROM repositories WHERE id=?", (repository_id,)).fetchone()
        return self._repo_from_row(row) if row else None

    def update_repository(self, repository_id: int, **values: object) -> None:
        allowed = {"local_path", "github_owner", "github_repo", "github_installation_id", "default_branch", "last_seen_sha", "last_scanned_at"}
        fields = [(k, v) for k, v in values.items() if k in allowed]
        if not fields:
            return
        fields.append(("updated_at", utc_now_iso()))
        sql = "UPDATE repositories SET " + ", ".join(f"{key}=?" for key, _ in fields) + " WHERE id=?"
        with self.connection:
            self.connection.execute(sql, [value for _, value in fields] + [repository_id])

    def remove_repository(self, repository_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM repositories WHERE id=?", (repository_id,))

    def create_note(self, title: str = DEFAULT_NOTE_TITLE, content_html: str = "", content_plain: str = "",
                    project_id: int | None = None, note_kind: str = "note") -> Note:
        now = utc_now_iso()
        if project_id is None:
            project = self.connection.execute("SELECT id FROM projects ORDER BY id LIMIT 1").fetchone()
            if project is None:
                project_id = self.create_project("Personal").id
            else:
                project_id = int(project["id"])
        safe_title = title.strip() or DEFAULT_NOTE_TITLE
        kind = note_kind if note_kind in {"note", "decision"} else "note"
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """INSERT INTO notes(title,content_html,content_plain,created_at,updated_at,is_deleted,uuid,project_id,note_kind)
                       VALUES (?,?,?,?,?,0,?,?,?)""",
                    (safe_title, content_html, content_plain, now, now, uuid.uuid4().hex, project_id, kind),
                )
            note = self.get_note(int(cursor.lastrowid))
            if note is None:
                raise DatabaseError("Created note could not be reloaded.")
            return note
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not create note: {exc}") from exc

    def get_note(self, note_id: int, include_deleted: bool = False) -> Note | None:
        sql = "SELECT * FROM notes WHERE id = ?"
        if not include_deleted:
            sql += " AND is_deleted = 0"
        row = self.connection.execute(sql, (note_id,)).fetchone()
        return self._note_from_row(row) if row else None

    def update_note(self, note_id: int, title: str, content_html: str, content_plain: str) -> None:
        now = utc_now_iso(); safe_title = title.strip() or DEFAULT_NOTE_TITLE
        try:
            with self.connection:
                cursor = self.connection.execute(
                    "UPDATE notes SET title=?, content_html=?, content_plain=?, updated_at=? WHERE id=? AND is_deleted=0",
                    (safe_title, content_html, content_plain, now, note_id),
                )
            if cursor.rowcount == 0:
                raise DatabaseError("The note no longer exists or is in Trash.")
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save note: {exc}") from exc

    def set_note_kind(self, note_id: int, note_kind: str) -> None:
        if note_kind not in {"note", "decision"}:
            raise DatabaseError("Unknown document type.")
        with self.connection:
            self.connection.execute("UPDATE notes SET note_kind=?, updated_at=? WHERE id=?", (note_kind, utc_now_iso(), note_id))

    def move_note_to_project(self, note_id: int, project_id: int) -> None:
        with self.connection:
            self.connection.execute("UPDATE notes SET project_id=?, updated_at=? WHERE id=?", (project_id, utc_now_iso(), note_id))

    def rename_note(self, note_id: int, title: str) -> None:
        note = self.get_note(note_id)
        if note is None: raise DatabaseError("Note not found.")
        self.update_note(note_id, title, note.content_html, note.content_plain)

    def duplicate_note(self, note_id: int) -> Note:
        source = self.get_note(note_id)
        if source is None: raise DatabaseError("Note not found.")
        copy = self.create_note(f"{source.title} Copy", source.content_html, source.content_plain, source.project_id, source.note_kind)
        diagram = self.get_diagram(note_id)
        if diagram: self.save_diagram(copy.id, diagram)
        return copy

    def list_notes(self, search: str = "", sort: str = "updated", project_id: int | None = None) -> list[NoteSummary]:
        where = ["n.is_deleted = 0"]; params: list[object] = []
        if project_id is not None:
            where.append("n.project_id = ?"); params.append(project_id)
        term = search.strip()
        if term:
            where.append("(n.title LIKE ? COLLATE NOCASE OR n.content_plain LIKE ? COLLATE NOCASE)")
            like = f"%{term}%"; params.extend([like, like])
        order_by = "n.updated_at DESC" if sort == "updated" else "n.title COLLATE NOCASE ASC, n.updated_at DESC"
        rows = self.connection.execute(
            f"""SELECT n.id,n.title,substr(replace(replace(n.content_plain,char(10),' '),char(13),' '),1,140) preview,
                n.created_at,n.updated_at,n.is_deleted,n.project_id,n.note_kind,
                EXISTS(SELECT 1 FROM resource_links r WHERE r.note_id=n.id AND r.needs_review=1) needs_review
                FROM notes n WHERE {' AND '.join(where)} ORDER BY {order_by}""", params).fetchall()
        return [NoteSummary(int(r["id"]), str(r["title"]), str(r["preview"] or ""), str(r["created_at"]), str(r["updated_at"]),
                            bool(r["is_deleted"]), int(r["project_id"]) if r["project_id"] is not None else None,
                            str(r["note_kind"] or "note"), bool(r["needs_review"])) for r in rows]

    def list_trash(self) -> list[NoteSummary]:
        rows = self.connection.execute(
            """SELECT n.id,n.title,substr(replace(replace(n.content_plain,char(10),' '),char(13),' '),1,140) preview,
               n.created_at,n.updated_at,n.is_deleted,n.project_id,n.note_kind,
               EXISTS(SELECT 1 FROM resource_links r WHERE r.note_id=n.id AND r.needs_review=1) needs_review
               FROM notes n WHERE n.is_deleted=1 ORDER BY n.updated_at DESC""").fetchall()
        return [NoteSummary(int(r["id"]),str(r["title"]),str(r["preview"] or ""),str(r["created_at"]),str(r["updated_at"]),True,
                            int(r["project_id"]) if r["project_id"] is not None else None,str(r["note_kind"] or "note"),bool(r["needs_review"])) for r in rows]

    def soft_delete_note(self, note_id: int) -> None:
        with self.connection: self.connection.execute("UPDATE notes SET is_deleted=1,updated_at=? WHERE id=?", (utc_now_iso(), note_id))

    def restore_note(self, note_id: int) -> None:
        with self.connection: self.connection.execute("UPDATE notes SET is_deleted=0,updated_at=? WHERE id=?", (utc_now_iso(), note_id))

    def permanently_delete_note(self, note_id: int) -> None:
        with self.connection: self.connection.execute("DELETE FROM notes WHERE id=? AND is_deleted=1", (note_id,))

    def empty_trash(self) -> int:
        with self.connection: cursor = self.connection.execute("DELETE FROM notes WHERE is_deleted=1")
        return int(cursor.rowcount)

    def save_diagram(self, note_id: int, data: dict[str, object] | str) -> None:
        data_json = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        now = utc_now_iso()
        with self.connection:
            self.connection.execute("""INSERT INTO diagrams(note_id,data_json,updated_at) VALUES (?,?,?)
                ON CONFLICT(note_id) DO UPDATE SET data_json=excluded.data_json,updated_at=excluded.updated_at""", (note_id, data_json, now))

    def get_diagram(self, note_id: int) -> dict[str, object]:
        row = self.connection.execute("SELECT data_json FROM diagrams WHERE note_id=?", (note_id,)).fetchone()
        if not row: return {"items": [], "edges": [], "paths": []}
        try:
            data = json.loads(str(row["data_json"])); return data if isinstance(data, dict) else {"items": [], "edges": [], "paths": []}
        except json.JSONDecodeError:
            return {"items": [], "edges": [], "paths": []}

    def add_resource_link(self, note_id: int, repository_id: int, resource_type: str, resource_value: str,
                          display_label: str = "", diagram_item_id: str | None = None, baseline_sha: str | None = None) -> ResourceLink:
        if resource_type not in {"repository", "directory", "file"}: raise DatabaseError("Unsupported resource link type.")
        value = resource_value.replace("\\", "/").strip("/") if resource_type != "repository" else ""
        now = utc_now_iso(); label = display_label.strip() or (value or "Repository")
        with self.connection:
            cur = self.connection.execute(
                """INSERT INTO resource_links(note_id,repository_id,resource_type,resource_value,display_label,diagram_item_id,
                   baseline_sha,last_checked_sha,needs_review,change_count,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,0,0,?,?)""",
                (note_id, repository_id, resource_type, value, label, diagram_item_id, baseline_sha, baseline_sha, now, now))
        return self.get_resource_link(int(cur.lastrowid))  # type: ignore[return-value]

    def get_resource_link(self, link_id: int) -> ResourceLink | None:
        row = self.connection.execute("SELECT * FROM resource_links WHERE id=?", (link_id,)).fetchone()
        return self._resource_from_row(row) if row else None

    def list_resource_links(self, note_id: int) -> list[ResourceLink]:
        return [self._resource_from_row(r) for r in self.connection.execute("SELECT * FROM resource_links WHERE note_id=? ORDER BY id", (note_id,)).fetchall()]

    def remove_resource_link(self, link_id: int) -> None:
        with self.connection: self.connection.execute("DELETE FROM resource_links WHERE id=?", (link_id,))

    def mark_link_changed(self, link_id: int, checked_sha: str, change_count: int) -> None:
        now = utc_now_iso()
        with self.connection:
            self.connection.execute("""UPDATE resource_links SET last_checked_sha=?, needs_review=1,
                change_count=?, last_changed_at=?, updated_at=? WHERE id=?""", (checked_sha, max(1, change_count), now, now, link_id))

    def mark_link_checked(self, link_id: int, checked_sha: str) -> None:
        with self.connection:
            self.connection.execute("UPDATE resource_links SET last_checked_sha=?,updated_at=? WHERE id=?", (checked_sha, utc_now_iso(), link_id))

    def mark_note_reviewed(self, note_id: int, repository_id: int, sha: str) -> None:
        now = utc_now_iso()
        with self.connection:
            self.connection.execute("""UPDATE resource_links SET baseline_sha=?,last_checked_sha=?,needs_review=0,change_count=0,
                last_changed_at=NULL,updated_at=? WHERE note_id=? AND repository_id=?""", (sha, sha, now, note_id, repository_id))
            self.connection.execute("INSERT INTO review_events(note_id,repository_id,reviewed_sha,reviewed_at) VALUES (?,?,?,?)", (note_id, repository_id, sha, now))

    def add_external_ref(self, note_id: int, repository_id: int, ref_type: str, ref_value: str, title: str = "", url: str | None = None) -> ExternalRef:
        if ref_type not in {"pull_request", "commit", "branch"}: raise DatabaseError("Unsupported reference type.")
        with self.connection:
            self.connection.execute("""INSERT INTO external_refs(note_id,repository_id,ref_type,ref_value,title,url,created_at)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(note_id,repository_id,ref_type,ref_value)
                DO UPDATE SET title=excluded.title,url=excluded.url""", (note_id, repository_id, ref_type, ref_value, title, url, utc_now_iso()))
        row = self.connection.execute("SELECT * FROM external_refs WHERE note_id=? AND repository_id=? AND ref_type=? AND ref_value=?",
                                      (note_id, repository_id, ref_type, ref_value)).fetchone()
        return ExternalRef(int(row["id"]), int(row["note_id"]), int(row["repository_id"]), str(row["ref_type"]), str(row["ref_value"]), str(row["title"]), str(row["url"]) if row["url"] else None, str(row["created_at"]))

    def list_external_refs(self, note_id: int) -> list[ExternalRef]:
        rows = self.connection.execute("SELECT * FROM external_refs WHERE note_id=? ORDER BY id", (note_id,)).fetchall()
        return [ExternalRef(int(r["id"]),int(r["note_id"]),int(r["repository_id"]),str(r["ref_type"]),str(r["ref_value"]),str(r["title"]),str(r["url"]) if r["url"] else None,str(r["created_at"])) for r in rows]

    def remove_external_ref(self, ref_id: int) -> None:
        with self.connection: self.connection.execute("DELETE FROM external_refs WHERE id=?", (ref_id,))

    def record_repository_change(self, repository_id: int, from_sha: str | None, to_sha: str, changed_files: list[str], commit_count: int) -> None:
        with self.connection:
            self.connection.execute("INSERT INTO repository_changes(repository_id,from_sha,to_sha,changed_files_json,commit_count,detected_at) VALUES (?,?,?,?,?,?)",
                                    (repository_id, from_sha, to_sha, json.dumps(changed_files, ensure_ascii=False), commit_count, utc_now_iso()))

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone(); return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connection: self.connection.execute("INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def optimize(self) -> None:
        try: self.connection.execute("VACUUM")
        except sqlite3.Error as exc: raise DatabaseError(f"Could not optimize database: {exc}") from exc

    def close(self) -> None:
        try: self.connection.close()
        except sqlite3.Error: pass

    def __enter__(self) -> "Database": return self
    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: self.close()
````

## `app/dialogs/__init__.py`

````python

````

## `app/dialogs/github.py`

````python
from __future__ import annotations

import time
import webbrowser

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout,
)

from app.services.github_client import GitHubAuthorizationPending, GitHubClient, GitHubError, GitHubSlowDown


class GitHubConnectDialog(QDialog):
    def __init__(self, client: GitHubClient, parent=None) -> None:
        super().__init__(parent)
        self.client = client
        self.device = None
        self.deadline = 0.0
        self.setWindowTitle("Connect GitHub")
        self.setMinimumWidth(480)
        root = QVBoxLayout(self)
        intro = QLabel("DevNest uses GitHub Device Flow. Your browser handles authorization; DevNest never asks for your GitHub password.")
        intro.setWordWrap(True); root.addWidget(intro)
        self.code = QLineEdit(); self.code.setReadOnly(True); self.code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code.setStyleSheet("font-size: 22px; font-weight: 700; letter-spacing: 2px; padding: 8px;")
        root.addWidget(self.code)
        row = QHBoxLayout(); self.open_button = QPushButton("Open GitHub"); self.open_button.clicked.connect(self._open)
        self.start_button = QPushButton("Generate code"); self.start_button.clicked.connect(self.start)
        row.addWidget(self.start_button); row.addWidget(self.open_button); root.addLayout(row)
        self.status = QLabel("Generate a code to begin."); self.status.setWordWrap(True); root.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel); buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.timer = QTimer(self); self.timer.timeout.connect(self._poll)
        QTimer.singleShot(0, self.start)

    def start(self) -> None:
        try:
            self.device = self.client.start_device_flow(); self.deadline = time.monotonic() + self.device.expires_in
            self.code.setText(self.device.user_code); self.status.setText("Enter this code on GitHub, then approve DevNest.")
            self.timer.start(max(5, self.device.interval) * 1000)
        except GitHubError as exc:
            self.status.setText(str(exc)); self.timer.stop()

    def _open(self) -> None:
        if self.device: webbrowser.open(self.device.verification_uri)

    def _poll(self) -> None:
        if not self.device: return
        if time.monotonic() >= self.deadline:
            self.timer.stop(); self.status.setText("Code expired. Generate a new code."); return
        try:
            self.client.poll_device_flow(self.device.device_code)
            user = self.client.authenticated_user(); self.timer.stop()
            self.status.setText(f"Connected as @{user.get('login', 'GitHub user')}"); QTimer.singleShot(400, self.accept)
        except GitHubAuthorizationPending:
            self.status.setText("Waiting for GitHub authorization…")
        except GitHubSlowDown:
            self.timer.setInterval(self.timer.interval() + 5000)
        except GitHubError as exc:
            self.timer.stop(); self.status.setText(str(exc))


class GitHubRepositoryDialog(QDialog):
    def __init__(self, client: GitHubClient, parent=None, install_url: str = "") -> None:
        super().__init__(parent)
        self.client = client; self.repositories: list[dict[str, object]] = []
        self.setWindowTitle("GitHub Repositories"); self.resize(700, 560)
        root = QVBoxLayout(self)
        top = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("Search repositories…")
        refresh = QPushButton("Refresh"); refresh.clicked.connect(self.load)
        top.addWidget(self.search, 1); top.addWidget(refresh)
        if install_url:
            manage = QPushButton("Manage GitHub access"); manage.clicked.connect(lambda: webbrowser.open(install_url)); top.addWidget(manage)
        root.addLayout(top)
        self.list = QListWidget(); self.list.itemDoubleClicked.connect(lambda _item, _column: self.accept()); root.addWidget(self.list, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.search.textChanged.connect(self._filter); QTimer.singleShot(0, self.load)

    def load(self) -> None:
        try: self.repositories = self.client.list_repositories()
        except GitHubError as exc:
            QMessageBox.warning(self, "GitHub", str(exc)); return
        self._filter(self.search.text())
        if not self.repositories:
            item = QListWidgetItem("No DevNest GitHub App repositories are available. Install/manage the app access, then Refresh.")
            item.setFlags(Qt.ItemFlag.NoItemFlags); self.list.addItem(item)

    def _filter(self, text: str) -> None:
        term = text.strip().casefold(); self.list.clear()
        for repo in self.repositories:
            full = str(repo.get("full_name", ""))
            if term and term not in full.casefold(): continue
            privacy = "private" if repo.get("private") else "public"
            item = QListWidgetItem(f"{full}   ·   {privacy}   ·   {repo.get('default_branch', 'main')}")
            item.setData(Qt.ItemDataRole.UserRole, repo); self.list.addItem(item)

    def selected_repository(self) -> dict[str, object] | None:
        item = self.list.currentItem(); data = item.data(Qt.ItemDataRole.UserRole) if item else None
        return data if isinstance(data, dict) else None
````

## `app/dialogs/preferences.py`

````python
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
)

from app.constants import MAX_AUTOSAVE_DELAY_MS, MIN_AUTOSAVE_DELAY_MS
from app.settings import AppPreferences
from app.themes.theme_manager import THEME_OPTIONS


class PreferencesDialog(QDialog):
    def __init__(self, prefs: AppPreferences, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(420)
        root = QVBoxLayout(self)

        general = QGroupBox("General")
        general_form = QFormLayout(general)
        self.autosave = QCheckBox("Enable autosave")
        self.autosave.setChecked(prefs.autosave_enabled)
        self.autosave_delay = QSpinBox()
        self.autosave_delay.setRange(MIN_AUTOSAVE_DELAY_MS, MAX_AUTOSAVE_DELAY_MS)
        self.autosave_delay.setSingleStep(100)
        self.autosave_delay.setSuffix(" ms")
        self.autosave_delay.setValue(prefs.autosave_delay_ms)
        self.start_last = QCheckBox("Start with last opened note")
        self.start_last.setChecked(prefs.start_with_last_note)
        general_form.addRow(self.autosave)
        general_form.addRow("Autosave delay:", self.autosave_delay)
        general_form.addRow(self.start_last)

        editor = QGroupBox("Editor")
        editor_form = QFormLayout(editor)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 36)
        self.font_size.setValue(prefs.editor_font_size)
        self.tab_width = QSpinBox()
        self.tab_width.setRange(2, 8)
        self.tab_width.setValue(prefs.tab_width)
        self.auto_checkbox = QCheckBox("Auto Checkbox by default")
        self.auto_checkbox.setChecked(prefs.auto_checkbox_default)
        self.blank_line_after_enter = QCheckBox("Double Enter")
        self.blank_line_after_enter.setChecked(prefs.blank_line_after_enter)
        self.blank_line_after_enter.setToolTip("When active, one Enter advances by two lines and leaves one empty line in between.")
        self.word_wrap = QCheckBox("Word wrap")
        self.word_wrap.setChecked(prefs.word_wrap)
        editor_form.addRow("Font size:", self.font_size)
        editor_form.addRow("Tab width (spaces):", self.tab_width)
        editor_form.addRow(self.auto_checkbox)
        editor_form.addRow(self.blank_line_after_enter)
        editor_form.addRow(self.word_wrap)

        appearance = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance)
        self.theme = QComboBox()
        for label, value in THEME_OPTIONS:
            self.theme.addItem(label, value)
        index = self.theme.findData(prefs.theme)
        self.theme.setCurrentIndex(max(0, index))
        appearance_form.addRow("Theme:", self.theme)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root.addWidget(general)
        root.addWidget(editor)
        root.addWidget(appearance)
        root.addWidget(buttons)

    def preferences(self) -> AppPreferences:
        return AppPreferences(
            theme=str(self.theme.currentData()),
            autosave_enabled=self.autosave.isChecked(),
            autosave_delay_ms=self.autosave_delay.value(),
            start_with_last_note=self.start_last.isChecked(),
            editor_font_size=self.font_size.value(),
            tab_width=self.tab_width.value(),
            auto_checkbox_default=self.auto_checkbox.isChecked(),
            blank_line_after_enter=self.blank_line_after_enter.isChecked(),
            word_wrap=self.word_wrap.isChecked(),
        )
````

## `app/dialogs/project.py`

````python
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from app.services.local_git import GitError, GitRepositoryInfo, inspect_repository


class ProjectDialog(QDialog):
    def __init__(self, parent=None, *, name: str = "", local_path: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(560)
        self.repo_info: GitRepositoryInfo | None = None

        root = QVBoxLayout(self)
        intro = QLabel("Create a local-first DevNest project. A Git repository is optional and can be attached later.")
        intro.setWordWrap(True); root.addWidget(intro)
        form = QFormLayout(); root.addLayout(form)
        self.name_edit = QLineEdit(name); self.name_edit.setPlaceholderText("Project name")
        form.addRow("Name", self.name_edit)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(local_path); self.path_edit.setPlaceholderText("C:\\Projects\\my-repo (optional)")
        browse = QPushButton("Browse…"); browse.clicked.connect(self._browse)
        inspect = QPushButton("Inspect Git"); inspect.clicked.connect(self._inspect)
        path_row.addWidget(self.path_edit, 1); path_row.addWidget(browse); path_row.addWidget(inspect)
        form.addRow("Local repository", path_row)

        self.detected = QLabel("No repository inspected yet.")
        self.detected.setWordWrap(True); root.addWidget(self.detected)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Git repository")
        if path:
            self.path_edit.setText(path)
            if not self.name_edit.text().strip(): self.name_edit.setText(Path(path).name)
            self._inspect()

    def _inspect(self) -> None:
        path = self.path_edit.text().strip()
        if not path:
            self.repo_info = None; self.detected.setText("Local repository is optional."); return
        try:
            self.repo_info = inspect_repository(path)
            remote = self.repo_info.remote_url or "No origin remote"
            self.detected.setText(
                f"✓ Git repository\nRoot: {self.repo_info.root}\nBranch: {self.repo_info.branch or 'detached'}\n"
                f"HEAD: {self.repo_info.head_sha[:12]}\nOrigin: {remote}"
            )
            self.path_edit.setText(str(self.repo_info.root))
            if not self.name_edit.text().strip(): self.name_edit.setText(self.repo_info.root.name)
        except GitError as exc:
            self.repo_info = None
            self.detected.setText(f"Not ready: {exc}")

    def _accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Project", "Enter a project name."); return
        if self.path_edit.text().strip() and self.repo_info is None:
            try: self.repo_info = inspect_repository(self.path_edit.text().strip())
            except GitError as exc:
                QMessageBox.warning(self, "Repository", f"The selected folder is not a usable Git repository.\n\n{exc}"); return
        self.accept()

    def values(self) -> tuple[str, GitRepositoryInfo | None]:
        return self.name_edit.text().strip(), self.repo_info
````

## `app/dialogs/shortcuts.py`

````python
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.constants import SHORTCUTS


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(480, 430)
        root = QVBoxLayout(self)
        table = QTableWidget(len(SHORTCUTS), 2)
        table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (name, shortcut) in enumerate(SHORTCUTS.items()):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(shortcut))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(lambda _button: self.accept())
        root.addWidget(table)
        root.addWidget(buttons)
````

## `app/dialogs/trash.py`

````python
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database import Database, DatabaseError


class TrashDialog(QDialog):
    def __init__(self, database: Database, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.changed = False
        self.setWindowTitle("Trash")
        self.resize(720, 420)
        root = QVBoxLayout(self)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Title", "Deleted / updated", "Preview"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        row = QHBoxLayout()
        restore = QPushButton("Restore")
        permanent = QPushButton("Permanently Delete")
        empty = QPushButton("Empty Trash")
        optimize = QPushButton("Optimize Database")
        close = QPushButton("Close")
        restore.clicked.connect(self.restore_selected)
        permanent.clicked.connect(self.permanently_delete_selected)
        empty.clicked.connect(self.empty_trash)
        optimize.clicked.connect(self.optimize_database)
        close.clicked.connect(self.accept)
        row.addWidget(restore)
        row.addWidget(permanent)
        row.addStretch(1)
        row.addWidget(empty)
        row.addWidget(optimize)
        row.addWidget(close)

        root.addWidget(self.table, 1)
        root.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        notes = self.database.list_trash()
        self.table.setRowCount(len(notes))
        for r, note in enumerate(notes):
            title = QTableWidgetItem(note.title)
            title.setData(Qt.ItemDataRole.UserRole, note.id)
            try:
                stamp = datetime.fromisoformat(note.updated_at).astimezone().strftime("%Y-%m-%d %H:%M")
            except ValueError:
                stamp = note.updated_at
            self.table.setItem(r, 0, title)
            self.table.setItem(r, 1, QTableWidgetItem(stamp))
            self.table.setItem(r, 2, QTableWidgetItem(note.preview))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def restore_selected(self) -> None:
        note_id = self._selected_id()
        if note_id is None:
            QMessageBox.information(self, "Trash", "Select a note first.")
            return
        try:
            self.database.restore_note(note_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Restore Failed", str(exc))

    def permanently_delete_selected(self) -> None:
        note_id = self._selected_id()
        if note_id is None:
            QMessageBox.information(self, "Trash", "Select a note first.")
            return
        answer = QMessageBox.warning(
            self,
            "Permanently Delete",
            "This permanently deletes the note and its diagram data. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.permanently_delete_note(note_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))

    def empty_trash(self) -> None:
        if not self.database.list_trash():
            QMessageBox.information(self, "Trash", "Trash is already empty.")
            return
        answer = QMessageBox.warning(
            self,
            "Empty Trash",
            "Permanently delete every note in Trash and its linked diagram data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            count = self.database.empty_trash()
            self.changed = True
            self.refresh()
            QMessageBox.information(self, "Trash", f"Permanently deleted {count} note(s).")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Empty Trash Failed", str(exc))

    def optimize_database(self) -> None:
        answer = QMessageBox.question(
            self,
            "Optimize Database",
            "Run SQLite VACUUM now? This can reduce the database file size after permanent deletions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.optimize()
            QMessageBox.information(self, "Optimize Database", "Database optimization completed.")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Optimize Failed", str(exc))
````

## `app/main_window.py`

````python
from __future__ import annotations

import logging
import re
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent, QFontDatabase, QKeySequence, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import APP_NAME, DEFAULT_NOTE_TITLE, GITHUB_APP_CLIENT_ID, GITHUB_APP_INSTALL_URL, SHORTCUTS, VERSION
from app.database import Database, DatabaseError
from app.dialogs.preferences import PreferencesDialog
from app.dialogs.project import ProjectDialog
from app.dialogs.github import GitHubConnectDialog, GitHubRepositoryDialog
from app.dialogs.shortcuts import ShortcutsDialog
from app.dialogs.trash import TrashDialog
from app.models import Note, Repository
from app.paths import database_path
from app.services.github_client import GitHubClient, GitHubError
from app.services.local_git import GitError, current_head, default_branch, inspect_repository, recent_commits
from app.services.repository_scanner import RepositoryScanner
from app.services.txt_codec import (
    export_internal_plain_text,
    import_text_to_html,
    parse_text,
    parsed_to_internal_text,
    read_utf8_text,
    write_utf8_text,
)
from app.settings import AppPreferences, SettingsManager
from app.themes.theme_manager import THEME_OPTIONS, ThemeManager
from app.widgets.context_panel import ContextPanel
from app.widgets.diagram_view import DiagramView
from app.widgets.note_editor import NoteEditor
from app.widgets.sidebar import Sidebar

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        database: Database,
        settings: SettingsManager,
        theme_manager: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.settings = settings
        self.theme_manager = theme_manager
        self.preferences = self.settings.preferences()
        self.current_project_id: int | None = None
        self.current_note_id: int | None = None
        self.github_client_id = str(self.settings.value("github/client_id", GITHUB_APP_CLIENT_ID) or GITHUB_APP_CLIENT_ID).strip()
        self.github = GitHubClient(self.github_client_id) if self.github_client_id else None
        self.scanner = RepositoryScanner(self.database, self.github)
        self._loading_note = False
        self._dirty = False
        self._diagram_dirty = False
        self._search_term = ""
        self._sort_mode = "updated"

        self.setWindowTitle(f"{APP_NAME} — Engineering Context")
        self.setMinimumSize(840, 560)
        self.resize(1220, 760)
        self.setAcceptDrops(True)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.save_current_note)
        self.diagram_timer = QTimer(self)
        self.diagram_timer.setSingleShot(True)
        self.diagram_timer.timeout.connect(self.save_current_diagram)
        self.repository_scan_timer = QTimer(self)
        self.repository_scan_timer.setInterval(120_000)
        self.repository_scan_timer.timeout.connect(self._auto_scan_current_project)

        self._build_ui()
        self._create_actions()
        self._build_toolbar()
        self._build_menus()
        self._connect_signals()
        self._restore_window_state()
        self._apply_preferences(self.preferences, persist=False)
        self._load_initial_note()
        self.repository_scan_timer.start()
        QTimer.singleShot(800, self._auto_scan_current_project)

    def _build_ui(self) -> None:
        self.sidebar = Sidebar()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(DEFAULT_NOTE_TITLE)
        self.title_edit.setStyleSheet("font-size: 18px; font-weight: 650; padding: 8px;")

        self.editor = NoteEditor()
        self.editor.setAcceptDrops(False)
        self.diagram = DiagramView()
        self.context = ContextPanel()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.editor, "Editor")
        self.tabs.addTab(self.diagram, "Diagram")
        self.tabs.addTab(self.context, "Context")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 6)
        content_layout.setSpacing(6)
        content_layout.addWidget(self.title_edit)
        content_layout.addWidget(self.tabs, 1)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(content)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([280, 940])

        self.workspace_bar = QWidget()
        self.workspace_bar.setObjectName("workspaceBar")
        self.workspace_layout = QHBoxLayout(self.workspace_bar)
        self.workspace_layout.setContentsMargins(8, 5, 8, 5)
        self.workspace_layout.setSpacing(6)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.workspace_bar)
        central_layout.addWidget(self.splitter, 1)
        self.setCentralWidget(central)

        self.save_label = QLabel("Saved")
        self.stats_label = QLabel("Words: 0  •  Lines: 1  •  Ln 1, Col 1")
        self.statusBar().addWidget(self.save_label)
        self.statusBar().addPermanentWidget(self.stats_label)

    def _create_actions(self) -> None:
        self.new_action = QAction("New Note", self)
        self.new_action.setShortcut(SHORTCUTS["New Note"])
        self.new_action.setToolTip("Create a new note")
        self.new_action.triggered.connect(self.new_note)

        self.delete_action = QAction("Delete", self)
        self.delete_action.setToolTip("Move the current note to Trash")
        self.delete_action.triggered.connect(lambda: self.delete_note(self.current_note_id) if self.current_note_id else None)

        self.import_action = QAction("Import TXT", self)
        self.import_action.triggered.connect(self.import_txt)

        self.export_action = QAction("Export TXT", self)
        self.export_action.setShortcut(SHORTCUTS["Export TXT"])
        self.export_action.triggered.connect(lambda: self.export_note(self.current_note_id) if self.current_note_id else None)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.editor.redo)
        self.cut_action = QAction("Cut", self)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action = QAction("Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action = QAction("Paste", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.editor.paste)
        self.select_all_action = QAction("Select All", self)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.select_all_action.triggered.connect(self.editor.selectAll)
        self.find_action = QAction("Find", self)
        self.find_action.setShortcut(SHORTCUTS["Find in Note"])
        self.find_action.triggered.connect(self.find_in_note)

        self.checkbox_action = QAction("Checkbox", self)
        self.checkbox_action.setShortcut(SHORTCUTS["Checkbox"])
        self.checkbox_action.triggered.connect(self.editor.insert_checkbox)
        self.auto_checkbox_action = QAction("Auto Checkbox", self)
        self.auto_checkbox_action.setCheckable(True)
        self.auto_checkbox_action.toggled.connect(self._set_auto_checkbox)
        self.blank_line_enter_action = QAction("Double Enter", self)
        self.blank_line_enter_action.setCheckable(True)
        self.blank_line_enter_action.setToolTip("When active, one Enter moves the cursor down by two lines")
        self.blank_line_enter_action.toggled.connect(self._set_blank_line_after_enter)

        self.bold_action = QAction("Bold", self)
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.triggered.connect(self.editor.toggle_bold)
        self.italic_action = QAction("Italic", self)
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.triggered.connect(self.editor.toggle_italic)
        self.underline_action = QAction("Underline", self)
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.triggered.connect(self.editor.toggle_underline)
        self.strike_action = QAction("Strikethrough", self)
        self.strike_action.triggered.connect(self.editor.toggle_strikethrough)
        self.bullet_action = QAction("Bullet List", self)
        self.bullet_action.triggered.connect(self.editor.make_bullet_list)
        self.numbered_action = QAction("List Mode", self)
        self.numbered_action.setCheckable(True)
        self.numbered_action.setToolTip("Write 1., 2., 3. ... as real text and continue numbering with Enter")
        self.numbered_action.toggled.connect(self._set_numbered_list_mode)

        self.toggle_sidebar_action = QAction("Toggle Sidebar", self)
        self.toggle_sidebar_action.setShortcut(SHORTCUTS["Toggle Sidebar"])
        self.toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        self.editor_tab_action = QAction("Editor", self)
        self.editor_tab_action.setShortcut(SHORTCUTS["Editor Tab"])
        self.editor_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        self.diagram_tab_action = QAction("Diagram", self)
        self.diagram_tab_action.setShortcut(SHORTCUTS["Diagram Tab"])
        self.diagram_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        self.context_tab_action = QAction("Context", self)
        self.context_tab_action.setShortcut("Ctrl+3")
        self.context_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))

        self.new_project_action = QAction("New Project…", self)
        self.new_project_action.triggered.connect(self.new_project)
        self.scan_project_action = QAction("Scan Project", self)
        self.scan_project_action.triggered.connect(self.scan_current_project)
        self.connect_github_action = QAction("Connect GitHub…", self)
        self.connect_github_action.triggered.connect(self.connect_github)
        self.github_repositories_action = QAction("GitHub Repositories…", self)
        self.github_repositories_action.triggered.connect(self.import_github_repository)

        self.preferences_action = QAction("Preferences…", self)
        self.preferences_action.triggered.connect(self.open_preferences)
        self.trash_action = QAction("Trash…", self)
        self.trash_action.triggered.connect(self.open_trash)
        self.shortcuts_action = QAction("Keyboard Shortcuts", self)
        self.shortcuts_action.triggered.connect(lambda: ShortcutsDialog(self).exec())
        self.about_action = QAction("About DevNest", self)
        self.about_action.triggered.connect(self.show_about)

    def _build_toolbar(self) -> None:
        # Two compact rows avoid Qt's overflow "..." extension button even on
        # smaller windows. Workspace navigation is a permanent bar below them.
        notes_toolbar = QToolBar("Notes & Format", self)
        notes_toolbar.setMovable(False)
        notes_toolbar.setFloatable(False)
        notes_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(notes_toolbar)
        for action in [self.new_action, self.delete_action, self.import_action, self.export_action]:
            notes_toolbar.addAction(action)
        notes_toolbar.addSeparator()
        notes_toolbar.addAction(self.checkbox_action)
        notes_toolbar.addAction(self.auto_checkbox_action)
        notes_toolbar.addAction(self.numbered_action)
        notes_toolbar.addAction(self.blank_line_enter_action)
        notes_toolbar.addSeparator()
        for action in [self.bold_action, self.italic_action, self.strike_action, self.bullet_action]:
            notes_toolbar.addAction(action)

        self.addToolBarBreak()
        text_toolbar = QToolBar("Text", self)
        text_toolbar.setMovable(False)
        text_toolbar.setFloatable(False)
        text_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(text_toolbar)

        self.font_combo = QComboBox()
        self.font_combo.setMinimumWidth(138)
        self.font_combo.setMaximumWidth(190)
        self.font_combo.setToolTip("Font family for selected text or new text")
        self._populate_font_combo()
        self.font_combo.currentIndexChanged.connect(self._apply_font_family_from_toolbar)
        text_toolbar.addWidget(self.font_combo)

        self.font_size_label = QLabel("12 pt")
        self.font_size_label.setMinimumWidth(36)
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 36)
        self.font_size_slider.setSingleStep(1)
        self.font_size_slider.setPageStep(2)
        self.font_size_slider.setValue(12)
        self.font_size_slider.setFixedWidth(92)
        self.font_size_slider.setToolTip("Text size: 8–36 pt")
        self.font_size_slider.valueChanged.connect(self._apply_font_size_from_toolbar)
        text_toolbar.addWidget(self.font_size_label)
        text_toolbar.addWidget(self.font_size_slider)

        self.font_weight_label = QLabel("W 400")
        self.font_weight_label.setMinimumWidth(42)
        self.font_weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_weight_slider.setRange(100, 900)
        self.font_weight_slider.setSingleStep(100)
        self.font_weight_slider.setPageStep(100)
        self.font_weight_slider.setValue(400)
        self.font_weight_slider.setFixedWidth(92)
        self.font_weight_slider.setToolTip("Font weight: 100 thin – 900 black")
        self.font_weight_slider.valueChanged.connect(self._apply_font_weight_from_toolbar)
        text_toolbar.addWidget(self.font_weight_label)
        text_toolbar.addWidget(self.font_weight_slider)
        text_toolbar.addSeparator()
        text_toolbar.addAction(self.undo_action)
        text_toolbar.addAction(self.redo_action)

        # Always-visible workspace controls. They are not QToolBar overflow items,
        # so Qt never moves Editor / Diagram / Theme behind a three-dot button.
        self.editor_workspace_button = QPushButton("Editor")
        self.editor_workspace_button.setObjectName("workspaceButton")
        self.editor_workspace_button.setCheckable(True)
        self.editor_workspace_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.diagram_workspace_button = QPushButton("Diagram")
        self.diagram_workspace_button.setObjectName("workspaceButton")
        self.diagram_workspace_button.setCheckable(True)
        self.diagram_workspace_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.context_workspace_button = QPushButton("Context")
        self.context_workspace_button.setObjectName("workspaceButton")
        self.context_workspace_button.setCheckable(True)
        self.context_workspace_button.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        self.workspace_layout.addWidget(self.editor_workspace_button)
        self.workspace_layout.addWidget(self.diagram_workspace_button)
        self.workspace_layout.addWidget(self.context_workspace_button)
        self.workspace_layout.addStretch(1)
        theme_label = QLabel("Theme:")
        self.workspace_layout.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themePresetCombo")
        self.theme_combo.setToolTip("Choose a DevNest color theme")
        for label, value in THEME_OPTIONS:
            self.theme_combo.addItem(label, value)
        self.theme_combo.currentIndexChanged.connect(self._theme_combo_changed)
        self.workspace_layout.addWidget(self.theme_combo)
        self._sync_workspace_buttons(self.tabs.currentIndex())

        # Defensive: if the platform style creates an extension button anyway,
        # keep it hidden. Both toolbars are deliberately short enough to fit.
        for toolbar in (notes_toolbar, text_toolbar):
            extension = toolbar.findChild(QToolButton, "qt_toolbar_ext_button")
            if extension is not None:
                extension.hide()

    def _populate_font_combo(self) -> None:
        available = {family.casefold(): family for family in QFontDatabase.families()}
        system_mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
        system_ui = QApplication.font().family()
        choices = [
            ("System Mono", system_mono),
            ("System UI", system_ui),
            ("Cascadia Code", "Cascadia Code"),
            ("Cascadia Mono", "Cascadia Mono"),
            ("Consolas", "Consolas"),
            ("JetBrains Mono", "JetBrains Mono"),
            ("Fira Code", "Fira Code"),
            ("Courier New", "Courier New"),
            ("Segoe UI", "Segoe UI"),
            ("Arial", "Arial"),
        ]
        used: set[str] = set()
        for label, requested in choices:
            family = available.get(requested.casefold())
            if family is None and requested in {system_mono, system_ui}:
                family = requested
            if not family or family.casefold() in used:
                continue
            used.add(family.casefold())
            self.font_combo.addItem(label, family)
        if self.font_combo.count() == 0:
            self.font_combo.addItem(system_mono, system_mono)

    def _apply_font_family_from_toolbar(self, _index: int) -> None:
        family = self.font_combo.currentData()
        if family:
            self.editor.apply_font_family(str(family))
            self.editor.setFocus()

    def _apply_font_size_from_toolbar(self, value: int) -> None:
        self.font_size_label.setText(f"{value} pt")
        self.editor.apply_font_point_size(value)
        self.editor.setFocus()

    def _apply_font_weight_from_toolbar(self, value: int) -> None:
        snapped = max(100, min(900, int(round(value / 100.0) * 100)))
        if snapped != value:
            self.font_weight_slider.blockSignals(True)
            self.font_weight_slider.setValue(snapped)
            self.font_weight_slider.blockSignals(False)
        self.font_weight_label.setText(f"W {snapped}")
        self.editor.apply_font_weight(snapped)
        self.editor.setFocus()

    def _sync_font_controls(self, fmt) -> None:
        size = int(round(fmt.fontPointSize())) if fmt.fontPointSize() > 0 else self.editor.base_font_size
        size = max(self.font_size_slider.minimum(), min(self.font_size_slider.maximum(), size))
        self.font_size_slider.blockSignals(True)
        self.font_size_slider.setValue(size)
        self.font_size_slider.blockSignals(False)
        self.font_size_label.setText(f"{size} pt")

        weight = int(fmt.fontWeight())
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        self.font_weight_slider.blockSignals(True)
        self.font_weight_slider.setValue(weight)
        self.font_weight_slider.blockSignals(False)
        self.font_weight_label.setText(f"W {weight}")

        families = fmt.font().families()
        family = families[0] if families else fmt.font().family()
        index = self.font_combo.findData(family)
        if index >= 0:
            self.font_combo.blockSignals(True)
            self.font_combo.setCurrentIndex(index)
            self.font_combo.blockSignals(False)

    def _build_menus(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.import_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.trash_action)
        file_menu.addAction(self.preferences_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        project_menu = menu.addMenu("Project")
        project_menu.addAction(self.new_project_action)
        project_menu.addAction(self.scan_project_action)
        project_menu.addSeparator()
        project_menu.addAction(self.connect_github_action)
        project_menu.addAction(self.github_repositories_action)

        edit_menu = menu.addMenu("Edit")
        for action in [self.undo_action, self.redo_action]:
            edit_menu.addAction(action)
        edit_menu.addSeparator()
        for action in [self.cut_action, self.copy_action, self.paste_action, self.select_all_action]:
            edit_menu.addAction(action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.find_action)

        view_menu = menu.addMenu("View")
        view_menu.addAction(self.toggle_sidebar_action)
        view_menu.addSeparator()
        view_menu.addAction(self.editor_tab_action)
        view_menu.addAction(self.diagram_tab_action)
        view_menu.addAction(self.context_tab_action)
        theme_menu = view_menu.addMenu("Theme")
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions: dict[str, QAction] = {}
        for label, value in THEME_OPTIONS:
            action = QAction(label, self, checkable=True)
            action.setData(value)
            action.triggered.connect(lambda _checked=False, t=value: self.set_theme(t))
            self.theme_group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[value] = action

        format_menu = menu.addMenu("Format")
        for action in [
            self.checkbox_action,
            self.auto_checkbox_action,
            self.blank_line_enter_action,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            self.strike_action,
            self.bullet_action,
            self.numbered_action,
        ]:
            format_menu.addAction(action)
        help_menu = menu.addMenu("Help")
        help_menu.addAction(self.shortcuts_action)
        help_menu.addAction(self.about_action)

    def _connect_signals(self) -> None:
        self.sidebar.noteSelected.connect(self.open_note)
        self.sidebar.newNoteRequested.connect(self.new_note)
        self.sidebar.trashRequested.connect(self.open_trash)
        self.sidebar.renameRequested.connect(self.rename_note)
        self.sidebar.duplicateRequested.connect(self.duplicate_note)
        self.sidebar.deleteRequested.connect(self.delete_note)
        self.sidebar.exportRequested.connect(self.export_note)
        self.sidebar.searchChanged.connect(self._on_search_changed)
        self.sidebar.sortChanged.connect(self._on_sort_changed)
        self.sidebar.projectSelected.connect(self.select_project)
        self.sidebar.newProjectRequested.connect(self.new_project)
        self.sidebar.projectMenuRequested.connect(self.open_project_menu)
        self.sidebar.scanRequested.connect(self.scan_current_project)
        self.sidebar.newDecisionRequested.connect(self.new_decision)

        self.context.documentKindChanged.connect(self._set_current_document_kind)
        self.context.scanRequested.connect(self.scan_current_project)
        self.context.markReviewedRequested.connect(self.mark_current_note_reviewed)
        self.context.addRepositoryLinkRequested.connect(lambda: self.add_resource_link("repository"))
        self.context.addDirectoryLinkRequested.connect(lambda: self.add_resource_link("directory"))
        self.context.addFileLinkRequested.connect(lambda: self.add_resource_link("file"))
        self.context.removeResourceRequested.connect(self.remove_resource_link)
        self.context.addCommitRequested.connect(self.add_commit_reference)
        self.context.addPullRequestRequested.connect(self.add_pull_request_reference)
        self.context.removeExternalRequested.connect(self.remove_external_reference)
        self.context.openResourceRequested.connect(self.open_linked_resource)

        self.title_edit.textChanged.connect(self._mark_content_dirty)
        self.editor.textChanged.connect(self._on_editor_changed)
        self.editor.cursorPositionChanged.connect(self._update_stats)
        self.editor.currentCharFormatChanged.connect(self._sync_font_controls)
        self.editor.taskStateChanged.connect(self._mark_content_dirty)
        self.editor.numberedListModeChanged.connect(self._sync_numbered_list_action)
        self.diagram.diagramChanged.connect(self._on_diagram_changed)
        self.tabs.currentChanged.connect(self._sync_workspace_buttons)
        color_scheme_changed = getattr(QApplication.styleHints(), "colorSchemeChanged", None)
        if color_scheme_changed is not None:
            color_scheme_changed.connect(self._on_system_color_scheme_changed)

    def _load_initial_note(self) -> None:
        projects = self.database.list_projects()
        if not projects:
            projects = [self.database.create_project("Personal")]
        stored = self.settings.value("session/last_project_id", None)
        try:
            stored_id = int(stored) if stored is not None else None
        except (TypeError, ValueError):
            stored_id = None
        ids = {project.id for project in projects}
        self.current_project_id = stored_id if stored_id in ids else projects[0].id
        self.sidebar.set_projects(projects, self.current_project_id)
        self._load_project_documents(preferred_note_id=self.settings.last_note_id())

    def _load_project_documents(self, preferred_note_id: int | None = None) -> None:
        if self.current_project_id is None:
            return
        notes = self.database.list_notes(sort=self._sort_mode, project_id=self.current_project_id)
        if not notes:
            created = self.database.create_note(project_id=self.current_project_id)
            notes = self.database.list_notes(sort=self._sort_mode, project_id=self.current_project_id)
            target = created.id
        else:
            ids = {note.id for note in notes}
            target = preferred_note_id if preferred_note_id in ids else notes[0].id
        self.sidebar.set_notes(notes, target)
        self.open_note(target)
        self.refresh_project_context()

    def refresh_projects(self, selected_id: int | None = None) -> None:
        projects = self.database.list_projects()
        self.sidebar.set_projects(projects, selected_id if selected_id is not None else self.current_project_id)

    def select_project(self, project_id: int) -> None:
        if project_id == self.current_project_id:
            return
        self.flush_pending_saves()
        if self.database.get_project(project_id) is None:
            return
        self.current_project_id = project_id
        self.current_note_id = None
        self.settings.set_value("session/last_project_id", project_id)
        self._search_term = ""
        self.sidebar.search.blockSignals(True)
        self.sidebar.search.clear()
        self.sidebar.search.blockSignals(False)
        self._load_project_documents()
        QTimer.singleShot(250, self._auto_scan_current_project)

    def refresh_sidebar(self, selected_id: int | None = None) -> None:
        notes = self.database.list_notes(self._search_term, self._sort_mode, self.current_project_id)
        self.sidebar.set_notes(notes, selected_id if selected_id is not None else self.current_note_id)

    def open_note(self, note_id: int) -> None:
        if note_id == self.current_note_id and not self._loading_note:
            self.refresh_context_panel()
            return
        self.flush_pending_saves()
        note = self.database.get_note(note_id)
        if note is None:
            self.refresh_sidebar()
            return
        if note.project_id is not None and note.project_id != self.current_project_id:
            self.current_project_id = note.project_id
            self.refresh_projects(note.project_id)
        self._loading_note = True
        try:
            self.current_note_id = note.id
            self.title_edit.setText(note.title)
            self.editor.setHtml(note.content_html) if note.content_html else self.editor.clear()
            self.diagram.load_data(self.database.get_diagram(note.id))
            self.context.set_kind(note.note_kind)
            self.settings.set_last_note_id(note.id)
            self._dirty = False
            self._diagram_dirty = False
            self.save_label.setText("Saved")
            self._update_stats()
            self.refresh_context_panel()
        finally:
            self._loading_note = False

    def new_note(self) -> None:
        self._create_document("note")

    def new_decision(self) -> None:
        self._create_document("decision")

    def _create_document(self, kind: str) -> None:
        self.flush_pending_saves()
        try:
            note = self.database.create_note(project_id=self.current_project_id, note_kind=kind)
            self._search_term = ""
            self.sidebar.search.clear()
            self.refresh_sidebar(note.id)
            self.open_note(note.id)
            self.title_edit.setFocus()
            self.title_edit.selectAll()
        except DatabaseError as exc:
            self._show_database_error(exc)

    def rename_note(self, note_id: int) -> None:
        note = self.database.get_note(note_id)
        if note is None:
            return
        title, ok = QInputDialog.getText(self, "Rename Note", "Title:", text=note.title)
        if not ok:
            return
        try:
            if note_id == self.current_note_id:
                self.title_edit.setText(title.strip() or DEFAULT_NOTE_TITLE)
                self.save_current_note()
            else:
                self.database.rename_note(note_id, title)
            self.refresh_sidebar(note_id)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def duplicate_note(self, note_id: int) -> None:
        self.flush_pending_saves()
        try:
            duplicate = self.database.duplicate_note(note_id)
            self.refresh_sidebar(duplicate.id)
            self.open_note(duplicate.id)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def delete_note(self, note_id: int | None) -> None:
        if note_id is None:
            return
        note = self.database.get_note(note_id)
        if note is None:
            return
        answer = QMessageBox.question(
            self,
            "Move to Trash",
            f'Move "{note.title}" to Trash? You can restore it later.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if note_id == self.current_note_id:
            self.flush_pending_saves()
        try:
            self.database.soft_delete_note(note_id)
            if note_id == self.current_note_id:
                self.current_note_id = None
            notes = self.database.list_notes(self._search_term, self._sort_mode, self.current_project_id)
            if not notes:
                created = self.database.create_note(project_id=self.current_project_id)
                notes = self.database.list_notes(self._search_term, self._sort_mode, self.current_project_id)
                target = created.id
            else:
                target = notes[0].id
            self.sidebar.set_notes(notes, target)
            self.open_note(target)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def open_trash(self) -> None:
        self.flush_pending_saves()
        dialog = TrashDialog(self.database, self)
        dialog.exec()
        if dialog.changed:
            self.refresh_sidebar(self.current_note_id)

    def save_current_note(self) -> None:
        self.autosave_timer.stop()
        if self._loading_note or not self._dirty or self.current_note_id is None:
            return
        try:
            title = self.title_edit.text().strip() or DEFAULT_NOTE_TITLE
            if self.title_edit.text() != title:
                self.title_edit.blockSignals(True)
                self.title_edit.setText(title)
                self.title_edit.blockSignals(False)
            self.database.update_note(
                self.current_note_id,
                title,
                self.editor.document().toHtml(),
                self.editor.toPlainText(),
            )
            self._dirty = False
            self.save_label.setText("Saved")
            self.refresh_sidebar(self.current_note_id)
        except DatabaseError as exc:
            self.save_label.setText("Save failed")
            logger.exception("Autosave failed")
            QMessageBox.critical(self, "Save Failed", str(exc))

    def save_current_diagram(self) -> None:
        self.diagram_timer.stop()
        if self._loading_note or not self._diagram_dirty or self.current_note_id is None:
            return
        try:
            self.database.save_diagram(self.current_note_id, self.diagram.to_data())
            self._diagram_dirty = False
        except DatabaseError as exc:
            logger.exception("Diagram save failed")
            QMessageBox.critical(self, "Diagram Save Failed", str(exc))

    def flush_pending_saves(self) -> None:
        self.save_current_note()
        self.save_current_diagram()
        self.settings.sync()

    def _mark_content_dirty(self) -> None:
        if self._loading_note:
            return
        self._dirty = True
        self.save_label.setText("Saving…" if self.preferences.autosave_enabled else "Modified")
        if self.preferences.autosave_enabled:
            self.autosave_timer.start(self.preferences.autosave_delay_ms)

    def _on_editor_changed(self) -> None:
        self._mark_content_dirty()
        self._update_stats()

    def _on_diagram_changed(self) -> None:
        if self._loading_note:
            return
        self._diagram_dirty = True
        self.diagram_timer.start(max(500, self.preferences.autosave_delay_ms))

    def _on_search_changed(self, text: str) -> None:
        self._search_term = text
        self.refresh_sidebar(self.current_note_id)

    def _on_sort_changed(self, mode: str) -> None:
        self._sort_mode = mode
        self.refresh_sidebar(self.current_note_id)

    def _update_stats(self) -> None:
        text = self.editor.toPlainText()
        words = len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))
        lines = max(1, self.editor.document().blockCount())
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.stats_label.setText(f"Words: {words}  •  Lines: {lines}  •  Ln {line}, Col {col}")

    def find_in_note(self) -> None:
        self.tabs.setCurrentIndex(0)
        self.editor.show_find_bar()

    def import_txt(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Import TXT", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            self._import_path(Path(filename))

    def _import_path(self, path: Path) -> None:
        if path.suffix.lower() != ".txt":
            QMessageBox.warning(self, "Import", "DevNest imports .txt files only.")
            return
        try:
            text = read_utf8_text(path)
            parsed = parse_text(text)
            html = import_text_to_html(text)
            plain = parsed_to_internal_text(parsed)
            note = self.database.create_note(path.stem or DEFAULT_NOTE_TITLE, html, plain, project_id=self.current_project_id)
            self._search_term = ""
            self.sidebar.search.clear()
            self.refresh_sidebar(note.id)
            self.open_note(note.id)
        except (OSError, UnicodeError, DatabaseError) as exc:
            logger.exception("TXT import failed for %s", path)
            QMessageBox.critical(self, "Import Failed", f"Could not import the file.\n\n{exc}")

    def export_note(self, note_id: int | None) -> None:
        if note_id is None:
            return
        if note_id == self.current_note_id:
            self.flush_pending_saves()
        note = self.database.get_note(note_id)
        if note is None:
            return
        default_name = self._safe_filename(note.title) + ".txt"
        filename, _ = QFileDialog.getSaveFileName(self, "Export Note as TXT", default_name, "Text Files (*.txt)")
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        if path.exists():
            answer = QMessageBox.question(
                self,
                "Overwrite File",
                f'"{path.name}" already exists. Overwrite it?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            if note_id == self.current_note_id:
                plain = self.editor.toPlainText()
            else:
                doc = QTextDocument()
                doc.setHtml(note.content_html)
                plain = doc.toPlainText()
            write_utf8_text(path, export_internal_plain_text(plain))
            self.statusBar().showMessage(f"Exported {path.name}", 3000)
        except OSError as exc:
            logger.exception("TXT export failed for %s", path)
            QMessageBox.critical(self, "Export Failed", f"Could not write the file.\n\n{exc}")

    @staticmethod
    def _safe_filename(title: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
        return cleaned[:100] or "Untitled Note"

    # --- Project / repository context -------------------------------------------------

    def _current_repository(self) -> Repository | None:
        if self.current_project_id is None:
            return None
        repos = self.database.list_repositories(self.current_project_id)
        return repos[0] if repos else None

    def refresh_project_context(self) -> None:
        repo = self._current_repository()
        self.context.set_repository(repo)
        project = self.database.get_project(self.current_project_id) if self.current_project_id else None
        if project:
            self.setWindowTitle(f"{APP_NAME} — {project.name}")
        self.refresh_context_panel()

    def refresh_context_panel(self) -> None:
        repo = self._current_repository()
        self.context.set_repository(repo)
        if self.current_note_id is None:
            self.context.set_data([], [])
            return
        note = self.database.get_note(self.current_note_id)
        if note:
            self.context.set_kind(note.note_kind)
        self.context.set_data(
            self.database.list_resource_links(self.current_note_id),
            self.database.list_external_refs(self.current_note_id),
        )

    def new_project(self) -> None:
        self.flush_pending_saves()
        dialog = ProjectDialog(self)
        if not dialog.exec():
            return
        name, info = dialog.values()
        try:
            project = self.database.create_project(name)
            if info is not None:
                branch = default_branch(info.root) or info.branch
                repo = self.database.add_repository(
                    project.id,
                    local_path=str(info.root),
                    github_owner=info.github_owner,
                    github_repo=info.github_repo,
                    default_branch=branch,
                )
                self.database.update_repository(repo.id, last_seen_sha=info.head_sha)
            self.current_project_id = project.id
            self.settings.set_value("session/last_project_id", project.id)
            self.refresh_projects(project.id)
            self.current_note_id = None
            self._load_project_documents()
        except (DatabaseError, GitError, Exception) as exc:
            logger.exception("Could not create project")
            QMessageBox.critical(self, "Project", f"Could not create the project.\n\n{exc}")

    def open_project_menu(self) -> None:
        menu = QMenu(self)
        new_action = menu.addAction("New Project…")
        rename_action = menu.addAction("Rename Project…")
        attach_action = menu.addAction("Attach Local Git Repository…")
        menu.addSeparator()
        connect_action = menu.addAction("Connect GitHub…")
        repos_action = menu.addAction("Import from GitHub Repositories…")
        scan_action = menu.addAction("Scan Linked Code")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Project…")
        button = self.sidebar.project_menu_button
        chosen = menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        if chosen == new_action:
            self.new_project()
        elif chosen == rename_action:
            self.rename_current_project()
        elif chosen == attach_action:
            self.attach_local_repository()
        elif chosen == connect_action:
            self.connect_github()
        elif chosen == repos_action:
            self.import_github_repository()
        elif chosen == scan_action:
            self.scan_current_project()
        elif chosen == delete_action:
            self.delete_current_project()

    def rename_current_project(self) -> None:
        if self.current_project_id is None:
            return
        project = self.database.get_project(self.current_project_id)
        if not project:
            return
        value, ok = QInputDialog.getText(self, "Rename Project", "Name:", text=project.name)
        if ok and value.strip():
            self.database.rename_project(project.id, value)
            self.refresh_projects(project.id)
            self.refresh_project_context()

    def delete_current_project(self) -> None:
        if self.current_project_id is None:
            return
        project = self.database.get_project(self.current_project_id)
        if not project:
            return
        answer = QMessageBox.question(
            self, "Delete Project",
            f'Delete project "{project.name}"? Its documents will be moved to another project; repository links for this project will be removed.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            old_id = project.id
            self.database.delete_project(old_id)
            projects = self.database.list_projects()
            self.current_project_id = projects[0].id
            self.current_note_id = None
            self.settings.set_value("session/last_project_id", self.current_project_id)
            self.refresh_projects(self.current_project_id)
            self._load_project_documents()
        except DatabaseError as exc:
            self._show_database_error(exc)

    def attach_local_repository(self) -> None:
        if self.current_project_id is None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Attach Local Git Repository")
        if not folder:
            return
        try:
            info = inspect_repository(folder)
            current = self._current_repository()
            branch = default_branch(info.root) or info.branch
            if current is None:
                repo = self.database.add_repository(
                    self.current_project_id, local_path=str(info.root), github_owner=info.github_owner,
                    github_repo=info.github_repo, default_branch=branch,
                )
            else:
                self.database.update_repository(
                    current.id, local_path=str(info.root), github_owner=info.github_owner,
                    github_repo=info.github_repo, default_branch=branch,
                )
                repo = self.database.get_repository(current.id)
            if repo:
                self.database.update_repository(repo.id, last_seen_sha=info.head_sha)
            self.refresh_project_context()
            self.statusBar().showMessage(f"Attached {info.root.name}", 3000)
        except (GitError, DatabaseError, Exception) as exc:
            QMessageBox.warning(self, "Repository", f"Could not attach this repository.\n\n{exc}")

    def _configure_github_client(self) -> bool:
        if not self.github_client_id:
            client_id, ok = QInputDialog.getText(
                self, "GitHub App Client ID",
                "Paste the Client ID from your DevNest GitHub App.\n(Device Flow must be enabled.)",
            )
            if not ok or not client_id.strip():
                return False
            self.github_client_id = client_id.strip()
            self.settings.set_value("github/client_id", self.github_client_id)
            self.settings.sync()
        self.github = GitHubClient(self.github_client_id)
        self.scanner = RepositoryScanner(self.database, self.github)
        return True

    def connect_github(self) -> bool:
        if not self._configure_github_client():
            return False
        assert self.github is not None
        try:
            if self.github.access_token():
                user = self.github.authenticated_user()
                answer = QMessageBox.question(
                    self, "GitHub",
                    f"Already connected as @{user.get('login', 'user')}. Reconnect?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer == QMessageBox.StandardButton.No:
                    return True
                self.github.disconnect()
        except GitHubError:
            self.github.disconnect()
        dialog = GitHubConnectDialog(self.github, self)
        if dialog.exec():
            try:
                user = self.github.authenticated_user()
                self.statusBar().showMessage(f"GitHub connected: @{user.get('login', 'user')}", 5000)
                return True
            except GitHubError as exc:
                QMessageBox.warning(self, "GitHub", str(exc))
        return False

    def import_github_repository(self) -> None:
        if not self._configure_github_client():
            return
        assert self.github is not None
        try:
            if not self.github.access_token() and not self.connect_github():
                return
        except GitHubError:
            if not self.connect_github():
                return
        dialog = GitHubRepositoryDialog(self.github, self, GITHUB_APP_INSTALL_URL)
        if not dialog.exec():
            return
        selected = dialog.selected_repository()
        if not selected:
            return
        full_name = str(selected.get("full_name", ""))
        if "/" not in full_name:
            return
        owner, repo_name = full_name.split("/", 1)
        try:
            project = self.database.create_project(repo_name)
            repo = self.database.add_repository(
                project.id, provider="github", github_owner=owner, github_repo=repo_name,
                github_installation_id=int(selected.get("_devnest_installation_id")) if selected.get("_devnest_installation_id") else None,
                default_branch=str(selected.get("default_branch") or "main"),
            )
            head, branch = self.github.branch_head(owner, repo_name, repo.default_branch)
            self.database.update_repository(repo.id, default_branch=branch, last_seen_sha=head)
            self.current_project_id = project.id
            self.current_note_id = None
            self.settings.set_value("session/last_project_id", project.id)
            self.refresh_projects(project.id)
            self._load_project_documents()
        except (DatabaseError, GitHubError, Exception) as exc:
            logger.exception("Could not import GitHub repository")
            QMessageBox.critical(self, "GitHub Repository", f"Could not create project from repository.\n\n{exc}")

    def _current_repo_head(self, repo: Repository) -> str:
        if repo.local_path and Path(repo.local_path).exists():
            sha = current_head(repo.local_path)
            if not repo.default_branch:
                self.database.update_repository(repo.id, default_branch=default_branch(repo.local_path))
            return sha
        if repo.github_owner and repo.github_repo:
            if self.github is None and not self._configure_github_client():
                raise GitHubError("GitHub is not configured.")
            assert self.github is not None
            if not self.github.access_token():
                raise GitHubError("GitHub is not connected.")
            sha, branch = self.github.branch_head(repo.github_owner, repo.github_repo, repo.default_branch)
            self.database.update_repository(repo.id, default_branch=branch)
            return sha
        raise GitError("No usable repository is attached to this project.")

    @staticmethod
    def _inside_repository(repo_root: Path, selected: Path) -> str:
        root = repo_root.resolve()
        target = selected.resolve()
        try:
            relative = target.relative_to(root)
        except ValueError as exc:
            raise GitError("Choose a file or folder inside the attached repository.") from exc
        return relative.as_posix()

    def add_resource_link(self, resource_type: str) -> None:
        if self.current_note_id is None:
            return
        repo = self._current_repository()
        if repo is None:
            QMessageBox.information(self, "Code Link", "Attach a Git repository to this project first.")
            return
        try:
            value = ""
            if resource_type in {"directory", "file"}:
                if repo.local_path and Path(repo.local_path).exists():
                    root = Path(repo.local_path)
                    if resource_type == "directory":
                        selected = QFileDialog.getExistingDirectory(self, "Link Repository Folder", str(root))
                    else:
                        selected, _ = QFileDialog.getOpenFileName(self, "Link Repository File", str(root), "All Files (*)")
                    if not selected:
                        return
                    value = self._inside_repository(root, Path(selected))
                else:
                    value, ok = QInputDialog.getText(
                        self, f"Link {resource_type.title()}",
                        f"Repository-relative {resource_type} path (example: src/auth/):",
                    )
                    if not ok or not value.strip():
                        return
                    value = value.strip().replace("\\", "/").strip("/")
            head = self._current_repo_head(repo)
            diagram_item_id = self.diagram.selected_item_id()
            label = repo.github_full_name or (Path(repo.local_path).name if repo.local_path else "Repository")
            if resource_type != "repository":
                label = value
            self.database.add_resource_link(
                self.current_note_id, repo.id, resource_type, value, str(label), diagram_item_id, head,
            )
            self.refresh_context_panel()
            self.refresh_sidebar(self.current_note_id)
            node_text = " to selected diagram node" if diagram_item_id else ""
            self.statusBar().showMessage(f"Linked {resource_type}{node_text} at {head[:10]}", 3500)
        except (DatabaseError, GitError, GitHubError) as exc:
            QMessageBox.warning(self, "Code Link", str(exc))

    def remove_resource_link(self, link_id: int) -> None:
        self.database.remove_resource_link(link_id)
        self.refresh_context_panel()
        self.refresh_sidebar(self.current_note_id)

    def mark_current_note_reviewed(self) -> None:
        if self.current_note_id is None:
            return
        repo = self._current_repository()
        if repo is None:
            return
        try:
            head = self._current_repo_head(repo)
            self.database.mark_note_reviewed(self.current_note_id, repo.id, head)
            self.refresh_context_panel()
            self.refresh_sidebar(self.current_note_id)
            self.statusBar().showMessage(f"Document reviewed at {head[:10]}", 3500)
        except (DatabaseError, GitError, GitHubError) as exc:
            QMessageBox.warning(self, "Review", str(exc))

    def _auto_scan_current_project(self) -> None:
        if self.current_project_id is None:
            return
        repos = self.database.list_repositories(self.current_project_id)
        if not repos:
            return
        # Never interrupt the user for credentials during a background check.
        if any(not repo.local_path and repo.github_owner for repo in repos):
            if self.github is None:
                return
            try:
                if not self.github.access_token():
                    return
            except GitHubError:
                return
        results = self.scanner.scan_project(self.current_project_id)
        if any(result.changed_links for result in results):
            self.refresh_sidebar(self.current_note_id)
            self.refresh_context_panel()
            changed = sum(result.changed_links for result in results)
            self.statusBar().showMessage(f"{changed} document code link(s) need review", 5000)
        for result in results:
            if result.error:
                logger.debug("Background repository scan skipped: %s", result.error)

    def scan_current_project(self) -> None:
        if self.current_project_id is None:
            return
        # A remote-only repository needs GitHub auth. Local repositories do not.
        repos = self.database.list_repositories(self.current_project_id)
        if not repos:
            QMessageBox.information(self, "Scan", "Attach a repository to this project first.")
            return
        if any(not repo.local_path and repo.github_owner for repo in repos):
            if self.github is None and not self._configure_github_client():
                return
            assert self.github is not None
            try:
                connected = bool(self.github.access_token())
            except GitHubError:
                connected = False
            if not connected and not self.connect_github():
                return
            self.scanner = RepositoryScanner(self.database, self.github)
        results = self.scanner.scan_project(self.current_project_id)
        errors = [result.error for result in results if result.error]
        changed = sum(result.changed_links for result in results)
        checked = sum(result.checked_links for result in results)
        self.refresh_sidebar(self.current_note_id)
        self.refresh_project_context()
        if errors:
            QMessageBox.warning(self, "Repository Scan", "\n\n".join(str(error) for error in errors))
        else:
            self.statusBar().showMessage(f"Scan complete: {checked} links checked, {changed} need review", 5000)

    def _set_current_document_kind(self, kind: str) -> None:
        if self._loading_note or self.current_note_id is None:
            return
        try:
            self.database.set_note_kind(self.current_note_id, kind)
            self.refresh_sidebar(self.current_note_id)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def add_commit_reference(self) -> None:
        if self.current_note_id is None:
            return
        repo = self._current_repository()
        if repo is None:
            QMessageBox.information(self, "Commit", "Attach a repository first.")
            return
        try:
            commits: list[tuple[str, str, str | None]] = []
            if repo.local_path and Path(repo.local_path).exists():
                for item in recent_commits(repo.local_path, 60):
                    sha = item["sha"]
                    title = item["title"]
                    url = f"https://github.com/{repo.github_full_name}/commit/{sha}" if repo.github_full_name else None
                    commits.append((sha, title, url))
            elif repo.github_owner and repo.github_repo:
                if self.github is None or not self.github.access_token():
                    if not self.connect_github():
                        return
                assert self.github is not None
                for item in self.github.list_commits(repo.github_owner, repo.github_repo, 60):
                    sha = str(item.get("sha", ""))
                    commit_data = item.get("commit") if isinstance(item.get("commit"), dict) else {}
                    title = str(commit_data.get("message", "")).splitlines()[0]
                    commits.append((sha, title, str(item.get("html_url")) if item.get("html_url") else None))
            if not commits:
                QMessageBox.information(self, "Commit", "No commits found.")
                return
            labels = [f"{sha[:10]}  {title}" for sha, title, _url in commits]
            selected, ok = QInputDialog.getItem(self, "Link Commit", "Commit:", labels, 0, False)
            if not ok:
                return
            index = labels.index(selected)
            sha, title, url = commits[index]
            self.database.add_external_ref(self.current_note_id, repo.id, "commit", sha, title, url)
            self.refresh_context_panel()
        except (GitError, GitHubError, DatabaseError) as exc:
            QMessageBox.warning(self, "Commit", str(exc))

    def add_pull_request_reference(self) -> None:
        if self.current_note_id is None:
            return
        repo = self._current_repository()
        if repo is None or not repo.github_owner or not repo.github_repo:
            QMessageBox.information(self, "Pull Request", "This project must be linked to a GitHub repository first.")
            return
        if self.github is None or not self.github.access_token():
            if not self.connect_github():
                return
        assert self.github is not None
        try:
            pulls = self.github.list_pull_requests(repo.github_owner, repo.github_repo, "all", 60)
            if not pulls:
                QMessageBox.information(self, "Pull Request", "No pull requests found.")
                return
            labels = [f"#{item.get('number')}  {item.get('title', '')}" for item in pulls]
            selected, ok = QInputDialog.getItem(self, "Link Pull Request", "Pull request:", labels, 0, False)
            if not ok:
                return
            item = pulls[labels.index(selected)]
            number = str(item.get("number"))
            self.database.add_external_ref(
                self.current_note_id, repo.id, "pull_request", f"#{number}",
                str(item.get("title", "")), str(item.get("html_url")) if item.get("html_url") else None,
            )
            self.refresh_context_panel()
        except (GitHubError, DatabaseError) as exc:
            QMessageBox.warning(self, "Pull Request", str(exc))

    def remove_external_reference(self, ref_id: int) -> None:
        self.database.remove_external_ref(ref_id)
        self.refresh_context_panel()

    def open_linked_resource(self, relative_path: str) -> None:
        repo = self._current_repository()
        if repo is None:
            return
        if repo.local_path:
            path = Path(repo.local_path) / relative_path
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
                return
        if repo.github_full_name:
            branch = repo.default_branch or "HEAD"
            kind = "tree" if relative_path and not Path(relative_path).suffix else "blob"
            url = f"https://github.com/{repo.github_full_name}/{kind}/{branch}/{relative_path}"
            QDesktopServices.openUrl(QUrl(url))

    def open_preferences(self) -> None:
        dialog = PreferencesDialog(self.preferences, self)
        if dialog.exec():
            self.preferences = dialog.preferences()
            self.settings.save_preferences(self.preferences)
            self._apply_preferences(self.preferences, persist=False)

    def _apply_preferences(self, prefs: AppPreferences, persist: bool = False) -> None:
        self.editor.set_editor_font_size(prefs.editor_font_size)
        if hasattr(self, "font_size_slider"):
            self.font_size_slider.blockSignals(True)
            self.font_size_slider.setValue(prefs.editor_font_size)
            self.font_size_slider.blockSignals(False)
            self.font_size_label.setText(f"{prefs.editor_font_size} pt")
        self.editor.set_tab_width(prefs.tab_width)
        self.editor.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth if prefs.word_wrap else QTextEdit.LineWrapMode.NoWrap
        )
        auto_enabled = prefs.auto_checkbox_default
        self.auto_checkbox_action.blockSignals(True)
        self.auto_checkbox_action.setChecked(auto_enabled)
        self.auto_checkbox_action.blockSignals(False)
        self.editor.set_auto_checkbox(auto_enabled)
        self.blank_line_enter_action.blockSignals(True)
        self.blank_line_enter_action.setChecked(prefs.blank_line_after_enter)
        self.blank_line_enter_action.blockSignals(False)
        self.editor.set_blank_line_after_enter(prefs.blank_line_after_enter)
        self.set_theme(prefs.theme, persist=persist)

    def _set_auto_checkbox(self, enabled: bool) -> None:
        self.editor.set_auto_checkbox(enabled)
        self.preferences.auto_checkbox_default = enabled
        self.settings.set_value("editor/auto_checkbox_default", enabled)

    def _set_blank_line_after_enter(self, enabled: bool) -> None:
        self.editor.set_blank_line_after_enter(enabled)
        self.preferences.blank_line_after_enter = enabled
        self.settings.set_value("editor/blank_line_after_enter", enabled)

    def _set_numbered_list_mode(self, enabled: bool) -> None:
        self.editor.set_numbered_list_mode(enabled)
        self.editor.setFocus()

    def _sync_numbered_list_action(self, enabled: bool) -> None:
        self.numbered_action.blockSignals(True)
        self.numbered_action.setChecked(enabled)
        self.numbered_action.blockSignals(False)

    def set_theme(self, theme: str, persist: bool = True) -> None:
        self.theme_manager.apply(theme)
        resolved_theme = self.theme_manager.current_theme
        spec = self.theme_manager.current_spec
        self.diagram.set_theme(spec.diagram_palette())
        self.editor.set_search_theme(
            match_background=spec.find_match_bg,
            match_foreground=spec.find_match_fg,
            current_background=spec.find_current_bg,
            current_foreground=spec.find_current_fg,
            marker=spec.find_marker,
            current_marker=spec.find_current_marker,
        )
        self.preferences.theme = resolved_theme
        for name, action in getattr(self, "theme_actions", {}).items():
            action.setChecked(name == resolved_theme)
        if hasattr(self, "theme_combo"):
            index = self.theme_combo.findData(resolved_theme)
            if index >= 0 and index != self.theme_combo.currentIndex():
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(index)
                self.theme_combo.blockSignals(False)
        if persist:
            self.settings.set_value("appearance/theme", resolved_theme)
            self.settings.sync()

    def _theme_combo_changed(self, _index: int) -> None:
        theme = self.theme_combo.currentData()
        if theme:
            self.set_theme(str(theme))

    def _sync_workspace_buttons(self, index: int) -> None:
        if hasattr(self, "editor_workspace_button"):
            self.editor_workspace_button.setChecked(index == 0)
            self.diagram_workspace_button.setChecked(index == 1)
            self.context_workspace_button.setChecked(index == 2)
        if index == 2:
            self.refresh_context_panel()

    def _on_system_color_scheme_changed(self, _scheme) -> None:
        if self.preferences.theme == "system":
            self.set_theme("system", persist=False)

    def _toggle_sidebar(self) -> None:
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME} {VERSION}</b><br><br>"
            "Local-first engineering context for notes, decisions, diagrams and code links.<br><br>"
            "No DevNest account or cloud storage is required. GitHub connection is optional and read-only.<br><br>"
            f"Database: {database_path()}",
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(Path(url.toLocalFile()).suffix.lower() == ".txt" for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        accepted = False
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".txt":
                self._import_path(path)
                accepted = True
        if accepted:
            event.acceptProposedAction()
        else:
            event.ignore()

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        splitter_state = self.settings.value("window/splitter")
        if splitter_state is not None:
            self.splitter.restoreState(splitter_state)
        tab_index = self.settings.value("window/tab_index", 0)
        try:
            self.tabs.setCurrentIndex(int(tab_index))
        except (TypeError, ValueError):
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        self.flush_pending_saves()
        self.settings.set_value("window/geometry", self.saveGeometry())
        self.settings.set_value("window/splitter", self.splitter.saveState())
        self.settings.set_value("window/tab_index", self.tabs.currentIndex())
        self.settings.set_last_note_id(self.current_note_id)
        if self.current_project_id is not None:
            self.settings.set_value("session/last_project_id", self.current_project_id)
        self.settings.sync()
        self.database.close()
        event.accept()

    def _show_database_error(self, exc: DatabaseError) -> None:
        logger.exception("Database operation failed")
        QMessageBox.critical(self, "Database Error", str(exc))
````

## `app/models.py`

````python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Note:
    id: int
    title: str
    content_html: str
    content_plain: str
    created_at: str
    updated_at: str
    is_deleted: bool
    uuid: str = ""
    project_id: int | None = None
    note_kind: str = "note"


@dataclass(slots=True)
class NoteSummary:
    id: int
    title: str
    preview: str
    created_at: str
    updated_at: str
    is_deleted: bool
    project_id: int | None = None
    note_kind: str = "note"
    needs_review: bool = False


@dataclass(slots=True)
class Project:
    id: int
    uuid: str
    name: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class Repository:
    id: int
    project_id: int
    uuid: str
    provider: str
    local_path: str | None
    github_owner: str | None
    github_repo: str | None
    github_installation_id: int | None
    default_branch: str | None
    last_seen_sha: str | None
    last_scanned_at: str | None
    created_at: str
    updated_at: str

    @property
    def github_full_name(self) -> str | None:
        if self.github_owner and self.github_repo:
            return f"{self.github_owner}/{self.github_repo}"
        return None


@dataclass(slots=True)
class ResourceLink:
    id: int
    note_id: int
    repository_id: int
    resource_type: str
    resource_value: str
    display_label: str
    diagram_item_id: str | None
    baseline_sha: str | None
    last_checked_sha: str | None
    needs_review: bool
    change_count: int
    last_changed_at: str | None
    created_at: str
    updated_at: str


@dataclass(slots=True)
class ExternalRef:
    id: int
    note_id: int
    repository_id: int
    ref_type: str
    ref_value: str
    title: str
    url: str | None
    created_at: str
````

## `app/paths.py`

````python
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def app_data_dir() -> Path:
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return app_data_dir() / "devnest.db"


def log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative
````

## `app/services/__init__.py`

````python

````

## `app/services/github_client.py`

````python
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.secret_store import clear_github_credentials, load_github_credentials, save_github_credentials


API_VERSION = "2026-03-10"


class GitHubError(RuntimeError):
    pass


class GitHubAuthorizationPending(GitHubError):
    pass


class GitHubSlowDown(GitHubError):
    pass


@dataclass(slots=True)
class DeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class GitHubClient:
    def __init__(self, client_id: str, *, timeout: int = 20) -> None:
        self.client_id = client_id.strip()
        self.timeout = timeout

    @staticmethod
    def _expiry_iso(seconds: object) -> str | None:
        try: value = int(seconds)
        except (TypeError, ValueError): return None
        return (datetime.now(timezone.utc) + timedelta(seconds=max(0, value - 60))).isoformat(timespec="seconds")

    @staticmethod
    def _is_expired(value: object) -> bool:
        if not value: return False
        try: return datetime.fromisoformat(str(value)) <= datetime.now(timezone.utc)
        except ValueError: return True

    def _request(self, url: str, *, method: str = "GET", token: str | None = None,
                 data: dict[str, object] | None = None, form: bool = False) -> Any:
        body = None
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "DevNest-Desktop/2"}
        if url.startswith("https://github.com/login/"):
            headers["Accept"] = "application/json"
        if "api.github.com" in url:
            headers["X-GitHub-Api-Version"] = API_VERSION
        if token: headers["Authorization"] = f"Bearer {token}"
        if data is not None:
            if form:
                body = urllib.parse.urlencode({k: str(v) for k, v in data.items() if v is not None}).encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                body = json.dumps(data).encode("utf-8"); headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try: message = json.loads(raw.decode("utf-8")).get("message", exc.reason)
            except Exception: message = exc.reason
            raise GitHubError(f"GitHub HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Could not reach GitHub: {exc.reason}") from exc
        if not raw: return {}
        try: return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc: raise GitHubError("GitHub returned an invalid response.") from exc

    def start_device_flow(self) -> DeviceCode:
        if not self.client_id: raise GitHubError("GitHub App Client ID is not configured.")
        data = self._request("https://github.com/login/device/code", method="POST", data={"client_id": self.client_id}, form=True)
        return DeviceCode(str(data["device_code"]), str(data["user_code"]), str(data["verification_uri"]), int(data["expires_in"]), int(data.get("interval", 5)))

    def poll_device_flow(self, device_code: str) -> dict[str, object]:
        data = self._request("https://github.com/login/oauth/access_token", method="POST", data={
            "client_id": self.client_id, "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }, form=True)
        error = data.get("error") if isinstance(data, dict) else None
        if error == "authorization_pending": raise GitHubAuthorizationPending("Authorization pending")
        if error == "slow_down": raise GitHubSlowDown("GitHub requested slower polling")
        if error: raise GitHubError(str(data.get("error_description") or error))
        credentials = {
            "access_token": data.get("access_token"), "access_expires_at": self._expiry_iso(data.get("expires_in")),
            "refresh_token": data.get("refresh_token"), "refresh_expires_at": self._expiry_iso(data.get("refresh_token_expires_in")),
            "token_type": data.get("token_type", "bearer"), "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        save_github_credentials(credentials)
        return credentials

    def credentials(self) -> dict[str, object] | None:
        return load_github_credentials()

    def access_token(self) -> str | None:
        creds = load_github_credentials()
        if not creds or not creds.get("access_token"): return None
        if not self._is_expired(creds.get("access_expires_at")):
            return str(creds["access_token"])
        refresh = creds.get("refresh_token")
        if not refresh or self._is_expired(creds.get("refresh_expires_at")):
            clear_github_credentials(); return None
        data = self._request("https://github.com/login/oauth/access_token", method="POST", data={
            "client_id": self.client_id, "grant_type": "refresh_token", "refresh_token": refresh,
        }, form=True)
        if data.get("error"):
            clear_github_credentials(); raise GitHubError(str(data.get("error_description") or data["error"]))
        updated = {
            "access_token": data.get("access_token"), "access_expires_at": self._expiry_iso(data.get("expires_in")),
            "refresh_token": data.get("refresh_token", refresh), "refresh_expires_at": self._expiry_iso(data.get("refresh_token_expires_in")),
            "token_type": data.get("token_type", "bearer"), "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        save_github_credentials(updated)
        return str(updated["access_token"])

    def disconnect(self) -> None:
        clear_github_credentials()

    def authenticated_user(self) -> dict[str, object]:
        token = self.access_token()
        if not token: raise GitHubError("GitHub is not connected.")
        return self._request("https://api.github.com/user", token=token)

    def list_repositories(self, limit: int = 200) -> list[dict[str, object]]:
        """Return repositories from installations of this GitHub App only.

        A GitHub App user token is intentionally narrower than a general OAuth
        token. Enumerating installations first mirrors GitHub's permission model
        and means the picker only shows repositories on which DevNest is actually
        installed.
        """
        token = self.access_token()
        if not token: raise GitHubError("GitHub is not connected.")
        installations_data = self._request("https://api.github.com/user/installations?per_page=100", token=token)
        installations = installations_data.get("installations", []) if isinstance(installations_data, dict) else []
        result: list[dict[str, object]] = []
        seen: set[int] = set()
        for installation in installations:
            if not isinstance(installation, dict) or not installation.get("id"):
                continue
            installation_id = int(installation["id"])
            page = 1
            while len(result) < limit:
                data = self._request(
                    f"https://api.github.com/user/installations/{installation_id}/repositories?per_page=100&page={page}",
                    token=token,
                )
                repos = data.get("repositories", []) if isinstance(data, dict) else []
                if not isinstance(repos, list): break
                for repo in repos:
                    if not isinstance(repo, dict): continue
                    repo_id = int(repo.get("id", 0) or 0)
                    if repo_id and repo_id in seen: continue
                    if repo_id: seen.add(repo_id)
                    copy = dict(repo); copy["_devnest_installation_id"] = installation_id
                    result.append(copy)
                    if len(result) >= limit: break
                if len(repos) < 100 or len(result) >= limit: break
                page += 1
        result.sort(key=lambda item: str(item.get("full_name", "")).casefold())
        return result[:limit]

    def repository(self, owner: str, repo: str) -> dict[str, object]:
        return self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}", token=self.access_token())

    def branch_head(self, owner: str, repo: str, branch: str | None = None) -> tuple[str, str]:
        info = self.repository(owner, repo)
        branch_name = branch or str(info.get("default_branch") or "main")
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/commits/{urllib.parse.quote(branch_name, safe='')}", token=self.access_token())
        return str(data["sha"]), branch_name

    def compare_commits(self, owner: str, repo: str, base: str, head: str) -> tuple[list[str], int]:
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/compare/{urllib.parse.quote(base, safe='')}...{urllib.parse.quote(head, safe='')}", token=self.access_token())
        files = [str(item.get("filename")) for item in data.get("files", []) if isinstance(item, dict) and item.get("filename")]
        return files, int(data.get("total_commits", len(data.get("commits", []))))


    def list_commits(self, owner: str, repo: str, limit: int = 50) -> list[dict[str, object]]:
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/commits?per_page={max(1,min(limit,100))}", token=self.access_token())
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []

    def list_pull_requests(self, owner: str, repo: str, state: str = "all", limit: int = 50) -> list[dict[str, object]]:
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/pulls?state={state}&per_page={max(1,min(limit,100))}&sort=updated&direction=desc", token=self.access_token())
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
````

## `app/services/local_git.py`

````python
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    pass


@dataclass(slots=True)
class GitRepositoryInfo:
    root: Path
    head_sha: str
    branch: str | None
    remote_url: str | None
    github_owner: str | None
    github_repo: str | None


def _run_git(path: Path | str, *args: str) -> str:
    working = Path(path)
    try:
        completed = subprocess.run(
            ["git", "-C", str(working), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError as exc:
        raise GitError("Git was not found. Install Git for Windows and restart DevNest.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitError("Git command timed out.") from exc
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "Unknown git error"
        raise GitError(message)
    return completed.stdout.strip()


def parse_github_remote(url: str | None) -> tuple[str | None, str | None]:
    if not url:
        return None, None
    value = url.strip()
    patterns = [
        r"^(?:https?://|git://)github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
        r"^git@github\.com:([^/]+)/(.+?)(?:\.git)?$",
        r"^ssh://git@github\.com/([^/]+)/(.+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
    return None, None


def inspect_repository(path: Path | str) -> GitRepositoryInfo:
    path = Path(path).expanduser().resolve()
    root_text = _run_git(path, "rev-parse", "--show-toplevel")
    root = Path(root_text).resolve()
    head = _run_git(root, "rev-parse", "HEAD")
    branch = _run_git(root, "branch", "--show-current") or None
    try:
        remote = _run_git(root, "remote", "get-url", "origin") or None
    except GitError:
        remote = None
    owner, repo = parse_github_remote(remote)
    return GitRepositoryInfo(root, head, branch, remote, owner, repo)


def current_head(path: Path | str) -> str:
    return _run_git(path, "rev-parse", "HEAD")


def default_branch(path: Path | str) -> str | None:
    try:
        symbolic = _run_git(path, "symbolic-ref", "refs/remotes/origin/HEAD")
        return symbolic.rsplit("/", 1)[-1] if symbolic else None
    except GitError:
        try:
            return _run_git(path, "branch", "--show-current") or None
        except GitError:
            return None


def changed_files(path: Path | str, base_sha: str, head_sha: str) -> list[str]:
    if base_sha == head_sha:
        return []
    output = _run_git(path, "diff", "--name-only", "--no-renames", f"{base_sha}..{head_sha}")
    return [line.replace("\\", "/").strip("/") for line in output.splitlines() if line.strip()]


def commit_count(path: Path | str, base_sha: str, head_sha: str) -> int:
    if base_sha == head_sha:
        return 0
    value = _run_git(path, "rev-list", "--count", f"{base_sha}..{head_sha}")
    try:
        return int(value)
    except ValueError:
        return 0


def recent_commits(path: Path | str, limit: int = 50) -> list[dict[str, str]]:
    fmt = "%H%x1f%h%x1f%s%x1f%an%x1f%aI%x1e"
    output = _run_git(path, "log", f"--max-count={max(1, min(limit, 200))}", f"--pretty=format:{fmt}")
    result: list[dict[str, str]] = []
    for record in output.split("\x1e"):
        parts = record.strip().split("\x1f")
        if len(parts) == 5:
            result.append({"sha": parts[0], "short_sha": parts[1], "title": parts[2], "author": parts[3], "date": parts[4]})
    return result
````

## `app/services/logging_setup.py`

````python
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.paths import log_dir


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        log_dir() / "devnest.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root.addHandler(handler)
````

## `app/services/repository_scanner.py`

````python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.database import Database, utc_now_iso
from app.models import Repository, ResourceLink
from app.services.github_client import GitHubClient, GitHubError
from app.services.local_git import GitError, changed_files as local_changed_files, commit_count as local_commit_count, current_head


@dataclass(slots=True)
class ScanResult:
    repository_id: int
    head_sha: str | None
    changed_links: int
    checked_links: int
    changed_files: int
    commit_count: int
    source: str
    error: str | None = None


def _normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def resource_is_affected(link: ResourceLink, files: list[str]) -> bool:
    if not files: return False
    if link.resource_type == "repository": return True
    value = _normalize(link.resource_value)
    normalized = [_normalize(item) for item in files]
    if link.resource_type == "directory" and not value:
        return True
    if link.resource_type == "file": return value in normalized
    prefix = value.rstrip("/") + "/"
    return any(item == value or item.startswith(prefix) for item in normalized)


class RepositoryScanner:
    def __init__(self, database: Database, github: GitHubClient | None = None) -> None:
        self.database = database
        self.github = github

    def _head(self, repo: Repository) -> tuple[str, str]:
        if repo.local_path and Path(repo.local_path).exists():
            return current_head(repo.local_path), "local"
        if repo.github_owner and repo.github_repo and self.github:
            sha, branch = self.github.branch_head(repo.github_owner, repo.github_repo, repo.default_branch)
            if branch != repo.default_branch: self.database.update_repository(repo.id, default_branch=branch)
            return sha, "github"
        raise GitError("Repository has neither an available local checkout nor a usable GitHub connection.")

    def _compare(self, repo: Repository, base: str, head: str, source: str) -> tuple[list[str], int]:
        if base == head: return [], 0
        if source == "local" and repo.local_path:
            return local_changed_files(repo.local_path, base, head), local_commit_count(repo.local_path, base, head)
        if repo.github_owner and repo.github_repo and self.github:
            return self.github.compare_commits(repo.github_owner, repo.github_repo, base, head)
        raise GitError("Cannot compare repository revisions.")

    def scan_repository(self, repository_id: int) -> ScanResult:
        repo = self.database.get_repository(repository_id)
        if repo is None: return ScanResult(repository_id, None, 0, 0, 0, 0, "none", "Repository not found")
        try:
            head, source = self._head(repo)
            if repo.last_seen_sha == head:
                checked = int(self.database.connection.execute(
                    "SELECT COUNT(*) FROM resource_links WHERE repository_id=?", (repo.id,)
                ).fetchone()[0])
                self.database.update_repository(repo.id, last_scanned_at=utc_now_iso())
                return ScanResult(repo.id, head, 0, checked, 0, 0, source)
            links = self.database.connection.execute("SELECT DISTINCT note_id FROM resource_links WHERE repository_id=?", (repo.id,)).fetchall()
            all_resource_links: list[ResourceLink] = []
            for row in links: all_resource_links.extend(self.database.list_resource_links(int(row["note_id"])))
            all_resource_links = [link for link in all_resource_links if link.repository_id == repo.id]
            comparison_cache: dict[str, tuple[list[str], int]] = {}
            changed_links = 0; max_files: set[str] = set(); max_commits = 0
            for link in all_resource_links:
                base = link.baseline_sha
                if not base:
                    self.database.mark_note_reviewed(link.note_id, repo.id, head)
                    continue
                if base not in comparison_cache:
                    comparison_cache[base] = self._compare(repo, base, head, source)
                files, commits = comparison_cache[base]
                max_files.update(files); max_commits = max(max_commits, commits)
                if resource_is_affected(link, files):
                    self.database.mark_link_changed(link.id, head, commits)
                    changed_links += 1
                else:
                    self.database.mark_link_checked(link.id, head)
            previous = repo.last_seen_sha
            if previous != head and max_files:
                self.database.record_repository_change(repo.id, previous, head, sorted(max_files), max_commits)
            self.database.update_repository(repo.id, last_seen_sha=head, last_scanned_at=utc_now_iso())
            return ScanResult(repo.id, head, changed_links, len(all_resource_links), len(max_files), max_commits, source)
        except (GitError, GitHubError) as exc:
            return ScanResult(repo.id, None, 0, 0, 0, 0, "error", str(exc))

    def scan_project(self, project_id: int) -> list[ScanResult]:
        return [self.scan_repository(repo.id) for repo in self.database.list_repositories(project_id)]
````

## `app/services/secret_store.py`

````python
from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path


class SecretStoreError(RuntimeError):
    pass


_TARGET = "DevNest:GitHub"
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168


if os.name == "nt":
    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR), ("LastWritten", FILETIME), ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
        ]

    _advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    _CredWriteW = _advapi32.CredWriteW
    _CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    _CredWriteW.restype = wintypes.BOOL
    _CredReadW = _advapi32.CredReadW
    _CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
    _CredReadW.restype = wintypes.BOOL
    _CredDeleteW = _advapi32.CredDeleteW
    _CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    _CredDeleteW.restype = wintypes.BOOL
    _CredFree = _advapi32.CredFree
    _CredFree.argtypes = [ctypes.c_void_p]


def _fallback_file() -> Path:
    # Development-only fallback for non-Windows platforms. Production Windows
    # builds use Credential Manager and never write tokens here.
    return Path.home() / ".devnest_github_credentials.json"


def save_github_credentials(data: dict[str, object]) -> None:
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    if os.name != "nt":
        path = _fallback_file(); path.write_bytes(payload)
        try: path.chmod(0o600)
        except OSError: pass
        return
    blob = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
    credential = CREDENTIALW()
    credential.Type = _CRED_TYPE_GENERIC
    credential.TargetName = _TARGET
    credential.CredentialBlobSize = len(payload)
    credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
    credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
    credential.UserName = "github"
    if not _CredWriteW(ctypes.byref(credential), 0):
        raise SecretStoreError(f"Windows Credential Manager error: {ctypes.get_last_error()}")


def load_github_credentials() -> dict[str, object] | None:
    if os.name != "nt":
        path = _fallback_file()
        if not path.exists(): return None
        try: return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return None
    pointer = ctypes.POINTER(CREDENTIALW)()
    if not _CredReadW(_TARGET, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        error = ctypes.get_last_error()
        if error == _ERROR_NOT_FOUND: return None
        raise SecretStoreError(f"Windows Credential Manager error: {error}")
    try:
        credential = pointer.contents
        raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        decoded = json.loads(raw.decode("utf-8"))
        return decoded if isinstance(decoded, dict) else None
    finally:
        _CredFree(pointer)


def clear_github_credentials() -> None:
    if os.name != "nt":
        try: _fallback_file().unlink()
        except FileNotFoundError: pass
        return
    if not _CredDeleteW(_TARGET, _CRED_TYPE_GENERIC, 0):
        error = ctypes.get_last_error()
        if error != _ERROR_NOT_FOUND:
            raise SecretStoreError(f"Windows Credential Manager error: {error}")
````

## `app/services/txt_codec.py`

````python
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

TASK_RE = re.compile(
    r"^(?P<indent>[\t ]*)(?P<marker>\[\s\]|\[[xX]\]|☐|☑|✓)(?:[\t ]*)(?P<text>.*)$"
)
INTERNAL_TASK_RE = re.compile(r"^(?P<indent>[\t ]*)(?P<marker>☐|☑)(?:[\t ]?)(?P<text>.*)$")


@dataclass(frozen=True, slots=True)
class ParsedLine:
    text: str
    is_task: bool
    checked: bool = False
    indent: str = ""


def parse_line(line: str) -> ParsedLine:
    match = TASK_RE.match(line)
    if not match:
        return ParsedLine(text=line, is_task=False)
    marker = match.group("marker")
    return ParsedLine(
        text=match.group("text"),
        is_task=True,
        checked=marker.lower() == "[x]" or marker in {"☑", "✓"},
        indent=match.group("indent"),
    )


def parse_text(text: str) -> list[ParsedLine]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [parse_line(line) for line in normalized.split("\n")]


def _indent_html(indent: str) -> str:
    return html.escape(indent.expandtabs(4))


def parsed_to_html(lines: list[ParsedLine]) -> str:
    blocks: list[str] = ["<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head><body>"]
    for line in lines:
        if line.is_task:
            marker = "☑" if line.checked else "☐"
            task_text = html.escape(line.text)
            if line.checked:
                task_text = f'<span style="text-decoration: line-through;">{task_text}</span>'
            blocks.append(
                f'<p style="margin:0; white-space:pre-wrap;">{_indent_html(line.indent)}{marker} {task_text}</p>'
            )
        else:
            escaped = html.escape(line.text).replace("\t", "    ")
            blocks.append(f'<p style="margin:0; white-space:pre-wrap;">{escaped if escaped else "<br>"}</p>')
    blocks.append("</body></html>")
    return "".join(blocks)



def parsed_to_internal_text(lines: list[ParsedLine]) -> str:
    output: list[str] = []
    for line in lines:
        if line.is_task:
            marker = "☑" if line.checked else "☐"
            suffix = f" {line.text}" if line.text else ""
            output.append(f"{line.indent.expandtabs(4)}{marker}{suffix}")
        else:
            output.append(line.text)
    return "\n".join(output)


def import_text_to_html(text: str) -> str:
    return parsed_to_html(parse_text(text))


def export_internal_plain_text(text: str) -> str:
    output: list[str] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for line in normalized.split("\n"):
        match = INTERNAL_TASK_RE.match(line)
        if not match:
            output.append(line)
            continue
        prefix = "[x]" if match.group("marker") == "☑" else "[ ]"
        text_part = match.group("text")
        output.append(f"{match.group('indent')}{prefix}{(' ' + text_part) if text_part else ''}")
    return "\n".join(output)


def read_utf8_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UnicodeError("The file is not valid UTF-8/UTF-8-SIG text.") from exc


def write_utf8_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")
````

## `app/settings.py`

````python
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

from app.constants import DEFAULT_AUTOSAVE_DELAY_MS


@dataclass(slots=True)
class AppPreferences:
    theme: str = "system"
    autosave_enabled: bool = True
    autosave_delay_ms: int = DEFAULT_AUTOSAVE_DELAY_MS
    start_with_last_note: bool = True
    editor_font_size: int = 12
    tab_width: int = 4
    auto_checkbox_default: bool = True
    blank_line_after_enter: bool = False
    word_wrap: bool = True


class SettingsManager:
    def __init__(self, settings: QSettings | None = None) -> None:
        self.qsettings = settings or QSettings()

    def preferences(self) -> AppPreferences:
        return AppPreferences(
            theme=str(self.qsettings.value("appearance/theme", "system")),
            autosave_enabled=self._bool("general/autosave_enabled", True),
            autosave_delay_ms=int(self.qsettings.value("general/autosave_delay_ms", DEFAULT_AUTOSAVE_DELAY_MS)),
            start_with_last_note=self._bool("general/start_with_last_note", True),
            editor_font_size=int(self.qsettings.value("editor/font_size", 12)),
            tab_width=int(self.qsettings.value("editor/tab_width", 4)),
            auto_checkbox_default=self._bool("editor/auto_checkbox_default", True),
            blank_line_after_enter=self._bool("editor/blank_line_after_enter", False),
            word_wrap=self._bool("editor/word_wrap", True),
        )

    def save_preferences(self, prefs: AppPreferences) -> None:
        self.qsettings.setValue("appearance/theme", prefs.theme)
        self.qsettings.setValue("general/autosave_enabled", prefs.autosave_enabled)
        self.qsettings.setValue("general/autosave_delay_ms", prefs.autosave_delay_ms)
        self.qsettings.setValue("general/start_with_last_note", prefs.start_with_last_note)
        self.qsettings.setValue("editor/font_size", prefs.editor_font_size)
        self.qsettings.setValue("editor/tab_width", prefs.tab_width)
        self.qsettings.setValue("editor/auto_checkbox_default", prefs.auto_checkbox_default)
        self.qsettings.setValue("editor/blank_line_after_enter", prefs.blank_line_after_enter)
        self.qsettings.setValue("editor/word_wrap", prefs.word_wrap)
        self.qsettings.sync()

    def last_note_id(self) -> int | None:
        value = self.qsettings.value("session/last_note_id", None)
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def set_last_note_id(self, note_id: int | None) -> None:
        if note_id is None:
            self.qsettings.remove("session/last_note_id")
        else:
            self.qsettings.setValue("session/last_note_id", note_id)

    def value(self, key: str, default: object = None) -> object:
        return self.qsettings.value(key, default)

    def set_value(self, key: str, value: object) -> None:
        self.qsettings.setValue(key, value)

    def sync(self) -> None:
        self.qsettings.sync()

    def _bool(self, key: str, default: bool) -> bool:
        value = self.qsettings.value(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
````

## `app/themes/__init__.py`

````python

````

## `app/themes/theme_manager.py`

````python
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True, slots=True)
class ThemeSpec:
    key: str
    label: str
    dark: bool
    window: str
    surface: str
    surface_alt: str
    editor: str
    text: str
    muted: str
    border: str
    hover: str
    selected: str
    accent: str
    find_match_bg: str
    find_match_fg: str
    find_current_bg: str
    find_current_fg: str
    find_marker: str
    find_current_marker: str
    diagram_bg: str
    diagram_grid_minor: str
    diagram_grid_major: str
    diagram_stroke: str
    diagram_fill: str
    diagram_text: str

    def diagram_palette(self) -> dict[str, str]:
        return {
            "background": self.diagram_bg,
            "grid_minor": self.diagram_grid_minor,
            "grid_major": self.diagram_grid_major,
            "stroke": self.diagram_stroke,
            "fill": self.diagram_fill,
            "text": self.diagram_text,
            "connector": self.diagram_stroke,
        }


THEME_SPECS: dict[str, ThemeSpec] = {
    "dark_matte": ThemeSpec(
        key="dark_matte",
        label="Matte Black",
        dark=True,
        window="#121212",
        surface="#171717",
        surface_alt="#1d1d1d",
        editor="#151515",
        text="#e7e7e7",
        muted="#a7a7a7",
        border="#303030",
        hover="#252525",
        selected="#303030",
        accent="#8b9bb4",
        find_match_bg="#59491f",
        find_match_fg="#f4ead2",
        find_current_bg="#b67d20",
        find_current_fg="#111111",
        find_marker="#c89b3c",
        find_current_marker="#f2c45d",
        diagram_bg="#151515",
        diagram_grid_minor="#1d1d1d",
        diagram_grid_major="#292929",
        diagram_stroke="#c4c7cc",
        diagram_fill="#1b1b1b",
        diagram_text="#f0f0f0",
    ),
    "dark_slate": ThemeSpec(
        key="dark_slate",
        label="Midnight Slate",
        dark=True,
        window="#151922",
        surface="#1b202b",
        surface_alt="#222938",
        editor="#181d27",
        text="#e7ecf3",
        muted="#9aa6b6",
        border="#313b4c",
        hover="#283142",
        selected="#33415a",
        accent="#5f86c9",
        find_match_bg="#294a62",
        find_match_fg="#edf6ff",
        find_current_bg="#4d86b5",
        find_current_fg="#ffffff",
        find_marker="#5e93bd",
        find_current_marker="#91c8f0",
        diagram_bg="#171c26",
        diagram_grid_minor="#202735",
        diagram_grid_major="#2d384b",
        diagram_stroke="#c1cad8",
        diagram_fill="#202735",
        diagram_text="#eef3f8",
    ),
    "dark_graphite": ThemeSpec(
        key="dark_graphite",
        label="Graphite",
        dark=True,
        window="#202124",
        surface="#25262a",
        surface_alt="#2b2d31",
        editor="#232428",
        text="#e8eaed",
        muted="#a9adb5",
        border="#3a3d43",
        hover="#32343a",
        selected="#3d424b",
        accent="#929aa8",
        find_match_bg="#51492d",
        find_match_fg="#f1ead2",
        find_current_bg="#8c7836",
        find_current_fg="#ffffff",
        find_marker="#a68c3e",
        find_current_marker="#d6b95d",
        diagram_bg="#222327",
        diagram_grid_minor="#292b30",
        diagram_grid_major="#383b42",
        diagram_stroke="#d0d3d8",
        diagram_fill="#292b30",
        diagram_text="#f1f3f4",
    ),
    "light_clean": ThemeSpec(
        key="light_clean",
        label="Clean Light",
        dark=False,
        window="#f7f7f8",
        surface="#ffffff",
        surface_alt="#f0f1f4",
        editor="#ffffff",
        text="#202124",
        muted="#69707c",
        border="#d7d9df",
        hover="#eceef2",
        selected="#dfe7ff",
        accent="#60769f",
        find_match_bg="#fff1a8",
        find_match_fg="#2c2a20",
        find_current_bg="#f4c34d",
        find_current_fg="#1f1b10",
        find_marker="#d9a72d",
        find_current_marker="#b47a00",
        diagram_bg="#f7f8fa",
        diagram_grid_minor="#edf0f3",
        diagram_grid_major="#dde1e6",
        diagram_stroke="#596273",
        diagram_fill="#ffffff",
        diagram_text="#202124",
    ),
    "light_soft": ThemeSpec(
        key="light_soft",
        label="Soft Gray",
        dark=False,
        window="#eceff1",
        surface="#f7f8f9",
        surface_alt="#e6e9ec",
        editor="#f9fafb",
        text="#25282c",
        muted="#687078",
        border="#cfd4d8",
        hover="#e1e5e8",
        selected="#d7e2eb",
        accent="#687f91",
        find_match_bg="#dceaf3",
        find_match_fg="#26333d",
        find_current_bg="#92c4df",
        find_current_fg="#182630",
        find_marker="#72a8c4",
        find_current_marker="#3e86aa",
        diagram_bg="#f1f3f4",
        diagram_grid_minor="#e5e8ea",
        diagram_grid_major="#d3d8dc",
        diagram_stroke="#5f6972",
        diagram_fill="#fbfcfc",
        diagram_text="#25282c",
    ),
    "light_warm": ThemeSpec(
        key="light_warm",
        label="Warm Paper",
        dark=False,
        window="#f3efe7",
        surface="#fbf8f1",
        surface_alt="#eee8dc",
        editor="#fffdf8",
        text="#332f2a",
        muted="#766e64",
        border="#d8d0c2",
        hover="#eee7db",
        selected="#e6dccb",
        accent="#8a7255",
        find_match_bg="#f1dfb5",
        find_match_fg="#3b3020",
        find_current_bg="#d7ac61",
        find_current_fg="#2a1e10",
        find_marker="#b78b48",
        find_current_marker="#8e6227",
        diagram_bg="#faf6ee",
        diagram_grid_minor="#eee8dc",
        diagram_grid_major="#ddd3c4",
        diagram_stroke="#6f655a",
        diagram_fill="#fffdf8",
        diagram_text="#332f2a",
    ),
    "light_cool": ThemeSpec(
        key="light_cool",
        label="Cool Mist",
        dark=False,
        window="#edf4f7",
        surface="#f8fbfc",
        surface_alt="#e4eef2",
        editor="#fbfdfe",
        text="#24313a",
        muted="#647681",
        border="#cad9df",
        hover="#e1edf2",
        selected="#d3e6ef",
        accent="#5e8194",
        find_match_bg="#d1e9f0",
        find_match_fg="#24343c",
        find_current_bg="#8bc2d2",
        find_current_fg="#16303b",
        find_marker="#6aa9bc",
        find_current_marker="#3f8499",
        diagram_bg="#f3f8fa",
        diagram_grid_minor="#e5eff3",
        diagram_grid_major="#cfdee5",
        diagram_stroke="#58707c",
        diagram_fill="#fbfdfe",
        diagram_text="#24313a",
    ),
}

THEME_OPTIONS: tuple[tuple[str, str], ...] = (
    ("System", "system"),
    ("Matte Black", "dark_matte"),
    ("Midnight Slate", "dark_slate"),
    ("Graphite", "dark_graphite"),
    ("Clean Light", "light_clean"),
    ("Soft Gray", "light_soft"),
    ("Warm Paper", "light_warm"),
    ("Cool Mist", "light_cool"),
)


def _qss(spec: ThemeSpec) -> str:
    return f"""
QWidget {{ color: {spec.text}; }}
QMainWindow, QDialog {{ background: {spec.window}; }}
QMenuBar {{ background: {spec.surface}; color: {spec.text}; }}
QMenuBar::item {{ background: transparent; padding: 5px 8px; }}
QMenuBar::item:selected {{ background: {spec.hover}; }}
QToolBar {{ background: {spec.surface}; border-bottom: 1px solid {spec.border}; spacing: 4px; padding: 4px; }}
QToolButton {{ border: 0; border-radius: 5px; padding: 5px 7px; background: transparent; color: {spec.text}; }}
QToolButton:hover {{ background: {spec.hover}; }}
QToolButton:checked {{ background: {spec.selected}; }}
QToolBar QToolButton#qt_toolbar_ext_button {{ width: 0px; height: 0px; padding: 0; margin: 0; border: 0; }}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QListWidget, QTreeWidget, QTableWidget {{
    background: {spec.editor}; color: {spec.text}; border: 1px solid {spec.border}; border-radius: 6px; padding: 5px;
    selection-background-color: {spec.selected}; selection-color: {spec.text};
}}
QComboBox QAbstractItemView {{ background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border}; selection-background-color: {spec.selected}; }}
QListWidget, QTreeWidget {{ background: {spec.surface}; }}
QListWidget::item {{ border-radius: 6px; padding: 3px; margin: 2px 0; }}
QListWidget::item:selected {{ background: {spec.selected}; color: {spec.text}; }}
QPushButton {{ background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border}; border-radius: 6px; padding: 6px 10px; }}
QPushButton:hover {{ background: {spec.hover}; }}
QPushButton:pressed, QPushButton:checked {{ background: {spec.selected}; }}
QMenu {{ background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border}; padding: 4px; }}
QMenu::item {{ padding: 6px 28px 6px 10px; border-radius: 4px; }}
QMenu::item:selected {{ background: {spec.selected}; }}
QStatusBar {{ background: {spec.surface}; border-top: 1px solid {spec.border}; }}
QTabWidget::pane {{ border: 1px solid {spec.border}; background: {spec.editor}; }}
QTabBar::tab {{ background: {spec.surface_alt}; color: {spec.muted}; padding: 7px 14px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: {spec.editor}; color: {spec.text}; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {spec.border}; min-height: 24px; border-radius: 6px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QSplitter::handle {{ background: {spec.border}; width: 1px; }}
QToolTip {{ background: {spec.surface_alt}; color: {spec.text}; border: 1px solid {spec.border}; padding: 4px; }}
QSlider::groove:horizontal {{ height: 4px; background: {spec.border}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 14px; margin: -5px 0; background: {spec.text}; border: 1px solid {spec.muted}; border-radius: 7px; }}
QSlider::sub-page:horizontal {{ background: {spec.accent}; border-radius: 2px; }}
QLabel#diagramHint {{ color: {spec.muted}; }}
QWidget#workspaceBar {{ background: {spec.surface}; border-bottom: 1px solid {spec.border}; }}
QPushButton#workspaceButton {{ min-width: 78px; padding: 6px 12px; border: 0; border-radius: 5px; }}
QPushButton#workspaceButton:checked {{ background: {spec.selected}; }}
QComboBox#themePresetCombo {{ min-width: 142px; background: {spec.surface_alt}; }}
QWidget#editorFindBar {{
    background: {spec.surface};
    border: 1px solid {spec.border};
    border-radius: 8px;
}}
QLineEdit#editorFindInput {{
    background: {spec.editor};
    color: {spec.text};
    border: 1px solid {spec.border};
    border-radius: 5px;
    padding: 5px 7px;
}}
QLabel#editorFindCount {{ color: {spec.muted}; }}
QCheckBox#editorFindDirection {{ spacing: 4px; color: {spec.text}; }}
QCheckBox#editorFindDirection::indicator {{
    width: 12px; height: 12px;
    border: 1px solid {spec.muted};
    border-radius: 2px;
    background: {spec.editor};
}}
QCheckBox#editorFindDirection::indicator:checked {{
    background: {spec.accent};
    border-color: {spec.accent};
}}
QPushButton#editorFindButton {{ padding: 5px 9px; background: {spec.surface_alt}; }}
QPushButton#editorFindClose {{
    padding: 3px;
    border: 0;
    background: transparent;
    font-size: 17px;
    font-weight: 600;
}}
QPushButton#editorFindClose:hover {{ background: {spec.hover}; }}
"""


class ThemeManager:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.current_theme = "system"
        self.current_spec = THEME_SPECS["light_clean"]
        self.is_dark = False

    def apply(self, theme: str) -> bool:
        normalized = theme.lower().strip()
        valid = {value for _, value in THEME_OPTIONS}
        if normalized not in valid:
            # Backward compatibility with DevNest 1.0/1.1 settings.
            if normalized == "dark":
                normalized = "dark_slate"
            elif normalized == "light":
                normalized = "light_clean"
            else:
                normalized = "system"
        self.current_theme = normalized
        resolved = self._resolve_system_theme() if normalized == "system" else normalized
        self.current_spec = THEME_SPECS[resolved]
        self.is_dark = self.current_spec.dark
        self.app.setStyleSheet(_qss(self.current_spec))
        return self.is_dark

    def _resolve_system_theme(self) -> str:
        return "dark_matte" if self._system_is_dark() else "light_clean"

    def _system_is_dark(self) -> bool:
        hints = self.app.styleHints()
        color_scheme = getattr(hints, "colorScheme", None)
        if callable(color_scheme):
            try:
                scheme = color_scheme()
                dark = getattr(Qt.ColorScheme, "Dark", None)
                light = getattr(Qt.ColorScheme, "Light", None)
                if dark is not None and scheme == dark:
                    return True
                if light is not None and scheme == light:
                    return False
            except Exception:
                pass
        palette: QPalette = self.app.palette()
        return palette.color(QPalette.ColorRole.Window).lightness() < 128
````

## `app/utils/__init__.py`

````python

````

## `app/widgets/__init__.py`

````python

````

## `app/widgets/context_panel.py`

````python
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from app.models import ExternalRef, Repository, ResourceLink


class ContextPanel(QWidget):
    documentKindChanged = Signal(str)
    scanRequested = Signal()
    markReviewedRequested = Signal()
    addRepositoryLinkRequested = Signal()
    addDirectoryLinkRequested = Signal()
    addFileLinkRequested = Signal()
    removeResourceRequested = Signal(int)
    addCommitRequested = Signal()
    addPullRequestRequested = Signal()
    removeExternalRequested = Signal(int)
    openResourceRequested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self); root.setContentsMargins(14, 12, 14, 12); root.setSpacing(10)
        header = QHBoxLayout(); title = QLabel("Engineering Context"); title.setStyleSheet("font-size: 17px; font-weight: 700;")
        self.kind = QComboBox(); self.kind.addItem("Note", "note"); self.kind.addItem("Decision", "decision")
        self.kind.currentIndexChanged.connect(lambda _i: self.documentKindChanged.emit(str(self.kind.currentData())))
        header.addWidget(title); header.addStretch(1); header.addWidget(QLabel("Type:")); header.addWidget(self.kind); root.addLayout(header)

        self.repo_label = QLabel("No repository attached to this project."); self.repo_label.setWordWrap(True); root.addWidget(self.repo_label)
        status_row = QHBoxLayout(); self.status = QLabel("No linked code"); self.status.setStyleSheet("font-weight: 700;")
        scan = QPushButton("Scan now"); scan.clicked.connect(self.scanRequested)
        self.review = QPushButton("✓ Mark as Reviewed"); self.review.clicked.connect(self.markReviewedRequested)
        status_row.addWidget(self.status); status_row.addStretch(1); status_row.addWidget(scan); status_row.addWidget(self.review); root.addLayout(status_row)

        root.addWidget(self._section("Code links"))
        link_buttons = QHBoxLayout()
        for text, signal in (("+ Repository", self.addRepositoryLinkRequested), ("+ Folder", self.addDirectoryLinkRequested), ("+ File", self.addFileLinkRequested)):
            button = QPushButton(text); button.clicked.connect(signal); link_buttons.addWidget(button)
        link_buttons.addStretch(1); root.addLayout(link_buttons)
        self.resources = QTreeWidget(); self.resources.setHeaderLabels(["Target", "Scope", "Baseline", "Status"]); self.resources.setRootIsDecorated(False)
        self.resources.itemDoubleClicked.connect(self._resource_double_clicked); root.addWidget(self.resources, 1)
        remove_resource = QPushButton("Remove selected code link"); remove_resource.clicked.connect(self._remove_resource); root.addWidget(remove_resource)

        root.addWidget(self._section("Implementation references"))
        refs_row = QHBoxLayout(); commit = QPushButton("+ Commit"); commit.clicked.connect(self.addCommitRequested)
        pr = QPushButton("+ Pull Request"); pr.clicked.connect(self.addPullRequestRequested); refs_row.addWidget(commit); refs_row.addWidget(pr); refs_row.addStretch(1); root.addLayout(refs_row)
        self.refs = QListWidget(); self.refs.setMaximumHeight(160); root.addWidget(self.refs)
        remove_ref = QPushButton("Remove selected reference"); remove_ref.clicked.connect(self._remove_external); root.addWidget(remove_ref)

        self.hint = QLabel("Tip: select a diagram node before adding a code link to attach the path to that specific architecture node.")
        self.hint.setWordWrap(True); self.hint.setStyleSheet("font-size: 11px;"); root.addWidget(self.hint)

    @staticmethod
    def _section(text: str) -> QLabel:
        label = QLabel(text); label.setStyleSheet("font-size: 13px; font-weight: 700; margin-top: 5px;"); return label

    def set_kind(self, kind: str) -> None:
        idx = self.kind.findData(kind); self.kind.blockSignals(True); self.kind.setCurrentIndex(max(0, idx)); self.kind.blockSignals(False)

    def set_repository(self, repo: Repository | None) -> None:
        if repo is None:
            self.repo_label.setText("No repository attached to this project."); return
        parts = []
        if repo.local_path: parts.append(f"Local: {repo.local_path}")
        if repo.github_full_name: parts.append(f"GitHub: {repo.github_full_name}")
        branch = repo.default_branch or "unknown branch"
        self.repo_label.setText(("  •  ".join(parts) if parts else "Repository") + f"  •  {branch}")

    def set_data(self, links: list[ResourceLink], refs: list[ExternalRef]) -> None:
        self.resources.clear(); needs_review = False
        for link in links:
            scope = "Diagram node" if link.diagram_item_id else "Document"
            baseline = (link.baseline_sha or "—")[:10]
            status = "⚠ Needs Review" if link.needs_review else "✓ Current"
            needs_review = needs_review or link.needs_review
            label = link.display_label or link.resource_value or "Repository"
            item = QTreeWidgetItem([label, scope, baseline, status]); item.setData(0, Qt.ItemDataRole.UserRole, link.id)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, link.resource_value); self.resources.addTopLevelItem(item)
        if not links: self.status.setText("No linked code")
        elif needs_review: self.status.setText("⚠ Needs Review — linked code changed")
        else: self.status.setText("✓ Current — linked code unchanged since review")
        self.review.setEnabled(bool(links))

        self.refs.clear()
        for ref in refs:
            prefix = {"pull_request": "PR", "commit": "Commit", "branch": "Branch"}.get(ref.ref_type, ref.ref_type)
            text = f"{prefix} {ref.ref_value} — {ref.title}" if ref.title else f"{prefix} {ref.ref_value}"
            item = QListWidgetItem(text); item.setData(Qt.ItemDataRole.UserRole, ref.id); self.refs.addItem(item)

    def _remove_resource(self) -> None:
        item = self.resources.currentItem()
        if item: self.removeResourceRequested.emit(int(item.data(0, Qt.ItemDataRole.UserRole)))

    def _remove_external(self) -> None:
        item = self.refs.currentItem()
        if item: self.removeExternalRequested.emit(int(item.data(Qt.ItemDataRole.UserRole)))

    def _resource_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        value = str(item.data(0, Qt.ItemDataRole.UserRole + 1) or "")
        if value: self.openResourceRequested.emit(value)
````

## `app/widgets/diagram_view.py`

````python
from __future__ import annotations

import math
import uuid
from typing import Callable

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# Shape defaults are used for legacy data and programmatic creation. New shapes are
# created by click-dragging their desired bounds, so these values are only fallbacks.
SHAPE_SIZES: dict[str, tuple[float, float]] = {
    "square": (92.0, 92.0),
    "rect": (160.0, 82.0),
    "rounded": (160.0, 82.0),
    "ellipse": (150.0, 90.0),
    "diamond": (150.0, 100.0),
}

SHAPE_LABELS: dict[str, str] = {
    "square": "Square",
    "rect": "Rectangle",
    "rounded": "Rounded",
    "ellipse": "Ellipse",
    "diamond": "Diamond",
}

MIN_SHAPE_WIDTH = 36.0
MIN_SHAPE_HEIGHT = 28.0
HANDLE_SIZE = 10.0
MIN_CREATE_DRAG = 6.0


DEFAULT_DIAGRAM_PALETTE: dict[str, str] = {
    "background": "#f7f8fa",
    "grid_minor": "#edf0f3",
    "grid_major": "#dde1e6",
    "stroke": "#596273",
    "fill": "#ffffff",
    "text": "#202124",
    "connector": "#596273",
}


def _pen(color: str, width: float = 2.0) -> QPen:
    return QPen(QColor(color), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


def _make_shape_path(shape_type: str, width: float, height: float) -> QPainterPath:
    rect = QRectF(0.0, 0.0, max(1.0, width), max(1.0, height))
    path = QPainterPath()
    if shape_type == "ellipse":
        path.addEllipse(rect)
    elif shape_type == "diamond":
        polygon = QPolygonF(
            [
                QPointF(width / 2.0, 0.0),
                QPointF(width, height / 2.0),
                QPointF(width / 2.0, height),
                QPointF(0.0, height / 2.0),
            ]
        )
        path.addPolygon(polygon)
        path.closeSubpath()
    elif shape_type == "rounded":
        radius = min(18.0, max(6.0, min(width, height) * 0.18))
        path.addRoundedRect(rect, radius, radius)
    else:
        path.addRect(rect)
    return path


def _path_points(path: QPainterPath) -> list[list[float]]:
    return [[path.elementAt(i).x, path.elementAt(i).y] for i in range(path.elementCount())]


def _translated_path(path: QPainterPath, offset: QPointF) -> QPainterPath:
    points = _path_points(path)
    if not points:
        return QPainterPath()
    translated = QPainterPath(QPointF(points[0][0] + offset.x(), points[0][1] + offset.y()))
    for x, y in points[1:]:
        translated.lineTo(x + offset.x(), y + offset.y())
    return translated


def _path_from_points(points: object) -> QPainterPath | None:
    if not isinstance(points, list) or not points:
        return None
    first = points[0]
    if not isinstance(first, list) or len(first) < 2:
        return None
    try:
        path = QPainterPath(QPointF(float(first[0]), float(first[1])))
        for point in points[1:]:
            if isinstance(point, list) and len(point) >= 2:
                path.lineTo(float(point[0]), float(point[1]))
        return path
    except (TypeError, ValueError):
        return None


class DiagramResizeHandle(QGraphicsRectItem):
    """Small drag handle used to resize a DiagramShape after creation."""

    _CURSORS = {
        "nw": Qt.CursorShape.SizeFDiagCursor,
        "se": Qt.CursorShape.SizeFDiagCursor,
        "ne": Qt.CursorShape.SizeBDiagCursor,
        "sw": Qt.CursorShape.SizeBDiagCursor,
        "n": Qt.CursorShape.SizeVerCursor,
        "s": Qt.CursorShape.SizeVerCursor,
        "e": Qt.CursorShape.SizeHorCursor,
        "w": Qt.CursorShape.SizeHorCursor,
    }

    def __init__(self, owner: "DiagramShape", role: str) -> None:
        half = HANDLE_SIZE / 2.0
        super().__init__(-half, -half, HANDLE_SIZE, HANDLE_SIZE, owner)
        self.owner = owner
        self.role = role
        self.setZValue(30.0)
        self.setCursor(self._CURSORS[role])
        self.setBrush(QBrush(QColor("#ffffff")))
        self.setPen(_pen("#4f8cff", 1.4))
        self.setVisible(False)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["connector"], 1.4))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.owner.resize_from_handle(self.role, event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.owner.finish_resize()
        event.accept()


class DiagramShape(QGraphicsPathItem):
    def __init__(
        self,
        item_id: str,
        shape_type: str,
        text: str,
        on_changed: Callable[[], None],
        width: float | None = None,
        height: float | None = None,
    ) -> None:
        super().__init__()
        self.item_id = item_id
        self.shape_type = shape_type if shape_type in SHAPE_SIZES else "rect"
        self._on_changed = on_changed
        default_width, default_height = SHAPE_SIZES[self.shape_type]
        self._width = max(MIN_SHAPE_WIDTH, float(width if width is not None else default_width))
        self._height = max(MIN_SHAPE_HEIGHT, float(height if height is not None else default_height))
        self.setPath(_make_shape_path(self.shape_type, self._width, self._height))
        self.label = QGraphicsTextItem(text, self)
        self.label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.label.setTextWidth(max(28.0, self._width - 20.0))
        self._position_label()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPen(_pen("#747b88", 1.6))
        self.setBrush(QBrush(QColor("#ffffff")))
        self._handles = {role: DiagramResizeHandle(self, role) for role in ("nw", "n", "ne", "e", "se", "s", "sw", "w")}
        self._position_handles()

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    def _position_label(self) -> None:
        self.label.setTextWidth(max(28.0, self._width - 20.0))
        label_height = self.label.boundingRect().height()
        self.label.setPos(10.0, max(4.0, (self._height - label_height) / 2.0))

    def _position_handles(self) -> None:
        x_mid = self._width / 2.0
        y_mid = self._height / 2.0
        positions = {
            "nw": QPointF(0.0, 0.0),
            "n": QPointF(x_mid, 0.0),
            "ne": QPointF(self._width, 0.0),
            "e": QPointF(self._width, y_mid),
            "se": QPointF(self._width, self._height),
            "s": QPointF(x_mid, self._height),
            "sw": QPointF(0.0, self._height),
            "w": QPointF(0.0, y_mid),
        }
        for role, handle in self._handles.items():
            handle.setPos(positions[role])

    def set_size(self, width: float, height: float, *, notify: bool = True) -> None:
        self._width = max(MIN_SHAPE_WIDTH, float(width))
        self._height = max(MIN_SHAPE_HEIGHT, float(height))
        self.setPath(_make_shape_path(self.shape_type, self._width, self._height))
        self._position_label()
        self._position_handles()
        if notify:
            self._on_changed()

    def resize_from_handle(self, role: str, scene_pos: QPointF) -> None:
        left = self.x()
        top = self.y()
        right = left + self._width
        bottom = top + self._height

        if "w" in role:
            left = min(scene_pos.x(), right - MIN_SHAPE_WIDTH)
        if "e" in role:
            right = max(scene_pos.x(), left + MIN_SHAPE_WIDTH)
        if "n" in role:
            top = min(scene_pos.y(), bottom - MIN_SHAPE_HEIGHT)
        if "s" in role:
            bottom = max(scene_pos.y(), top + MIN_SHAPE_HEIGHT)

        self.setPos(left, top)
        self.set_size(right - left, bottom - top, notify=False)
        self._on_changed()

    def finish_resize(self) -> None:
        self._on_changed()

    @property
    def text(self) -> str:
        return self.label.toPlainText()

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["stroke"], 1.6))
        self.label.setDefaultTextColor(QColor(palette["text"]))
        for handle in self._handles.values():
            handle.set_theme(palette)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            selected = bool(value)
            for handle in self._handles.values():
                handle.setVisible(selected)
        return result

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        text, ok = QInputDialog.getText(None, "Edit Shape", "Text:", text=self.text)
        if ok:
            self.label.setPlainText(text or SHAPE_LABELS.get(self.shape_type, "Shape"))
            self._position_label()
            self._on_changed()
        event.accept()


class DiagramText(QGraphicsTextItem):
    def __init__(self, item_id: str, text: str, on_changed: Callable[[], None]) -> None:
        super().__init__(text)
        self.item_id = item_id
        self._on_changed = on_changed
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setDefaultTextColor(QColor(palette["text"]))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        return result

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        text, ok = QInputDialog.getMultiLineText(None, "Edit Text", "Text:", self.toPlainText())
        if ok:
            self.setPlainText(text)
            self._on_changed()
        event.accept()


class DiagramEdge(QGraphicsPathItem):
    """Legacy node-to-node edge kept for old DevNest diagrams."""

    def __init__(self, source_id: str, target_id: str) -> None:
        super().__init__()
        self.source_id = source_id
        self.target_id = target_id
        self._start = QPointF()
        self._end = QPointF()
        self.setZValue(-10)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(_pen("#596273", 2.6))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"], 2.6))

    def set_endpoints(self, start: QPointF, end: QPointF) -> None:
        self._start = start
        self._end = end
        path = QPainterPath(start)
        path.lineTo(end)
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        _paint_arrow_head(painter, self.path(), self.pen())


class DiagramFreehand(QGraphicsPathItem):
    """A freehand drawing that can also act as a connection endpoint."""

    def __init__(
        self,
        item_id: str,
        path: QPainterPath | None,
        on_changed: Callable[[], None],
    ) -> None:
        super().__init__(path or QPainterPath())
        self.item_id = item_id
        self._on_changed = on_changed
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["stroke"], 2.2))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        return result


DiagramEndpoint = DiagramShape | DiagramText | DiagramFreehand


class DiagramConnector(QGraphicsPathItem):
    """A hand-drawn arrow whose route can optionally stay attached to shapes."""

    def __init__(
        self,
        path: QPainterPath | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> None:
        super().__init__(path or QPainterPath())
        self.source_id = source_id
        self.target_id = target_id
        self.setZValue(-6)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(_pen("#596273", 2.6))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"], 2.6))

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        _paint_arrow_head(painter, self.path(), self.pen())


def _paint_arrow_head(painter: QPainter, path: QPainterPath, pen: QPen) -> None:
    count = path.elementCount()
    if count < 2:
        return
    end_element = path.elementAt(count - 1)
    end = QPointF(end_element.x, end_element.y)
    previous: QPointF | None = None
    for index in range(count - 2, -1, -1):
        element = path.elementAt(index)
        candidate = QPointF(element.x, element.y)
        if QLineF(candidate, end).length() >= 2.0:
            previous = candidate
            break
    if previous is None:
        return
    line = QLineF(previous, end)
    angle = math.atan2(-line.dy(), line.dx())
    arrow_size = 16.0
    left = end - QPointF(
        math.sin(angle + math.pi / 3.0) * arrow_size,
        math.cos(angle + math.pi / 3.0) * arrow_size,
    )
    right = end - QPointF(
        math.sin(angle + math.pi - math.pi / 3.0) * arrow_size,
        math.cos(angle + math.pi - math.pi / 3.0) * arrow_size,
    )
    painter.setBrush(pen.color())
    painter.setPen(pen)
    painter.drawPolygon(QPolygonF([end, left, right]))


class DiagramScene(QGraphicsScene):
    diagramChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.mode = "select"
        self.current_path: DiagramFreehand | None = None  # legacy only
        self.current_connector: DiagramConnector | None = None
        self._last_draw_point: QPointF | None = None
        self._shape_preview: QGraphicsPathItem | None = None
        self._shape_start: QPointF | None = None
        self._shape_type: str | None = None
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.path_pen = _pen(self.palette["stroke"])
        self.loading = False
        self.setSceneRect(-2500, -2500, 5000, 5000)

    def set_mode(self, mode: str) -> None:
        self._cancel_shape_preview()
        if self.current_connector is not None and self.current_connector.scene() is self:
            self.removeItem(self.current_connector)
        self.mode = mode
        self.current_path = None
        self.current_connector = None
        self._last_draw_point = None

    def _notify_changed(self) -> None:
        self.update_connections()
        if not self.loading:
            self.diagramChanged.emit()

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex

    def add_shape(
        self,
        shape_type: str,
        pos: QPointF,
        text: str | None = None,
        item_id: str | None = None,
        width: float | None = None,
        height: float | None = None,
        notify: bool = True,
    ) -> DiagramShape:
        label = text if text is not None else SHAPE_LABELS.get(shape_type, "Shape")
        shape = DiagramShape(
            item_id or self._new_id(),
            shape_type,
            label,
            self._notify_changed,
            width=width,
            height=height,
        )
        shape.set_theme(self.palette)
        self.addItem(shape)
        shape.setPos(pos)
        if notify:
            self._notify_changed()
        return shape

    @staticmethod
    def _drag_rect(start: QPointF, end: QPointF) -> QRectF:
        return QRectF(start, end).normalized()

    def _begin_shape_preview(self, shape_type: str, pos: QPointF) -> None:
        self._cancel_shape_preview()
        self._shape_start = pos
        self._shape_type = shape_type if shape_type in SHAPE_SIZES else "square"
        preview = QGraphicsPathItem()
        preview.setZValue(50.0)
        pen = _pen(self.palette["connector"], 1.6)
        pen.setStyle(Qt.PenStyle.DashLine)
        preview.setPen(pen)
        fill = QColor(self.palette["fill"])
        fill.setAlpha(72)
        preview.setBrush(QBrush(fill))
        preview.setPath(_make_shape_path(self._shape_type, 1.0, 1.0))
        preview.setPos(pos)
        self.addItem(preview)
        self._shape_preview = preview

    def _update_shape_preview(self, pos: QPointF) -> None:
        if self._shape_preview is None or self._shape_start is None or self._shape_type is None:
            return
        rect = self._drag_rect(self._shape_start, pos)
        self._shape_preview.setPos(rect.topLeft())
        self._shape_preview.setPath(
            _make_shape_path(self._shape_type, max(1.0, rect.width()), max(1.0, rect.height()))
        )

    def _finish_shape_preview(self, pos: QPointF) -> DiagramShape | None:
        if self._shape_preview is None or self._shape_start is None or self._shape_type is None:
            self._cancel_shape_preview()
            return None
        rect = self._drag_rect(self._shape_start, pos)
        shape_type = self._shape_type
        self._cancel_shape_preview()
        if rect.width() < MIN_CREATE_DRAG or rect.height() < MIN_CREATE_DRAG:
            return None
        width = max(MIN_SHAPE_WIDTH, rect.width())
        height = max(MIN_SHAPE_HEIGHT, rect.height())
        shape = self.add_shape(
            shape_type,
            rect.topLeft(),
            width=width,
            height=height,
            notify=False,
        )
        self.clearSelection()
        shape.setSelected(True)
        self._notify_changed()
        return shape

    def _cancel_shape_preview(self) -> None:
        if self._shape_preview is not None and self._shape_preview.scene() is self:
            self.removeItem(self._shape_preview)
        self._shape_preview = None
        self._shape_start = None
        self._shape_type = None

    def add_text(self, pos: QPointF, text: str = "Text", item_id: str | None = None) -> DiagramText:
        item = DiagramText(item_id or self._new_id(), text, self._notify_changed)
        item.set_theme(self.palette)
        self.addItem(item)
        item.setPos(pos)
        self._notify_changed()
        return item

    def add_edge(self, source: DiagramEndpoint, target: DiagramEndpoint) -> DiagramEdge:
        if source.item_id == target.item_id:
            raise ValueError("A diagram item cannot connect to itself")
        edge = DiagramEdge(source.item_id, target.item_id)
        edge.set_theme(self.palette)
        self.addItem(edge)
        self.update_edges()
        self._notify_changed()
        return edge

    def add_freehand_path(
        self,
        path: QPainterPath,
        item_id: str | None = None,
        notify: bool = True,
    ) -> DiagramFreehand:
        item = DiagramFreehand(item_id or self._new_id(), path, self._notify_changed)
        item.set_theme(self.palette)
        self.addItem(item)
        if notify:
            self._notify_changed()
        return item

    def add_connector_path(
        self,
        path: QPainterPath,
        notify: bool = True,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> DiagramConnector:
        if not source_id or not target_id or source_id == target_id:
            raise ValueError("A connector must link two different diagram items")
        nodes = self._nodes_by_id()
        if source_id not in nodes or target_id not in nodes:
            raise ValueError("Connector endpoints must exist in the scene")
        connector = DiagramConnector(path, source_id=source_id, target_id=target_id)
        connector.set_theme(self.palette)
        self.addItem(connector)
        if notify:
            self._notify_changed()
        return connector

    def update_connections(self) -> None:
        self.update_edges()
        self.update_drawn_connectors()

    def update_edges(self) -> None:
        nodes = self._nodes_by_id()
        for item in self.items():
            if not isinstance(item, DiagramEdge):
                continue
            source = nodes.get(item.source_id)
            target = nodes.get(item.target_id)
            if source is None or target is None:
                continue
            source_center = source.sceneBoundingRect().center()
            target_center = target.sceneBoundingRect().center()
            start = self._connection_point(source, target_center)
            end = self._connection_point(target, source_center)
            item.set_endpoints(start, end)

    def update_drawn_connectors(self) -> None:
        nodes = self._nodes_by_id()
        for item in self.items():
            if not isinstance(item, DiagramConnector):
                continue
            points = _path_points(item.path())
            if len(points) < 2:
                continue
            if item.source_id and item.source_id in nodes:
                toward = QPointF(points[1][0], points[1][1])
                start = self._connection_point(nodes[item.source_id], toward)
                points[0] = [start.x(), start.y()]
            if item.target_id and item.target_id in nodes:
                toward = QPointF(points[-2][0], points[-2][1])
                end = self._connection_point(nodes[item.target_id], toward)
                points[-1] = [end.x(), end.y()]
            rebuilt = _path_from_points(points)
            if rebuilt is not None:
                item.setPath(rebuilt)

    @staticmethod
    def _scene_path(item: DiagramFreehand) -> QPainterPath:
        points = _path_points(item.path())
        if not points:
            return QPainterPath()
        first = item.mapToScene(QPointF(points[0][0], points[0][1]))
        scene_path = QPainterPath(first)
        for x, y in points[1:]:
            scene_point = item.mapToScene(QPointF(x, y))
            scene_path.lineTo(scene_point)
        return scene_path

    def _connection_point(self, item: DiagramEndpoint, toward: QPointF) -> QPointF:
        if isinstance(item, DiagramFreehand):
            # Freehand objects have no artificial center anchor. Attach the
            # connector to the actual drawn contour point nearest to the drag.
            scene_path = self._scene_path(item)
            points = _path_points(scene_path)
            if not points:
                return item.sceneBoundingRect().center()
            best = min(
                (QPointF(x, y) for x, y in points),
                key=lambda point: QLineF(point, toward).length(),
            )
            return best
        return self._boundary_point(item, toward)

    def _boundary_point(self, item: DiagramEndpoint, toward: QPointF) -> QPointF:
        rect = item.sceneBoundingRect()
        center = rect.center()
        dx = toward.x() - center.x()
        dy = toward.y() - center.y()
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            return center
        half_w = max(1.0, rect.width() / 2.0)
        half_h = max(1.0, rect.height() / 2.0)
        shape_type = item.shape_type if isinstance(item, DiagramShape) else "rect"
        if shape_type == "ellipse":
            scale = 1.0 / math.sqrt((dx / half_w) ** 2 + (dy / half_h) ** 2)
        elif shape_type == "diamond":
            scale = 1.0 / (abs(dx) / half_w + abs(dy) / half_h)
        else:
            scale = min(half_w / max(abs(dx), 1e-6), half_h / max(abs(dy), 1e-6))
        return QPointF(center.x() + dx * scale, center.y() + dy * scale)

    def _nodes_by_id(self) -> dict[str, DiagramEndpoint]:
        result: dict[str, DiagramEndpoint] = {}
        for item in self.items():
            if isinstance(item, (DiagramShape, DiagramText, DiagramFreehand)):
                result[item.item_id] = item
        return result

    def _endpoint_at(self, pos: QPointF) -> DiagramEndpoint | None:
        # First prefer the exact Qt hit-test, including child text labels.
        for item in self.items(pos):
            current = item
            while current is not None:
                if isinstance(current, (DiagramShape, DiagramText, DiagramFreehand)):
                    return current
                current = current.parentItem()

        # A hand-drawn box/circle often has an empty interior. Treat the interior
        # of its bounding box as a practical hit area so connecting does not
        # require pixel-perfect clicking on the pen stroke. Smallest match wins.
        candidates: list[DiagramFreehand] = []
        for item in self.items():
            if isinstance(item, DiagramFreehand) and item.sceneBoundingRect().adjusted(-8, -8, 8, 8).contains(pos):
                candidates.append(item)
        if candidates:
            return min(candidates, key=lambda item: item.sceneBoundingRect().width() * item.sceneBoundingRect().height())
        return None

    @staticmethod
    def _append_sample(item: QGraphicsPathItem, pos: QPointF, previous: QPointF | None) -> QPointF:
        if previous is not None and QLineF(previous, pos).length() < 1.5:
            return previous
        path = item.path()
        path.lineTo(pos)
        item.setPath(path)
        return pos

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        pos = event.scenePos()
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode.startswith("shape:"):
                self._begin_shape_preview(self.mode.split(":", 1)[1], pos)
                event.accept()
                return
            if self.mode == "text":
                text, ok = QInputDialog.getText(None, "Text", "Text:")
                if ok:
                    self.add_text(pos, text or "Text")
                event.accept()
                return
            if self.mode == "connect":
                source = self._endpoint_at(pos)
                if source is None:
                    self.current_connector = None
                    self._last_draw_point = None
                    event.accept()
                    return
                start = self._connection_point(source, pos)
                path = QPainterPath(start)
                self.current_connector = DiagramConnector(path, source_id=source.item_id)
                self.current_connector.set_theme(self.palette)
                self.addItem(self.current_connector)
                self._last_draw_point = start
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mode.startswith("shape:") and self._shape_preview is not None:
            self._update_shape_preview(event.scenePos())
            event.accept()
            return
        if self.mode == "connect" and self.current_connector is not None:
            self._last_draw_point = self._append_sample(
                self.current_connector, event.scenePos(), self._last_draw_point
            )
            points = _path_points(self.current_connector.path())
            nodes = self._nodes_by_id()
            source = nodes.get(self.current_connector.source_id or "")
            if source is not None and len(points) >= 2:
                toward = QPointF(points[1][0], points[1][1])
                start = self._connection_point(source, toward)
                points[0] = [start.x(), start.y()]
                rebuilt = _path_from_points(points)
                if rebuilt is not None:
                    self.current_connector.setPath(rebuilt)
            event.accept()
            return
        super().mouseMoveEvent(event)
        self.update_connections()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.mode.startswith("shape:"):
            self._finish_shape_preview(event.scenePos())
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton and self.mode == "connect":
            item = self.current_connector
            if item is not None:
                self._append_sample(item, event.scenePos(), self._last_draw_point)
                keep_item = item.path().elementCount() >= 2
                target = self._endpoint_at(event.scenePos())
                valid_target = (
                    target is not None
                    and item.source_id is not None
                    and target.item_id != item.source_id
                )
                if not valid_target:
                    keep_item = False
                else:
                    item.target_id = target.item_id
                    points = _path_points(item.path())
                    if len(points) >= 2:
                        end = self._connection_point(target, QPointF(points[-2][0], points[-2][1]))
                        points[-1] = [end.x(), end.y()]
                        rebuilt = _path_from_points(points)
                        if rebuilt is not None:
                            item.setPath(rebuilt)
                if not keep_item and item.scene() is self:
                    self.removeItem(item)
                self.current_connector = None
                self._last_draw_point = None
                if keep_item:
                    self._notify_changed()
            event.accept()
            return

        super().mouseReleaseEvent(event)
        self._notify_changed()

    def delete_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        node_ids = {item.item_id for item in selected if isinstance(item, (DiagramShape, DiagramText, DiagramFreehand))}
        for item in list(self.items()):
            if isinstance(item, (DiagramEdge, DiagramConnector)) and (
                item.source_id in node_ids or item.target_id in node_ids
            ):
                self.removeItem(item)
        for item in selected:
            if item.scene() is self:
                self.removeItem(item)
        self._notify_changed()

    def duplicate_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        self.clearSelection()
        created = False
        offset = QPointF(24.0, 24.0)
        for item in selected:
            if isinstance(item, DiagramShape):
                copy = self.add_shape(item.shape_type, item.pos() + offset, item.text, width=item.width, height=item.height)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramText):
                copy = self.add_text(item.pos() + offset, item.toPlainText())
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramFreehand):
                scene_path = self._scene_path(item)
                path = _translated_path(scene_path, offset)
                copy = self.add_freehand_path(path, notify=False)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramConnector):
                path = _translated_path(item.path(), offset)
                copy = self.add_connector_path(
                    path, notify=False, source_id=item.source_id, target_id=item.target_id
                )
                copy.setSelected(True)
                created = True
        if created:
            self._notify_changed()

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        if isinstance(palette, bool):
            # Compatibility with older caller code/tests.
            palette = {
                **DEFAULT_DIAGRAM_PALETTE,
                **(
                    {
                        "background": "#151515",
                        "grid_minor": "#1d1d1d",
                        "grid_major": "#292929",
                        "stroke": "#c4c7cc",
                        "fill": "#1b1b1b",
                        "text": "#f0f0f0",
                        "connector": "#c4c7cc",
                    }
                    if palette
                    else {}
                ),
            }
        self.palette = {**DEFAULT_DIAGRAM_PALETTE, **palette}
        self.setBackgroundBrush(QBrush(QColor(self.palette["background"])))
        self.path_pen = _pen(self.palette["stroke"])
        for item in self.items():
            if isinstance(item, (DiagramShape, DiagramText, DiagramEdge, DiagramFreehand, DiagramConnector)):
                item.set_theme(self.palette)

    def to_data(self) -> dict[str, object]:
        nodes: list[dict[str, object]] = []
        edges: list[dict[str, object]] = []
        paths: list[dict[str, object]] = []
        connectors: list[dict[str, object]] = []
        for item in self.items():
            if isinstance(item, DiagramShape):
                nodes.append(
                    {
                        "type": "shape",
                        "shape": item.shape_type,
                        "id": item.item_id,
                        "x": item.x(),
                        "y": item.y(),
                        "text": item.text,
                        "width": item.width,
                        "height": item.height,
                    }
                )
            elif isinstance(item, DiagramText):
                nodes.append(
                    {
                        "type": "text",
                        "id": item.item_id,
                        "x": item.x(),
                        "y": item.y(),
                        "text": item.toPlainText(),
                    }
                )
            elif isinstance(item, DiagramEdge):
                edges.append({"source": item.source_id, "target": item.target_id})
            elif isinstance(item, DiagramConnector):
                points = _path_points(item.path())
                if (
                    points
                    and item.source_id
                    and item.target_id
                    and item.source_id != item.target_id
                ):
                    connectors.append(
                        {
                            "points": points,
                            "source": item.source_id,
                            "target": item.target_id,
                        }
                    )
            elif isinstance(item, DiagramFreehand):
                points = _path_points(self._scene_path(item))
                if points:
                    paths.append({"id": item.item_id, "points": points})
        return {"version": 5, "items": nodes, "edges": edges, "paths": paths, "connectors": connectors}

    def load_data(self, data: dict[str, object]) -> None:
        self.loading = True
        try:
            self.current_path = None
            self.current_connector = None
            self._last_draw_point = None
            self._shape_preview = None
            self._shape_start = None
            self._shape_type = None
            self.clear()
            id_map: dict[str, DiagramEndpoint] = {}
            for raw in data.get("items", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                item_id = str(raw.get("id", self._new_id()))
                try:
                    pos = QPointF(float(raw.get("x", 0.0)), float(raw.get("y", 0.0)))
                except (TypeError, ValueError):
                    pos = QPointF()
                text = str(raw.get("text", "Shape"))
                item_type = str(raw.get("type", "node"))
                if item_type == "text":
                    item = self.add_text(pos, text, item_id)
                else:
                    # Version 1 stored rectangle nodes as type="node" without a shape field.
                    shape_type = str(raw.get("shape", "rect"))
                    try:
                        width = float(raw["width"]) if "width" in raw else None
                        height = float(raw["height"]) if "height" in raw else None
                    except (TypeError, ValueError):
                        width = None
                        height = None
                    item = self.add_shape(
                        shape_type, pos, text, item_id, width=width, height=height, notify=False
                    )
                id_map[item_id] = item

            for raw in data.get("edges", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                source = id_map.get(str(raw.get("source", "")))
                target = id_map.get(str(raw.get("target", "")))
                if source is not None and target is not None and source is not target:
                    self.add_edge(source, target)

            for raw in data.get("paths", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is None:
                    continue
                item_id = str(raw.get("id", self._new_id()))
                path_item = self.add_freehand_path(path, item_id=item_id, notify=False)
                id_map[item_id] = path_item

            for raw in data.get("connectors", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is not None:
                    source_id = str(raw.get("source")) if raw.get("source") else None
                    target_id = str(raw.get("target")) if raw.get("target") else None
                    # Version 4+ only accepts connectors that are anchored at both ends.
                    # Legacy floating connectors are intentionally ignored instead of
                    # reintroducing arrows that point to empty canvas space.
                    if (
                        source_id in id_map
                        and target_id in id_map
                        and source_id != target_id
                    ):
                        self.add_connector_path(
                            path, notify=False, source_id=source_id, target_id=target_id
                        )

            self.update_connections()
            self.set_theme(self.palette)
        finally:
            self.loading = False


class DiagramCanvas(QGraphicsView):
    def __init__(self, scene: DiagramScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._middle_panning = False
        self._middle_pan_pos = QPointF()


    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_panning = True
            self._middle_pan_pos = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._middle_panning:
            current = event.position()
            delta = current - self._middle_pan_pos
            self._middle_pan_pos = current
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._middle_panning:
            self._middle_panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def set_mode(self, mode: str) -> None:
        if mode == "pan":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        if isinstance(palette, bool):
            self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
            if palette:
                self.palette.update(
                    {
                        "background": "#151515",
                        "grid_minor": "#1d1d1d",
                        "grid_major": "#292929",
                    }
                )
        else:
            self.palette = {**DEFAULT_DIAGRAM_PALETTE, **palette}
        self.viewport().update()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(self.palette["background"]))
        minor = 25
        major = 100
        left = int(math.floor(rect.left() / minor) * minor)
        top = int(math.floor(rect.top() / minor) * minor)
        minor_pen = QPen(QColor(self.palette["grid_minor"]), 1.0)
        major_pen = QPen(QColor(self.palette["grid_major"]), 1.0)
        x = left
        while x < rect.right():
            painter.setPen(major_pen if x % major == 0 else minor_pen)
            painter.drawLine(QLineF(float(x), rect.top(), float(x), rect.bottom()))
            x += minor
        y = top
        while y < rect.bottom():
            painter.setPen(major_pen if y % major == 0 else minor_pen)
            painter.drawLine(QLineF(rect.left(), float(y), rect.right(), float(y)))
            y += minor

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def keyPressEvent(self, event) -> None:
        scene = self.scene()
        if isinstance(scene, DiagramScene):
            if event.key() == Qt.Key.Key_Delete:
                scene.delete_selected()
                event.accept()
                return
            if event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                scene.duplicate_selected()
                event.accept()
                return
        super().keyPressEvent(event)

    def fit_all(self) -> None:
        scene = self.scene()
        if scene is None:
            return
        bounds = scene.itemsBoundingRect()
        if bounds.isNull() or bounds.isEmpty():
            self.resetTransform()
            return
        self.fitInView(bounds.adjusted(-60, -60, 60, 60), Qt.AspectRatioMode.KeepAspectRatio)


class DiagramView(QWidget):
    diagramChanged = Signal()
    selectionChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 4, 6, 0)
        self.scene = DiagramScene(self)
        self.scene.diagramChanged.connect(self.diagramChanged)
        self.scene.selectionChanged.connect(self.selectionChanged)
        self.canvas = DiagramCanvas(self.scene)
        self._mode_buttons: dict[str, QPushButton] = {}

        tools = [
            ("Select", "select", "Select/move items; selected shapes show resize handles"),
            ("Pan", "pan", "Pan the canvas (middle mouse drag works in every tool)"),
            ("Square", "shape:square", "Press and drag to draw a box at exactly the size you want; stretch it into a rectangle if needed"),
            ("Round", "shape:rounded", "Press and drag to draw a rounded box at the size you want"),
            ("Ellipse", "shape:ellipse", "Press and drag to draw an ellipse at the size you want"),
            ("Diamond", "shape:diamond", "Press and drag to draw a decision diamond at the size you want"),
            ("Text", "text", "Add standalone text"),
            ("Connect", "connect", "Start on one existing item and drag any route to another item; the arrow points to the target"),
        ]
        for label, mode, tooltip in tools:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setToolTip(tooltip)
            button.clicked.connect(lambda _checked=False, m=mode: self.set_mode(m))
            bar.addWidget(button)
            self._mode_buttons[mode] = button

        bar.addStretch(1)
        duplicate = QPushButton("Duplicate")
        duplicate.setToolTip("Duplicate selected diagram items (Ctrl+D)")
        duplicate.clicked.connect(self.scene.duplicate_selected)
        fit = QPushButton("Fit")
        fit.setToolTip("Fit all diagram items in view")
        fit.clicked.connect(self.canvas.fit_all)
        zoom_out = QPushButton("−")
        zoom_out.setToolTip("Zoom out")
        zoom_out.clicked.connect(lambda: self.canvas.scale(0.85, 0.85))
        zoom_in = QPushButton("+")
        zoom_in.setToolTip("Zoom in")
        zoom_in.clicked.connect(lambda: self.canvas.scale(1.15, 1.15))
        delete = QPushButton("Delete")
        delete.setToolTip("Delete selected diagram items (Delete)")
        delete.clicked.connect(self.scene.delete_selected)
        for button in (duplicate, fit, zoom_out, zoom_in, delete):
            bar.addWidget(button)

        hint = QLabel(
            "Square/Round/Ellipse/Diamond: basılı tutup sürükleyerek istediğin boyutta çiz. Select: seçili şeklin 8 tutamacından yeniden boyutlandır. Connect: bir öğeden diğerine rota çiz. Orta mouse: canvas taşı."
        )
        hint.setObjectName("diagramHint")
        hint.setContentsMargins(8, 0, 8, 2)

        root.addLayout(bar)
        root.addWidget(hint)
        root.addWidget(self.canvas, 1)
        self.set_mode("shape:square")

    def set_mode(self, mode: str) -> None:
        self.scene.set_mode(mode)
        self.canvas.set_mode(mode)
        for button_mode, button in self._mode_buttons.items():
            button.setChecked(button_mode == mode)

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        self.scene.set_theme(palette)
        self.canvas.set_theme(palette)

    def load_data(self, data: dict[str, object]) -> None:
        self.scene.load_data(data)
        self.canvas.resetTransform()

    def to_data(self) -> dict[str, object]:
        return self.scene.to_data()

    def selected_item_id(self) -> str | None:
        for item in self.scene.selectedItems():
            item_id = getattr(item, "item_id", None)
            if item_id:
                return str(item_id)
        return None

    def delete_selected(self) -> None:
        self.scene.delete_selected()
````

## `app/widgets/find_bar.py`

````python
from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FindLineEdit(QLineEdit):
    escapePressed = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.escapePressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class EditorFindBar(QWidget):
    queryChanged = Signal(str)
    findRequested = Signal(str)
    closeRequested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("editorFindBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 6, 7, 6)
        layout.setSpacing(6)

        self.query_edit = FindLineEdit(self)
        self.query_edit.setObjectName("editorFindInput")
        self.query_edit.setPlaceholderText("Find in note…")
        self.query_edit.setClearButtonEnabled(True)
        self.query_edit.setMinimumWidth(180)
        self.query_edit.setMaximumWidth(320)
        self.query_edit.textChanged.connect(self.queryChanged)
        self.query_edit.returnPressed.connect(self._emit_find)
        self.query_edit.escapePressed.connect(self.closeRequested)
        layout.addWidget(self.query_edit, 1)

        self.result_label = QLabel("0 matches", self)
        self.result_label.setObjectName("editorFindCount")
        self.result_label.setMinimumWidth(68)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

        self.down_checkbox = QCheckBox("↓ Down", self)
        self.down_checkbox.setObjectName("editorFindDirection")
        self.up_checkbox = QCheckBox("↑ Up", self)
        self.up_checkbox.setObjectName("editorFindDirection")
        self.direction_group = QButtonGroup(self)
        self.direction_group.setExclusive(True)
        self.direction_group.addButton(self.down_checkbox)
        self.direction_group.addButton(self.up_checkbox)
        self.down_checkbox.toggled.connect(self._ensure_direction_selected)
        self.up_checkbox.toggled.connect(self._ensure_direction_selected)
        self.down_checkbox.setChecked(True)
        layout.addWidget(self.down_checkbox)
        layout.addWidget(self.up_checkbox)

        self.find_button = QPushButton("Find", self)
        self.find_button.setObjectName("editorFindButton")
        self.find_button.setToolTip("Find the next match in the selected direction (Enter)")
        self.find_button.clicked.connect(self._emit_find)
        layout.addWidget(self.find_button)

        self.close_button = QPushButton("×", self)
        self.close_button.setObjectName("editorFindClose")
        self.close_button.setFixedWidth(30)
        self.close_button.setToolTip("Close search (Esc)")
        self.close_button.clicked.connect(self.closeRequested)
        layout.addWidget(self.close_button)

    def direction(self) -> str:
        return "up" if self.up_checkbox.isChecked() else "down"

    def set_query(self, text: str) -> None:
        self.query_edit.setText(text)

    def focus_query(self, select_all: bool = True) -> None:
        self.query_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        if select_all:
            self.query_edit.selectAll()

    def set_result_count(self, count: int, active_index: int | None = None) -> None:
        if count <= 0:
            self.result_label.setText("0 matches")
        elif active_index is None:
            self.result_label.setText(f"{count} matches")
        else:
            self.result_label.setText(f"{active_index + 1} / {count}")

    def _ensure_direction_selected(self, _checked: bool) -> None:
        if not self.down_checkbox.isChecked() and not self.up_checkbox.isChecked():
            self.down_checkbox.setChecked(True)

    def _emit_find(self) -> None:
        if self.query_edit.text():
            self.findRequested.emit(self.direction())
````

## `app/widgets/note_editor.py`

````python
from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
    QTextListFormat,
)
from PySide6.QtWidgets import QMenu, QScrollBar, QTextEdit

from app.widgets.find_bar import EditorFindBar

from app.constants import TAB_SPACES

TASK_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<marker>☐|☑)(?: (?P<text>.*))?$")
NUMBERED_TEXT_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<number>\d+)\.(?: (?P<text>.*))?$")

class SearchMarkerScrollBar(QScrollBar):
    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        self._markers: list[float] = []
        self._active_marker: float | None = None
        self._marker_color = QColor("#d0a84b")
        self._active_color = QColor("#f2cf70")

    def set_markers(self, markers: list[float], active_marker: float | None = None) -> None:
        self._markers = [max(0.0, min(1.0, marker)) for marker in markers]
        self._active_marker = None if active_marker is None else max(0.0, min(1.0, active_marker))
        self.update()

    def set_marker_colors(self, marker: str, active: str) -> None:
        self._marker_color = QColor(marker)
        self._active_color = QColor(active)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.orientation() != Qt.Orientation.Vertical or not self._markers:
            return
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        top = 2
        marker_height = 2
        usable_height = max(1, self.height() - top * 2 - marker_height)
        width = max(3, self.width() - 4)
        for ratio in self._markers:
            y = top + int(round(ratio * usable_height))
            painter.fillRect(2, y, width, marker_height, self._marker_color)
        if self._active_marker is not None:
            y = top + int(round(self._active_marker * usable_height))
            painter.fillRect(1, max(0, y - 1), max(4, self.width() - 2), 4, self._active_color)


class NoteEditor(QTextEdit):
    taskStateChanged = Signal()
    numberedListModeChanged = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.auto_checkbox_enabled = True
        self.blank_line_after_enter = False
        self.numbered_list_mode_enabled = False
        self.tab_spaces = TAB_SPACES
        self.base_font_size = 12
        self.setAcceptRichText(True)
        self.setUndoRedoEnabled(True)
        self.setPlaceholderText("Write notes, tasks, bugs, ideas, or plans…")
        self.setTabChangesFocus(False)
        self.setMouseTracking(True)

        self._search_query = ""
        self._search_ranges: list[tuple[int, int]] = []
        self._search_active_index: int | None = None
        self._search_anchor_position = 0
        self._search_match_background = QColor("#d9c36a")
        self._search_match_foreground = QColor("#1a1a1a")
        self._search_current_background = QColor("#f0b94d")
        self._search_current_foreground = QColor("#111111")

        self._search_scrollbar = SearchMarkerScrollBar(Qt.Orientation.Vertical, self)
        self.setVerticalScrollBar(self._search_scrollbar)
        self.find_bar = EditorFindBar(self)
        self.find_bar.hide()
        self.find_bar.queryChanged.connect(self._set_search_query)
        self.find_bar.findRequested.connect(self.find_search_match)
        self.find_bar.closeRequested.connect(self.hide_find_bar)
        self.textChanged.connect(self._refresh_search_after_edit)

        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(self.base_font_size)
        self.setFont(font)

    def show_find_bar(self) -> None:
        selected = self.textCursor().selectedText().replace("\u2029", "\n")
        if selected and "\n" not in selected and len(selected) <= 160:
            self.find_bar.set_query(selected)
        self._search_anchor_position = self.textCursor().selectionEnd()
        self.find_bar.show()
        self.find_bar.raise_()
        self._position_find_bar()
        if self.find_bar.query_edit.text():
            self._set_search_query(self.find_bar.query_edit.text())
        self.find_bar.focus_query(select_all=True)

    def hide_find_bar(self) -> None:
        self.find_bar.hide()
        self._search_query = ""
        self._search_ranges.clear()
        self._search_active_index = None
        self.setExtraSelections([])
        self._search_scrollbar.set_markers([])
        self.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def is_find_bar_visible(self) -> bool:
        return self.find_bar.isVisible()

    def search_match_ranges(self) -> tuple[tuple[int, int], ...]:
        return tuple(self._search_ranges)

    def active_search_range(self) -> tuple[int, int] | None:
        if self._search_active_index is None or not self._search_ranges:
            return None
        return self._search_ranges[self._search_active_index]

    def set_search_theme(
        self,
        *,
        match_background: str,
        match_foreground: str,
        current_background: str,
        current_foreground: str,
        marker: str,
        current_marker: str,
    ) -> None:
        self._search_match_background = QColor(match_background)
        self._search_match_foreground = QColor(match_foreground)
        self._search_current_background = QColor(current_background)
        self._search_current_foreground = QColor(current_foreground)
        self._search_scrollbar.set_marker_colors(marker, current_marker)
        self._render_search_highlights()

    def find_search_match(self, direction: str = "down") -> bool:
        if not self._search_ranges:
            self.find_bar.set_result_count(0)
            return False

        direction = "up" if direction == "up" else "down"
        if self._search_active_index is None:
            self._search_active_index = self._initial_search_index(direction)
        elif direction == "down":
            self._search_active_index = (self._search_active_index + 1) % len(self._search_ranges)
        else:
            self._search_active_index = (self._search_active_index - 1) % len(self._search_ranges)

        start, end = self._search_ranges[self._search_active_index]
        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self.find_bar.set_result_count(len(self._search_ranges), self._search_active_index)
        self._render_search_highlights()
        return True

    def _initial_search_index(self, direction: str) -> int:
        anchor = max(0, min(self.document().characterCount() - 1, self._search_anchor_position))
        if direction == "up":
            for index in range(len(self._search_ranges) - 1, -1, -1):
                start, end = self._search_ranges[index]
                if end <= anchor:
                    return index
            return len(self._search_ranges) - 1
        for index, (start, _end) in enumerate(self._search_ranges):
            if start >= anchor:
                return index
        return 0

    def _set_search_query(self, query: str) -> None:
        self._search_query = query
        self._search_active_index = None
        self._search_anchor_position = self.textCursor().selectionEnd()
        self._collect_search_matches()
        self.find_bar.set_result_count(len(self._search_ranges))
        self._render_search_highlights()

    def _refresh_search_after_edit(self) -> None:
        if not self._search_query:
            return
        active_start = None
        if self._search_active_index is not None and self._search_ranges:
            active_start = self._search_ranges[self._search_active_index][0]
        self._collect_search_matches()
        self._search_active_index = None
        if active_start is not None and self._search_ranges:
            nearest = min(range(len(self._search_ranges)), key=lambda index: abs(self._search_ranges[index][0] - active_start))
            self._search_active_index = nearest
        self.find_bar.set_result_count(len(self._search_ranges), self._search_active_index)
        self._render_search_highlights()

    def _collect_search_matches(self) -> None:
        self._search_ranges.clear()
        query = self._search_query
        if not query:
            return
        document = self.document()
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        while True:
            match = document.find(query, cursor)
            if match.isNull() or not match.hasSelection():
                break
            start = match.selectionStart()
            end = match.selectionEnd()
            if end <= start:
                break
            self._search_ranges.append((start, end))
            cursor.setPosition(end)

    def _render_search_highlights(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        for index, (start, end) in enumerate(self._search_ranges):
            selection = QTextEdit.ExtraSelection()
            cursor = QTextCursor(self.document())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor
            if index == self._search_active_index:
                selection.format.setBackground(self._search_current_background)
                selection.format.setForeground(self._search_current_foreground)
            else:
                selection.format.setBackground(self._search_match_background)
                selection.format.setForeground(self._search_match_foreground)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, False)
            selections.append(selection)
        self.setExtraSelections(selections)
        marker_positions = [self._search_marker_ratio(start) for start, _end in self._search_ranges]
        active_marker = None
        if self._search_active_index is not None and self._search_ranges:
            active_marker = marker_positions[self._search_active_index]
        self._search_scrollbar.set_markers(marker_positions, active_marker)

    def _search_marker_ratio(self, position: int) -> float:
        document = self.document()
        document_height = max(1.0, document.size().height())
        cursor = QTextCursor(document)
        cursor.setPosition(max(0, min(position, document.characterCount() - 1)))
        block = cursor.block()
        layout = block.layout()
        block_rect = document.documentLayout().blockBoundingRect(block)
        line = layout.lineForTextPosition(cursor.positionInBlock()) if layout is not None else None
        y = block_rect.top()
        if line is not None and line.isValid():
            y += line.y() + line.height() / 2.0
        return max(0.0, min(1.0, y / document_height))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_find_bar()

    def _position_find_bar(self) -> None:
        if not self.find_bar.isVisible():
            return
        self.find_bar.adjustSize()
        available_width = max(260, self.viewport().width() - 18)
        width = min(max(self.find_bar.sizeHint().width(), 520), available_width)
        self.find_bar.resize(width, self.find_bar.sizeHint().height())
        x = max(6, self.viewport().geometry().right() - width - 6)
        y = self.viewport().geometry().top() + 6
        self.find_bar.move(x, y)
        self.find_bar.raise_()

    def set_editor_font_size(self, size: int) -> None:
        self.base_font_size = max(8, min(32, size))
        font = self.font()
        font.setPointSize(self.base_font_size)
        self.setFont(font)

    def apply_font_family(self, family: str) -> None:
        if not family:
            return
        fmt = QTextCharFormat()
        fmt.setFontFamilies([family])
        self._merge_font_format(fmt)

    def apply_font_point_size(self, size: int) -> None:
        size = max(8, min(48, int(size)))
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size))
        self._merge_font_format(fmt)

    def apply_font_weight(self, weight: int) -> None:
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        fmt = QTextCharFormat()
        fmt.setFontWeight(weight)
        self._merge_font_format(fmt)

    def set_tab_width(self, spaces: int) -> None:
        self.tab_spaces = max(2, min(8, spaces))
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(" ") * self.tab_spaces)

    def set_auto_checkbox(self, enabled: bool) -> None:
        self.auto_checkbox_enabled = enabled

    def set_blank_line_after_enter(self, enabled: bool) -> None:
        self.blank_line_after_enter = enabled

    def insert_checkbox(self) -> None:
        cursor = self.textCursor()
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if match:
            self.toggle_checkbox(block)
            return
        block_pos = block.position()
        leading = len(block.text()) - len(block.text().lstrip(" "))
        cursor.setPosition(block_pos + leading)
        cursor.insertText("☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(cursor.block(), checked=False)
        self.taskStateChanged.emit()

    def toggle_checkbox_at_cursor(self) -> bool:
        block = self.textCursor().block()
        if not TASK_LINE_RE.match(block.text()):
            return False
        self.toggle_checkbox(block)
        return True

    def toggle_checkbox(self, block: QTextBlock) -> None:
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return
        marker_pos = block.position() + len(match.group("indent"))
        cursor = QTextCursor(self.document())
        cursor.setPosition(marker_pos)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        checked = match.group("marker") == "☐"
        cursor.insertText("☑" if checked else "☐")
        updated_block = self.document().findBlock(marker_pos)
        self._apply_task_style(updated_block, checked=checked)
        self.taskStateChanged.emit()

    def _apply_task_style(self, block: QTextBlock, checked: bool) -> None:
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return
        indent_len = len(match.group("indent"))
        marker_pos = block.position() + indent_len
        text_start = marker_pos + 1
        if block.text()[indent_len + 1 :].startswith(" "):
            text_start += 1

        marker_cursor = QTextCursor(self.document())
        marker_cursor.setPosition(marker_pos)
        marker_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        marker_fmt = QTextCharFormat()
        marker_fmt.setFontStrikeOut(False)
        marker_cursor.mergeCharFormat(marker_fmt)

        if text_start < block.position() + len(block.text()):
            text_cursor = QTextCursor(self.document())
            text_cursor.setPosition(text_start)
            text_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            text_fmt = QTextCharFormat()
            text_fmt.setFontStrikeOut(checked)
            text_cursor.mergeCharFormat(text_fmt)

    def toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        current = self.textCursor().charFormat().fontWeight()
        fmt.setFontWeight(QFont.Weight.Normal if current >= QFont.Weight.Bold else QFont.Weight.Bold)
        self._merge_font_format(fmt)

    def toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.textCursor().charFormat().fontItalic())
        self._merge_format(fmt)

    def toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.textCursor().charFormat().fontUnderline())
        self._merge_format(fmt)

    def toggle_strikethrough(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not self.textCursor().charFormat().fontStrikeOut())
        self._merge_format(fmt)

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.textCursor()
        cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def _merge_font_format(self, fmt: QTextCharFormat) -> None:
        """Apply font properties without leaving task/list markers behind.

        Checkbox markers are ordinary document characters, while Qt bullet and
        numbered-list markers are block decorations.  When the cursor is on a
        decorated line we therefore update both the text fragments and the
        block character format used to paint the list marker.
        """
        visible_cursor = self.textCursor()
        start = visible_cursor.selectionStart()
        end = visible_cursor.selectionEnd()

        if visible_cursor.hasSelection():
            visible_cursor.mergeCharFormat(fmt)
            self._format_decorated_markers(start, end, fmt)
            self.setTextCursor(visible_cursor)
            self.mergeCurrentCharFormat(fmt)
            return

        block = visible_cursor.block()
        is_task = bool(TASK_LINE_RE.match(block.text()))
        is_list_item = block.textList() is not None
        if is_task or is_list_item:
            line_cursor = QTextCursor(self.document())
            line_cursor.setPosition(block.position())
            line_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            if line_cursor.hasSelection():
                line_cursor.mergeCharFormat(fmt)
            if is_list_item:
                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockCharFormat(fmt)
            self.setTextCursor(visible_cursor)
            self.mergeCurrentCharFormat(fmt)
            return

        visible_cursor.mergeCharFormat(fmt)
        self.setTextCursor(visible_cursor)
        self.mergeCurrentCharFormat(fmt)

    def _format_decorated_markers(self, start: int, end: int, fmt: QTextCharFormat) -> None:
        document = self.document()
        block = document.findBlock(start)
        if end > start and document.findBlock(end).position() == end:
            last_position = max(start, end - 1)
        else:
            last_position = end
        last_block = document.findBlock(last_position)

        while block.isValid():
            task_match = TASK_LINE_RE.match(block.text())
            if task_match:
                marker_position = block.position() + len(task_match.group("indent"))
                marker_cursor = QTextCursor(document)
                marker_cursor.setPosition(marker_position)
                marker_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
                marker_cursor.mergeCharFormat(fmt)
            if block.textList() is not None:
                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockCharFormat(fmt)
            if block == last_block:
                break
            block = block.next()

    def set_heading(self, level: int) -> None:
        sizes = {0: self.base_font_size, 1: self.base_font_size + 10, 2: self.base_font_size + 6, 3: self.base_font_size + 3}
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        fmt = QTextCharFormat()
        fmt.setFontPointSize(sizes.get(level, self.base_font_size))
        fmt.setFontWeight(QFont.Weight.Bold if level else QFont.Weight.Normal)
        cursor.mergeCharFormat(fmt)

    def make_bullet_list(self) -> None:
        self._make_list(QTextListFormat.Style.ListDisc)

    def make_numbered_list(self) -> None:
        """Enable the plain-text numbered list mode.

        Unlike QTextList's decimal markers, these numbers are real document
        characters so Select All / Copy / TXT export includes them.
        """
        self.set_numbered_list_mode(True)

    def set_numbered_list_mode(self, enabled: bool) -> None:
        self.numbered_list_mode_enabled = bool(enabled)
        if self.numbered_list_mode_enabled:
            self._number_selected_or_current_blocks()

    def _number_selected_or_current_blocks(self) -> None:
        visible_cursor = self.textCursor()
        document = self.document()
        selection_start = visible_cursor.selectionStart()
        selection_end = visible_cursor.selectionEnd()
        original_position = visible_cursor.position()
        original_position_in_block = visible_cursor.positionInBlock()
        original_block_text = visible_cursor.block().text()
        original_match = NUMBERED_TEXT_LINE_RE.match(original_block_text)
        original_indent_len = (
            len(original_match.group("indent"))
            if original_match
            else len(original_block_text) - len(original_block_text.lstrip(" "))
        )
        original_prefix_len = 0
        if original_match:
            original_prefix = f"{original_match.group('number')}."
            if original_block_text[len(original_match.group("indent")) + len(original_prefix) :].startswith(" "):
                original_prefix += " "
            original_prefix_len = len(original_prefix)
            if not visible_cursor.hasSelection():
                # Re-enabling the mode on an existing numbered item should
                # continue from that number instead of resetting it to 1.
                return

        end_lookup = max(selection_start, selection_end - 1) if visible_cursor.hasSelection() else selection_start
        first_block = document.findBlock(selection_start)
        last_block = document.findBlock(end_lookup)

        blocks: list[QTextBlock] = []
        block = first_block
        while block.isValid():
            blocks.append(block)
            if block == last_block:
                break
            block = block.next()

        # Edit from bottom to top so positions of blocks that still need work
        # remain stable while prefixes are inserted/replaced.
        edit = QTextCursor(document)
        edit.beginEditBlock()
        try:
            for number, block in reversed(list(enumerate(blocks, start=1))):
                text = block.text()
                existing = NUMBERED_TEXT_LINE_RE.match(text)
                indent = existing.group("indent") if existing else text[: len(text) - len(text.lstrip(" "))]
                prefix_start = block.position() + len(indent)
                block_cursor = QTextCursor(document)
                block_cursor.setPosition(prefix_start)
                if existing:
                    old_prefix = f"{existing.group('number')}."
                    if text[len(indent) + len(old_prefix) :].startswith(" "):
                        old_prefix += " "
                    block_cursor.setPosition(prefix_start + len(old_prefix), QTextCursor.MoveMode.KeepAnchor)
                block_cursor.insertText(f"{number}. ")
        finally:
            edit.endEditBlock()

        # Preserve the caret relative to the user's text. The prefix is real
        # text, so a cursor positioned after the insertion point must move by
        # exactly the prefix length delta.
        if not visible_cursor.hasSelection() and blocks:
            new_prefix_len = len("1. ")
            prefix_delta = new_prefix_len - original_prefix_len
            new_position = original_position
            if original_position_in_block >= original_indent_len:
                new_position += prefix_delta
            current = QTextCursor(document)
            current.setPosition(max(0, min(document.characterCount() - 1, new_position)))
            self.setTextCursor(current)

    def _make_list(self, style: QTextListFormat.Style) -> None:
        cursor = self.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(style)
        current_list = cursor.currentList()
        if current_list is not None:
            list_format.setIndent(current_list.format().indent())
        else:
            list_format.setIndent(1)
        cursor.createList(list_format)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.numbered_list_mode_enabled and self._handle_numbered_list_enter():
                return
            if self.auto_checkbox_enabled and self._handle_task_enter():
                return
            if self.blank_line_after_enter:
                self._handle_spaced_enter(event)
                return

        if key == Qt.Key.Key_Tab and not (modifiers & Qt.KeyboardModifier.ControlModifier):
            if self._handle_task_indent(outdent=bool(modifiers & Qt.KeyboardModifier.ShiftModifier)):
                return

        if key == Qt.Key.Key_Backtab:
            if self._handle_task_indent(outdent=True):
                return

        super().keyPressEvent(event)

    def _handle_numbered_list_enter(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        block = cursor.block()
        match = NUMBERED_TEXT_LINE_RE.match(block.text())
        if not match:
            return False

        item_text = (match.group("text") or "").strip()
        indent = match.group("indent")
        number = int(match.group("number"))
        if not item_text:
            marker_start = block.position() + len(indent)
            remove_cursor = QTextCursor(self.document())
            remove_cursor.setPosition(marker_start)
            remove_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            remove_cursor.removeSelectedText()
            remove_cursor.setPosition(marker_start)
            self.setTextCursor(remove_cursor)
            self.numbered_list_mode_enabled = False
            self.numberedListModeChanged.emit(False)
            return True

        cursor.insertBlock()
        if self.blank_line_after_enter:
            cursor.insertBlock()
        cursor.insertText(f"{indent}{number + 1}. ")
        self.setTextCursor(cursor)
        return True

    def _handle_task_enter(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return False

        text = (match.group("text") or "").strip()
        indent = match.group("indent")
        if not text:
            marker_start = block.position() + len(indent)
            remove_cursor = QTextCursor(self.document())
            remove_cursor.setPosition(marker_start)
            remove_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            remove_cursor.removeSelectedText()
            remove_cursor.setPosition(marker_start)
            self.setTextCursor(remove_cursor)
            return True

        checked = match.group("marker") == "☑"
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertBlock()
        if self.blank_line_after_enter:
            cursor.insertBlock()
        cursor.insertText(f"{indent}☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(block, checked=checked)
        self._apply_task_style(cursor.block(), checked=False)
        reset_fmt = QTextCharFormat()
        reset_fmt.setFontStrikeOut(False)
        self.mergeCurrentCharFormat(reset_fmt)
        return True

    def _handle_spaced_enter(self, event: QKeyEvent) -> None:
        """Handle Enter as two native Enter presses, leaving one blank line."""
        super().keyPressEvent(event)
        cursor = self.textCursor()
        cursor.insertBlock()
        self.setTextCursor(cursor)

    def _handle_task_indent(self, outdent: bool) -> bool:
        cursor = self.textCursor()
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return False
        block_start = block.position()
        old_pos = cursor.position()
        leading = match.group("indent")
        edit = QTextCursor(self.document())
        if outdent:
            remove_count = min(self.tab_spaces, len(leading))
            if remove_count == 0:
                return True
            edit.setPosition(block_start)
            edit.setPosition(block_start + remove_count, QTextCursor.MoveMode.KeepAnchor)
            edit.removeSelectedText()
            cursor.setPosition(max(block_start, old_pos - remove_count))
        else:
            edit.setPosition(block_start)
            edit.insertText(" " * self.tab_spaces)
            cursor.setPosition(old_pos + self.tab_spaces)
        self.setTextCursor(cursor)
        return True

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            block = cursor.block()
            match = TASK_LINE_RE.match(block.text())
            if match:
                marker_index = len(match.group("indent"))
                relative = cursor.position() - block.position()
                if relative in {marker_index, marker_index + 1}:
                    self.toggle_checkbox(block)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu: QMenu = self.createStandardContextMenu()
        menu.addSeparator()
        add_checkbox = menu.addAction("Add / Toggle Checkbox")
        add_checkbox.triggered.connect(self.insert_checkbox)
        toggle_checked = menu.addAction("Toggle Checked")
        toggle_checked.setEnabled(bool(TASK_LINE_RE.match(self.textCursor().block().text())))
        toggle_checked.triggered.connect(self.toggle_checkbox_at_cursor)
        strike = menu.addAction("Strikethrough")
        strike.triggered.connect(self.toggle_strikethrough)
        menu.exec(event.globalPos())
````

## `app/widgets/sidebar.py`

````python
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QPushButton, QVBoxLayout, QWidget,
)

from app.models import NoteSummary, Project


class NoteCard(QWidget):
    def __init__(self, note: NoteSummary, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(7, 5, 7, 5); layout.setSpacing(2)
        title_row = QHBoxLayout(); title_row.setContentsMargins(0, 0, 0, 0)
        kind = "DEC" if note.note_kind == "decision" else "NOTE"
        badge = QLabel(kind); badge.setStyleSheet("font-size: 9px; font-weight: 700; padding: 1px 4px;")
        title = QLabel(note.title); title.setStyleSheet("font-weight: 600;")
        title_row.addWidget(badge); title_row.addWidget(title, 1)
        if note.needs_review:
            review = QLabel("⚠ REVIEW"); review.setToolTip("Linked code changed since this document was last reviewed")
            review.setStyleSheet("font-size: 9px; font-weight: 700;"); title_row.addWidget(review)
        preview = QLabel(note.preview or "No content"); preview.setWordWrap(False); preview.setStyleSheet("font-size: 11px;")
        date = QLabel(self._format_date(note.updated_at)); date.setStyleSheet("font-size: 10px;")
        layout.addLayout(title_row); layout.addWidget(preview); layout.addWidget(date)

    @staticmethod
    def _format_date(value: str) -> str:
        try: return datetime.fromisoformat(value).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError: return value


class Sidebar(QWidget):
    noteSelected = Signal(int)
    newNoteRequested = Signal()
    newDecisionRequested = Signal()
    trashRequested = Signal()
    renameRequested = Signal(int)
    duplicateRequested = Signal(int)
    deleteRequested = Signal(int)
    exportRequested = Signal(int)
    searchChanged = Signal(str)
    sortChanged = Signal(str)
    projectSelected = Signal(int)
    newProjectRequested = Signal()
    projectMenuRequested = Signal()
    scanRequested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent); self.setMinimumWidth(240); self.setMaximumWidth(560)
        root = QVBoxLayout(self); root.setContentsMargins(8, 8, 8, 8); root.setSpacing(7)

        project_label_row = QHBoxLayout(); project_label = QLabel("Project"); project_label.setStyleSheet("font-size: 11px; font-weight: 700;")
        self.project_menu_button = QPushButton("•••"); self.project_menu_button.setFixedWidth(38); self.project_menu_button.clicked.connect(self.projectMenuRequested)
        project_label_row.addWidget(project_label); project_label_row.addStretch(1); project_label_row.addWidget(self.project_menu_button)
        self.project_combo = QComboBox(); self.project_combo.setMinimumHeight(32)
        self.project_combo.currentIndexChanged.connect(self._project_changed)
        project_buttons = QHBoxLayout(); new_project = QPushButton("+ Project"); new_project.clicked.connect(self.newProjectRequested)
        scan = QPushButton("↻ Scan"); scan.setToolTip("Check linked repository changes"); scan.clicked.connect(self.scanRequested)
        project_buttons.addWidget(new_project); project_buttons.addWidget(scan)
        root.addLayout(project_label_row); root.addWidget(self.project_combo); root.addLayout(project_buttons)

        divider = QLabel("Documents"); divider.setStyleSheet("font-size: 15px; font-weight: 700; margin-top: 6px;")
        root.addWidget(divider)
        top = QHBoxLayout();
        new_note = QPushButton("+ Note"); new_note.setToolTip("New Note (Ctrl+N)"); new_note.clicked.connect(self.newNoteRequested)
        new_decision = QPushButton("+ Decision"); new_decision.clicked.connect(self.newDecisionRequested)
        top.addWidget(new_note); top.addWidget(new_decision); root.addLayout(top)

        self.search = QLineEdit(); self.search.setPlaceholderText("Search project documents…"); self.search.setClearButtonEnabled(True); self.search.textChanged.connect(self.searchChanged)
        self.sort_combo = QComboBox(); self.sort_combo.addItem("Recently edited", "updated"); self.sort_combo.addItem("Alphabetical", "title")
        self.sort_combo.currentIndexChanged.connect(lambda _i: self.sortChanged.emit(str(self.sort_combo.currentData())))
        self.list = QListWidget(); self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.list.customContextMenuRequested.connect(self._show_context_menu)
        self.list.currentItemChanged.connect(self._on_current_changed)
        trash = QPushButton("Trash"); trash.clicked.connect(self.trashRequested)
        root.addWidget(self.search); root.addWidget(self.sort_combo); root.addWidget(self.list, 1); root.addWidget(trash)

    def set_projects(self, projects: list[Project], selected_id: int | None = None) -> None:
        self.project_combo.blockSignals(True); self.project_combo.clear(); selected_index = -1
        for index, project in enumerate(projects):
            self.project_combo.addItem(project.name, project.id)
            if project.id == selected_id: selected_index = index
        if selected_index >= 0: self.project_combo.setCurrentIndex(selected_index)
        elif self.project_combo.count(): self.project_combo.setCurrentIndex(0)
        self.project_combo.blockSignals(False)

    def current_project_id(self) -> int | None:
        data = self.project_combo.currentData()
        try: return int(data) if data is not None else None
        except (TypeError, ValueError): return None

    def _project_changed(self, _index: int) -> None:
        project_id = self.current_project_id()
        if project_id is not None: self.projectSelected.emit(project_id)

    def set_notes(self, notes: list[NoteSummary], selected_id: int | None = None) -> None:
        self.list.blockSignals(True); self.list.clear(); selected_item: QListWidgetItem | None = None
        for note in notes:
            item = QListWidgetItem(); item.setData(Qt.ItemDataRole.UserRole, note.id)
            card = NoteCard(note); item.setSizeHint(card.sizeHint()); self.list.addItem(item); self.list.setItemWidget(item, card)
            if note.id == selected_id: selected_item = item
        if selected_item is not None: self.list.setCurrentItem(selected_item)
        self.list.blockSignals(False)

    def select_note(self, note_id: int) -> None:
        for index in range(self.list.count()):
            item = self.list.item(index)
            if int(item.data(Qt.ItemDataRole.UserRole)) == note_id:
                self.list.setCurrentItem(item); self.list.scrollToItem(item); return

    def _on_current_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is not None: self.noteSelected.emit(int(current.data(Qt.ItemDataRole.UserRole)))

    def _show_context_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if item is None: return
        note_id = int(item.data(Qt.ItemDataRole.UserRole)); menu = QMenu(self)
        rename = menu.addAction("Rename"); duplicate = menu.addAction("Duplicate"); export = menu.addAction("Export TXT")
        menu.addSeparator(); delete = menu.addAction("Delete to Trash"); chosen = menu.exec(self.list.mapToGlobal(pos))
        if chosen == rename: self.renameRequested.emit(note_id)
        elif chosen == duplicate: self.duplicateRequested.emit(note_id)
        elif chosen == export: self.exportRequested.emit(note_id)
        elif chosen == delete: self.deleteRequested.emit(note_id)
````

## `build.ps1`

````powershell
param(
    [switch]$SkipInstall,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

try {
    $VersionText = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
} catch {
    Fail "Python was not found. Install 64-bit Python 3.12 or newer and reopen PowerShell."
}

$Parts = $VersionText.Trim().Split('.')
if ([int]$Parts[0] -lt 3 -or ([int]$Parts[0] -eq 3 -and [int]$Parts[1] -lt 12)) {
    Fail "Python 3.12+ is required. Found $VersionText."
}

$Architecture = python -c "import platform; print(platform.architecture()[0])"
if ($Architecture.Trim() -ne "64bit") {
    Write-Host "WARNING: You are not building with 64-bit Python. For normal Windows 10/11 distribution, 64-bit Python is recommended." -ForegroundColor Yellow
}

if (-not $SkipInstall) {
    Write-Host "Installing/updating project dependencies..."
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed." }
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Fail "Dependency installation failed." }
}

python -c "import PySide6, PyInstaller; print('PySide6', PySide6.__version__, '| PyInstaller', PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) { Fail "PySide6 or PyInstaller is unavailable in the active Python environment." }

Write-Host "Running tests..."
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
if ($LASTEXITCODE -ne 0) { Fail "Tests failed. Build stopped to avoid packaging a broken release." }
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue

foreach ($Folder in @("build", "dist")) {
    if (Test-Path $Folder) {
        Write-Host "Removing old $Folder folder..."
        Remove-Item -Recurse -Force $Folder
    }
}

if ($OneFile) {
    Write-Host "Building single-file DevNest.exe with PyInstaller..."
    python -m PyInstaller --noconfirm --clean DevNest.spec -- --onefile
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller one-file build failed. Review the output above." }
    $Exe = Join-Path $ProjectRoot "dist\DevNest.exe"
} else {
    Write-Host "Building DevNest onedir package with PyInstaller..."
    python -m PyInstaller --noconfirm --clean DevNest.spec
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller onedir build failed. Review the output above." }
    $Exe = Join-Path $ProjectRoot "dist\DevNest\DevNest.exe"
}

if (-not (Test-Path $Exe)) {
    Fail "Build completed without the expected executable: $Exe"
}

Write-Host ""
Write-Host "Build successful." -ForegroundColor Green
Write-Host "Executable: $Exe"
if ($OneFile) {
    Write-Host "You can distribute dist\DevNest.exe as a single file."
} else {
    Write-Host "For maximum reliability, distribute the ENTIRE dist\DevNest folder."
}
Write-Host "User notes remain in Windows AppData, not beside the executable."
````

## `main.py`

````python
from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.constants import APP_NAME, ORGANIZATION_DOMAIN, ORGANIZATION_NAME, VERSION
from app.database import Database, DatabaseError
from app.main_window import MainWindow
from app.paths import resource_path
from app.services.logging_setup import configure_logging
from app.settings import SettingsManager
from app.themes.theme_manager import ThemeManager


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setDesktopFileName("devnest")

    icon_path = resource_path("resources/devnest.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        database = Database()
    except DatabaseError as exc:
        logger.exception("Application startup failed")
        QMessageBox.critical(None, "DevNest — Database Error", str(exc))
        return 1

    settings = SettingsManager()
    theme_manager = ThemeManager(app)
    window = MainWindow(database, settings, theme_manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
````

## `pytest.ini`

````ini
[pytest]
pythonpath = .
testpaths = tests
````

## `requirements.txt`

````text
PySide6==6.11.2
PyInstaller==6.22.2
pytest>=8.3,<10
````

## `resources/devnest.svg`

````xml
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect x="16" y="16" width="224" height="224" rx="48" fill="#273043"/>
  <path d="M68 76h120v22H68zm0 42h88v22H68zm0 42h120v22H68z" fill="#F3F5F7"/>
  <path d="M174 112l18 18-18 18" fill="none" stroke="#7AA2F7" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
````

## `tests/test_database.py`

````python
from __future__ import annotations

from pathlib import Path

from app.database import Database


def test_database_crud_and_search(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("API Plan", "<p>Hello</p>", "Hello endpoint")
        loaded = db.get_note(note.id)
        assert loaded is not None
        assert loaded.title == "API Plan"

        db.update_note(note.id, "API Plan v2", "<p>Updated</p>", "Database Redis")
        loaded = db.get_note(note.id)
        assert loaded is not None
        assert loaded.title == "API Plan v2"
        assert loaded.content_plain == "Database Redis"
        assert [item.id for item in db.list_notes("redis")] == [note.id]
    finally:
        db.close()


def test_soft_delete_restore_and_permanent_delete_cascade(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("Disposable")
        db.save_diagram(note.id, {"items": [{"id": "n1"}], "edges": [], "paths": []})

        db.soft_delete_note(note.id)
        assert db.get_note(note.id) is None
        assert db.get_note(note.id, include_deleted=True) is not None
        assert [item.id for item in db.list_trash()] == [note.id]

        db.restore_note(note.id)
        assert db.get_note(note.id) is not None
        assert db.get_diagram(note.id)["items"] == [{"id": "n1"}]

        db.soft_delete_note(note.id)
        db.permanently_delete_note(note.id)
        assert db.get_note(note.id, include_deleted=True) is None
        count = db.connection.execute("SELECT COUNT(*) FROM diagrams WHERE note_id = ?", (note.id,)).fetchone()[0]
        assert count == 0
    finally:
        db.close()


def test_duplicate_copies_diagram(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("Original", "<p>Body</p>", "Body")
        diagram = {"items": [{"type": "node", "id": "a", "x": 1, "y": 2, "text": "API"}], "edges": [], "paths": []}
        db.save_diagram(note.id, diagram)
        copy = db.duplicate_note(note.id)
        assert copy.title == "Original Copy"
        assert copy.content_html == note.content_html
        assert db.get_diagram(copy.id) == diagram
    finally:
        db.close()


def test_empty_trash_returns_deleted_count(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        a = db.create_note("A")
        b = db.create_note("B")
        db.soft_delete_note(a.id)
        db.soft_delete_note(b.id)
        assert db.empty_trash() == 2
        assert db.list_trash() == []
    finally:
        db.close()
````

## `tests/test_diagram.py`

````python
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from app.widgets.diagram_view import DiagramConnector, DiagramFreehand, DiagramScene, DiagramShape, DiagramView


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_shape_types_connections_and_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    first = scene.add_shape("square", QPointF(10, 20), "Frontend")
    second = scene.add_shape("diamond", QPointF(260, 30), "API?")
    third = scene.add_shape("ellipse", QPointF(500, 20), "Database")
    scene.add_edge(first, second)
    scene.add_edge(second, third)

    data = scene.to_data()
    shapes = [item for item in data["items"] if item["type"] == "shape"]
    assert {item["shape"] for item in shapes} == {"square", "diamond", "ellipse"}
    assert len(data["edges"]) == 2

    restored = DiagramScene()
    restored.load_data(data)
    restored_data = restored.to_data()
    assert len(restored_data["items"]) == 3
    assert len(restored_data["edges"]) == 2


def test_old_rectangle_node_data_is_backward_compatible(app: QApplication) -> None:
    scene = DiagramScene()
    scene.load_data(
        {
            "items": [{"type": "node", "id": "old", "x": 1, "y": 2, "text": "Legacy"}],
            "edges": [],
            "paths": [],
        }
    )
    shapes = [item for item in scene.items() if isinstance(item, DiagramShape)]
    assert len(shapes) == 1
    assert shapes[0].shape_type == "rect"
    assert shapes[0].text == "Legacy"


def _freehand_box(x: float, y: float, size: float = 80.0) -> QPainterPath:
    path = QPainterPath(QPointF(x, y))
    path.lineTo(x + size, y)
    path.lineTo(x + size, y + size)
    path.lineTo(x, y + size)
    path.lineTo(x, y)
    return path


def test_freehand_objects_are_connectable_and_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    first = scene.add_freehand_path(_freehand_box(10, 10))
    second = scene.add_freehand_path(_freehand_box(260, 40))

    route = QPainterPath(QPointF(90, 50))
    route.lineTo(140, 20)
    route.lineTo(210, 100)
    route.lineTo(260, 80)
    scene.add_connector_path(route, source_id=first.item_id, target_id=second.item_id)

    data = scene.to_data()
    assert data["version"] == 5
    assert len(data["paths"]) == 2
    assert all("id" in path for path in data["paths"])
    assert len(data["connectors"]) == 1
    assert data["connectors"][0]["source"] == first.item_id
    assert data["connectors"][0]["target"] == second.item_id

    restored = DiagramScene()
    restored.load_data(data)
    freehands = [item for item in restored.items() if isinstance(item, DiagramFreehand)]
    connectors = [item for item in restored.items() if isinstance(item, DiagramConnector)]
    assert len(freehands) == 2
    assert len(connectors) == 1
    assert connectors[0].source_id != connectors[0].target_id
    assert connectors[0].path().elementCount() == 4


def test_floating_connector_is_rejected(app: QApplication) -> None:
    scene = DiagramScene()
    path = QPainterPath(QPointF(10, 10))
    path.lineTo(100, 100)
    with pytest.raises(ValueError):
        scene.add_connector_path(path)


def test_freehand_connection_point_uses_drawn_contour_not_center(app: QApplication) -> None:
    scene = DiagramScene()
    freehand = scene.add_freehand_path(_freehand_box(0, 0, 100))
    point = scene._connection_point(freehand, QPointF(180, 50))
    assert point.x() == pytest.approx(100.0)
    assert point != freehand.sceneBoundingRect().center()


def test_square_is_drag_creation_tool_and_freehand_draw_is_removed(app: QApplication) -> None:
    view = DiagramView()
    assert "shape:square" in view._mode_buttons
    assert "shape:rect" not in view._mode_buttons
    assert "draw" not in view._mode_buttons
    assert "connect" in view._mode_buttons
    assert view.scene.mode == "shape:square"


def test_shape_size_persists_and_can_be_changed(app: QApplication) -> None:
    scene = DiagramScene()
    shape = scene.add_shape("ellipse", QPointF(20, 30), "Service", width=240, height=110)
    assert shape.width == pytest.approx(240.0)
    assert shape.height == pytest.approx(110.0)

    shape.set_size(310, 150)
    data = scene.to_data()
    assert data["version"] == 5
    raw = next(item for item in data["items"] if item["id"] == shape.item_id)
    assert raw["width"] == pytest.approx(310.0)
    assert raw["height"] == pytest.approx(150.0)

    restored = DiagramScene()
    restored.load_data(data)
    restored_shape = next(item for item in restored.items() if isinstance(item, DiagramShape))
    assert restored_shape.width == pytest.approx(310.0)
    assert restored_shape.height == pytest.approx(150.0)


def test_shape_preview_requires_drag_and_uses_dragged_size(app: QApplication) -> None:
    scene = DiagramScene()
    scene._begin_shape_preview("square", QPointF(10, 10))
    assert scene._finish_shape_preview(QPointF(12, 12)) is None
    assert not any(isinstance(item, DiagramShape) for item in scene.items())

    scene._begin_shape_preview("square", QPointF(20, 30))
    created = scene._finish_shape_preview(QPointF(260, 145))
    assert created is not None
    assert created.width == pytest.approx(240.0)
    assert created.height == pytest.approx(115.0)


def test_resize_from_handle_changes_shape_bounds(app: QApplication) -> None:
    scene = DiagramScene()
    shape = scene.add_shape("rounded", QPointF(100, 100), width=160, height=80)
    shape.resize_from_handle("se", QPointF(340, 250))
    assert shape.width == pytest.approx(240.0)
    assert shape.height == pytest.approx(150.0)
````

## `tests/test_editor.py`

````python
from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtWidgets")
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from app.services.txt_codec import import_text_to_html
from app.widgets.note_editor import NoteEditor


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _character_strike_out(editor: NoteEditor, position: int) -> bool:
    """Return the format of the character that starts at *position*.

    QTextCursor.charFormat() at a bare boundary position describes the cursor's
    insertion format and can reflect the character immediately before it.
    Selecting the character makes the assertion deterministic across Qt builds.
    """
    cursor = QTextCursor(editor.document())
    cursor.setPosition(position)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
    return cursor.charFormat().fontStrikeOut()


def test_checkbox_toggle_applies_and_removes_strike(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API'yi hazırla")
    block = editor.document().firstBlock()
    editor.toggle_checkbox(block)
    assert editor.toPlainText().startswith("☑")

    checked_block = editor.document().firstBlock()
    first_task_char = checked_block.position() + 2
    last_task_char = checked_block.position() + len(checked_block.text()) - 1
    assert _character_strike_out(editor, first_task_char) is True
    assert _character_strike_out(editor, last_task_char) is True

    editor.toggle_checkbox(checked_block)
    assert editor.toPlainText().startswith("☐")
    unchecked_block = editor.document().firstBlock()
    first_task_char = unchecked_block.position() + 2
    last_task_char = unchecked_block.position() + len(unchecked_block.text()) - 1
    assert _character_strike_out(editor, first_task_char) is False
    assert _character_strike_out(editor, last_task_char) is False


def test_imported_checkbox_html_stays_recognizable(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setHtml(import_text_to_html("    [x] Database\n[ ] API"))
    assert editor.toPlainText().splitlines() == ["    ☑ Database", "☐ API"]


def test_auto_checkbox_enter_continues_task(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.setPlainText("☐ Backend")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "☐ Backend\n☐ "


def test_empty_auto_checkbox_enter_exits_task_mode(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.setPlainText("☐ ")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == ""


def test_font_controls_apply_rich_text_formatting(app: QApplication) -> None:
    from PySide6.QtGui import QFont

    editor = NoteEditor()
    editor.setPlainText("format me")
    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)
    family = editor.font().family()
    editor.apply_font_family(family)
    editor.apply_font_point_size(18)
    editor.apply_font_weight(800)

    fmt = editor.textCursor().charFormat()
    assert round(fmt.fontPointSize()) == 18
    assert int(fmt.fontWeight()) == int(QFont.Weight.ExtraBold)
    assert family in fmt.font().families() or fmt.font().family() == family



def _character_format(editor: NoteEditor, position: int):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(position)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
    return cursor.charFormat()


def test_font_controls_apply_to_checkbox_marker_and_whole_task_line(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API endpoint")
    cursor = editor.textCursor()
    cursor.setPosition(len("☐ API"))
    editor.setTextCursor(cursor)

    editor.apply_font_point_size(20)
    editor.apply_font_weight(700)

    block = editor.document().firstBlock()
    marker_fmt = _character_format(editor, block.position())
    text_fmt = _character_format(editor, block.position() + 2)
    assert round(marker_fmt.fontPointSize()) == 20
    assert round(text_fmt.fontPointSize()) == 20
    assert int(marker_fmt.fontWeight()) == 700
    assert int(text_fmt.fontWeight()) == 700


def test_font_controls_apply_to_bullet_list_marker_block_format(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("Bullet item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.setTextCursor(cursor)
    editor.make_bullet_list()
    editor.apply_font_point_size(19)
    editor.apply_font_weight(700)

    block = editor.document().firstBlock()
    assert block.textList() is not None
    assert round(block.charFormat().fontPointSize()) == 19
    assert int(block.charFormat().fontWeight()) == 700
    text_fmt = _character_format(editor, block.position())
    assert round(text_fmt.fontPointSize()) == 19
    assert int(text_fmt.fontWeight()) == 700


def test_blank_line_after_enter_setting(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(False)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("First line")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "First line\n\n"


def test_blank_line_after_enter_with_auto_checkbox(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("☐ Backend")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "☐ Backend\n\n☐ "



def test_plain_text_list_mode_numbers_selected_lines_and_select_all_includes_markers(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("Alpha\nBeta\nGamma")
    editor.selectAll()
    editor.set_numbered_list_mode(True)

    expected = "1. Alpha\n2. Beta\n3. Gamma"
    assert editor.toPlainText() == expected
    block = editor.document().firstBlock()
    while block.isValid():
        assert block.textList() is None
        block = block.next()

    editor.selectAll()
    selected = editor.textCursor().selectedText().replace("\u2029", "\n")
    assert selected == expected


def test_plain_text_list_mode_enter_continues_numbering(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(False)
    editor.setPlainText("First item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    editor.set_numbered_list_mode(True)

    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "1. First item\n2. "


def test_plain_text_list_mode_works_with_double_enter(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(False)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("First item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    editor.set_numbered_list_mode(True)

    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "1. First item\n\n2. "


def test_empty_plain_text_list_item_exits_list_mode(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.setPlainText("1. ")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    editor.set_numbered_list_mode(True)

    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == ""
    assert editor.numbered_list_mode_enabled is False


def test_reenabling_list_mode_on_existing_item_keeps_its_number(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("7. Existing item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    editor.set_numbered_list_mode(True)
    assert editor.toPlainText() == "7. Existing item"


def test_inline_find_highlights_all_matches_and_advances_down(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("git one\ngit two\nGIT three")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.setTextCursor(cursor)

    editor.show_find_bar()
    editor.find_bar.set_query("git")

    ranges = editor.search_match_ranges()
    assert len(ranges) == 3
    assert len(editor.extraSelections()) == 3
    assert editor.active_search_range() is None

    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[0]
    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[1]
    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[2]
    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[0]


def test_inline_find_advances_up_and_direction_boxes_are_exclusive(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("git one\ngit two\ngit three")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    editor.show_find_bar()
    editor.find_bar.set_query("git")
    assert editor.find_bar.down_checkbox.isChecked() is True
    assert editor.find_bar.up_checkbox.isChecked() is False

    editor.find_bar.up_checkbox.click()
    assert editor.find_bar.up_checkbox.isChecked() is True
    assert editor.find_bar.down_checkbox.isChecked() is False

    ranges = editor.search_match_ranges()
    assert editor.find_search_match("up") is True
    assert editor.active_search_range() == ranges[-1]
    assert editor.find_search_match("up") is True
    assert editor.active_search_range() == ranges[-2]

    editor.find_bar.down_checkbox.click()
    assert editor.find_bar.down_checkbox.isChecked() is True
    assert editor.find_bar.up_checkbox.isChecked() is False


def test_inline_find_scrollbar_receives_one_marker_per_match(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("alpha\n" * 30 + "needle\n" + "beta\n" * 30 + "needle\n")
    editor.show_find_bar()
    editor.find_bar.set_query("needle")

    assert len(editor.search_match_ranges()) == 2
    assert len(editor._search_scrollbar._markers) == 2
    assert all(0.0 <= marker <= 1.0 for marker in editor._search_scrollbar._markers)


def test_inline_find_close_clears_highlights(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("git git")
    editor.show_find_bar()
    editor.find_bar.set_query("git")
    assert len(editor.extraSelections()) == 2

    editor.hide_find_bar()
    assert editor.is_find_bar_visible() is False
    assert editor.extraSelections() == []
    assert editor.search_match_ranges() == ()
````

## `tests/test_engineering_context.py`

````python
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

from app.database import Database
from app.services.local_git import inspect_repository, parse_github_remote
from app.services.repository_scanner import RepositoryScanner, resource_is_affected


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _init_repo(path: Path) -> None:
    path.mkdir()
    _git(path, "init")
    _git(path, "config", "user.email", "devnest@example.test")
    _git(path, "config", "user.name", "DevNest Test")
    _git(path, "remote", "add", "origin", "git@github.com:acme/backend.git")


def test_v1_database_migrates_without_losing_notes(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content_html TEXT NOT NULL DEFAULT '',
            content_plain TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE diagrams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER NOT NULL UNIQUE,
            data_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO notes(title, content_html, content_plain, created_at, updated_at, is_deleted)
        VALUES ('Legacy', '<p>kept</p>', 'kept', '2026-01-01', '2026-01-01', 0);
        PRAGMA user_version = 1;
        """
    )
    con.commit(); con.close()

    db = Database(db_path)
    try:
        note = db.get_note(1)
        assert note is not None
        assert note.title == "Legacy"
        assert note.uuid
        assert note.project_id is not None
        assert db.connection.execute("PRAGMA user_version").fetchone()[0] == Database.SCHEMA_VERSION
        assert (tmp_path / "legacy.pre-v2.backup.db").exists()
    finally:
        db.close()


def test_parse_github_remote_supports_ssh_and_https() -> None:
    assert parse_github_remote("git@github.com:acme/backend.git") == ("acme", "backend")
    assert parse_github_remote("https://github.com/acme/backend.git") == ("acme", "backend")
    assert parse_github_remote("https://gitlab.com/acme/backend.git") == (None, None)


def test_resource_scope_matching(tmp_path: Path) -> None:
    db = Database(tmp_path / "links.db")
    try:
        project = db.create_project("API")
        note = db.create_note(project_id=project.id)
        repo = db.add_repository(project.id, local_path=str(tmp_path / "repo"))
        directory = db.add_resource_link(note.id, repo.id, "directory", "src/auth", baseline_sha="a")
        file_link = db.add_resource_link(note.id, repo.id, "file", "src/db.py", baseline_sha="a")
        assert resource_is_affected(directory, ["src/auth/session.py"])
        assert not resource_is_affected(directory, ["src/other.py"])
        assert resource_is_affected(file_link, ["src/db.py"])
        assert not resource_is_affected(file_link, ["src/db.py.old"])
    finally:
        db.close()


def test_local_repository_scan_marks_link_needs_review(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    _init_repo(repo_path)
    (repo_path / "src").mkdir()
    (repo_path / "src" / "auth.py").write_text("VERSION = 1\n", encoding="utf-8")
    (repo_path / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo_path, "add", ".")
    _git(repo_path, "commit", "-m", "initial")
    info = inspect_repository(repo_path)

    db = Database(tmp_path / "devnest.db")
    try:
        project = db.create_project("Backend")
        note = db.create_note("Auth decision", project_id=project.id, note_kind="decision")
        repo = db.add_repository(
            project.id, local_path=str(info.root), github_owner=info.github_owner,
            github_repo=info.github_repo, default_branch=info.branch,
        )
        db.update_repository(repo.id, last_seen_sha=info.head_sha)
        link = db.add_resource_link(note.id, repo.id, "file", "src/auth.py", baseline_sha=info.head_sha)

        # An unrelated commit must not mark this link.
        (repo_path / "README.md").write_text("changed\n", encoding="utf-8")
        _git(repo_path, "add", "."); _git(repo_path, "commit", "-m", "docs")
        result = RepositoryScanner(db).scan_repository(repo.id)
        assert result.error is None
        assert not db.get_resource_link(link.id).needs_review  # type: ignore[union-attr]

        # A commit touching the linked file must mark it Needs Review from the original baseline.
        (repo_path / "src" / "auth.py").write_text("VERSION = 2\n", encoding="utf-8")
        _git(repo_path, "add", "."); _git(repo_path, "commit", "-m", "change auth")
        result = RepositoryScanner(db).scan_repository(repo.id)
        updated = db.get_resource_link(link.id)
        assert result.error is None
        assert updated is not None and updated.needs_review
        assert updated.change_count >= 2  # baseline spans both commits

        head = _git(repo_path, "rev-parse", "HEAD")
        db.mark_note_reviewed(note.id, repo.id, head)
        reviewed = db.get_resource_link(link.id)
        assert reviewed is not None and not reviewed.needs_review
        assert reviewed.baseline_sha == head
    finally:
        db.close()


def test_github_repository_listing_is_limited_to_app_installations(monkeypatch) -> None:
    from app.services.github_client import GitHubClient

    client = GitHubClient("Iv1.test")
    monkeypatch.setattr(client, "access_token", lambda: "token")

    def fake_request(url: str, **_kwargs):
        if url.startswith("https://api.github.com/user/installations?"):
            return {"installations": [{"id": 10}, {"id": 20}]}
        if "/user/installations/10/repositories" in url:
            return {"repositories": [{"id": 1, "full_name": "acme/backend"}]}
        if "/user/installations/20/repositories" in url:
            return {"repositories": [{"id": 2, "full_name": "me/frontend"}]}
        raise AssertionError(url)

    monkeypatch.setattr(client, "_request", fake_request)
    repos = client.list_repositories()
    assert [repo["full_name"] for repo in repos] == ["acme/backend", "me/frontend"]
    assert repos[0]["_devnest_installation_id"] == 10
    assert repos[1]["_devnest_installation_id"] == 20
````

## `tests/test_settings.py`

````python
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtCore")
from PySide6.QtCore import QSettings

from app.settings import AppPreferences, SettingsManager


def test_settings_round_trip(tmp_path: Path) -> None:
    qsettings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    manager = SettingsManager(qsettings)
    expected = AppPreferences(
        theme="dark",
        autosave_enabled=False,
        autosave_delay_ms=1200,
        start_with_last_note=False,
        editor_font_size=14,
        tab_width=2,
        auto_checkbox_default=False,
        blank_line_after_enter=True,
        word_wrap=False,
    )
    manager.save_preferences(expected)
    assert manager.preferences() == expected


def test_last_note_id_and_boolean_string_parsing(tmp_path: Path) -> None:
    qsettings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    qsettings.setValue("general/autosave_enabled", "false")
    manager = SettingsManager(qsettings)
    assert manager.preferences().autosave_enabled is False
    assert manager.last_note_id() is None
    manager.set_last_note_id(42)
    assert manager.last_note_id() == 42
    manager.set_last_note_id(None)
    assert manager.last_note_id() is None
````

## `tests/test_themes.py`

````python
from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtWidgets")

from app.themes.theme_manager import THEME_OPTIONS, THEME_SPECS


def test_theme_presets_include_multiple_dark_and_light_modes() -> None:
    values = {value for _label, value in THEME_OPTIONS}
    assert {"dark_matte", "dark_slate", "dark_graphite"} <= values
    assert {"light_clean", "light_soft", "light_warm", "light_cool"} <= values
    assert sum(1 for spec in THEME_SPECS.values() if spec.dark) >= 3
    assert sum(1 for spec in THEME_SPECS.values() if not spec.dark) >= 4
````

## `tests/test_txt_codec.py`

````python
from __future__ import annotations

from app.services.txt_codec import (
    export_internal_plain_text,
    import_text_to_html,
    parse_line,
    parse_text,
    parsed_to_internal_text,
)


def test_detects_supported_checkbox_markers() -> None:
    samples = {
        "[ ] Task": False,
        "[x] Task": True,
        "[X] Task": True,
        "☐ Task": False,
        "☑ Task": True,
        "✓ Task": True,
    }
    for source, expected_checked in samples.items():
        line = parse_line(source)
        assert line.is_task is True
        assert line.checked is expected_checked
        assert line.text == "Task"


def test_normal_text_is_not_a_task() -> None:
    line = parse_line("Bug: token refresh fails")
    assert line.is_task is False
    assert line.text == "Bug: token refresh fails"


def test_nested_indentation_is_preserved() -> None:
    lines = parse_text("[ ] Backend\n    [ ] API\n\t[x] Database")
    assert lines[0].indent == ""
    assert lines[1].indent == "    "
    assert lines[2].indent == "\t"
    internal = parsed_to_internal_text(lines)
    assert internal == "☐ Backend\n    ☐ API\n    ☑ Database"


def test_unicode_checkbox_html_marks_checked_task_as_struck() -> None:
    rendered = import_text_to_html("☐ Frontend\n☑ Login\n✓ Deploy")
    assert "☐" in rendered
    assert rendered.count("☑") == 2
    assert rendered.count("line-through") == 2


def test_export_converts_internal_checkbox_state() -> None:
    source = "☐ Login ekranı\n☑ Database bağlantısı\n    ☐ API"
    assert export_internal_plain_text(source) == "[ ] Login ekranı\n[x] Database bağlantısı\n    [ ] API"


def test_txt_round_trip_preserves_task_states_and_indentation() -> None:
    original = "[ ] Backend\n    [x] Database\nNormal açıklama\n\t[X] JWT"
    internal = parsed_to_internal_text(parse_text(original))
    exported = export_internal_plain_text(internal)
    reparsed = parse_text(exported)
    assert [(x.is_task, x.checked, x.text) for x in reparsed] == [
        (True, False, "Backend"),
        (True, True, "Database"),
        (False, False, "Normal açıklama"),
        (True, True, "JWT"),
    ]
    assert reparsed[1].indent == "    "
    assert reparsed[3].indent == "    "
````

## `tests/test_version.py`

````python
from app.constants import VERSION


def test_version_is_single_source() -> None:
    assert VERSION == "2.0.0"
````
