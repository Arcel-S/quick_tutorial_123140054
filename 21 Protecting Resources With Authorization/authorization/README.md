# Analisis Kode: Otorisasi dan Perlindungan *Resource*

Pada tahap ini, diperkenalkan lapisan keamanan kedua: **authorization** (otorisasi), atau proses menentukan "apa yang boleh Anda lakukan" setelah Anda diautentikasi. Ini menggunakan **Access Control Lists (ACLs)** untuk melindungi *view* tertentu.

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan ini mengintegrasikan *Authentication Policy* (dari materi 20) dengan *Authorization Policy* bawaan Pyramid untuk mengamankan *view*.

* **`tutorial/__init__.py` (Modifikasi Kunci):**
    * **`root_factory='tutorial.resources.Root'`:** Baris ini ditambahkan ke `Configurator`.
    * **Analisis:** Ini adalah perubahan arsitektural yang fundamental. Ini memberi tahu Pyramid bahwa untuk **setiap *request***, sebelum *routing* terjadi, ia harus terlebih dahulu membuat *instance* dari *class* `tutorial.resources.Root`. Objek ini menjadi **konteks (context)** atau *resource* *root* dari aplikasi. Sistem keamanan akan memeriksa objek ini (dan *resource* lain yang mungkin ditemukan) untuk mendapatkan ACL.

* **`tutorial/resources.py` (Baru):**
    * File ini mendefinisikan *resource* *root* yang dirujuk di `__init__.py`.
    * **`class Root:`:** *Class* ini adalah *root factory*.
    * **`__acl__ = [...]`:** Ini adalah **Access Control List (ACL)**. Ini adalah inti dari materi ini. Ini adalah daftar *tupel* yang mendefinisikan izin:
        * `(Allow, Everyone, 'view')`: Mengizinkan **siapa saja** (termasuk pengguna anonim, yang diwakili oleh `Everyone`) untuk memiliki izin `'view'`.
        * `(Allow, 'group:editors', 'edit')`: Mengizinkan **hanya pengguna** yang memiliki *principal* `'group:editors'` untuk memiliki izin `'edit'`.

* **`tutorial/security.py` (Dimodifikasi):**
    * **`GROUPS = {'editor': ['group:editors']}`:** *Database* tiruan baru ini memetakan `userid` (`'editor'`) ke daftar *principal* grup (`['group:editors']`).
    * **`effective_principals(self, request)`:** *Method* ini (bagian dari *security policy interface*) diperluas. Sekarang, jika seorang pengguna diautentikasi (misalnya, `userid` adalah `'editor'`), *method* ini akan mengembalikan daftar *principal* pengguna tersebut: `[Everyone, Authenticated, 'u:editor', 'group:editors']`.
    * **`permits(self, ...)`:** *Method* ini (bagian dari *security policy interface*) dipanggil oleh Pyramid untuk memeriksa izin. Ia mengambil *principal* efektif pengguna (dari `effective_principals`) dan ACL dari *resource* saat ini (`context.__acl__`), dan menentukan apakah pengguna diizinkan (`True`) atau ditolak (`False`) untuk `permission` yang diminta.

* **`tutorial/views.py` (Modifikasi Kunci):**
    * **`@view_config(route_name='hello', permission='edit')`:** Dekorator untuk *view* `hello` sekarang memiliki argumen `permission='edit'`.
    * **Analisis:** Ini memberi tahu Pyramid bahwa sebelum mengeksekusi *view* `hello`, ia **harus** memeriksa *security policy* (yang kita definisikan di `security.py`) untuk melihat apakah pengguna saat ini memiliki izin `'edit'` pada *resource* yang ditemukan.
    * **`@forbidden_view_config(renderer='login.pt')`:** Dekorator **baru** ini ditambahkan ke *view* `login`.
    * **Analisis:** Ini mengkonfigurasi **Forbidden View**. Jika Pyramid menolak akses ke *view* (seperti `hello` karena izin `'edit'` tidak ada), ia akan mencari dan mengeksekusi *forbidden view* sebagai gantinya. Dalam hal ini, ia akan me-*render* `login.pt`, yang secara efektif mengarahkan pengguna yang tidak sah ke halaman *login*.

---

## 2. Alur Eksekusi (*Request* yang Dilindungi)

Alur kerja keamanan sekarang lengkap, menggabungkan autentikasi dan otorisasi.

1.  **Permintaan `GET /howdy` (Pengguna Anonim):**
    1.  `pserve` -> `waitress` -> Pyramid.
    2.  *Root factory* (`Root`) dipanggil, membuat *instance* `Root` sebagai `context` awal.
    3.  *Router* mencocokkan rute `hello`.
    4.  Pyramid melihat *view* `hello` memerlukan `permission='edit'`.
    5.  Pyramid memanggil `security_policy.permits(request, context, 'edit')`.
    6.  Di dalam `permits`, `effective_principals` dipanggil. Pengguna anonim, sehingga mengembalikan `[Everyone]`.
    7.  `permits` memeriksa ACL pada `context` (`Root.__acl__`).
    8.  ACL: `(Allow, Everyone, 'view')` (tidak cocok), `(Allow, 'group:editors', 'edit')` (tidak cocok).
    9.  Tidak ada izin yang cocok. `permits` mengembalikan `False`.
    10. Pyramid menolak akses, menghasilkan **HTTP 403 Forbidden**.
    11. Pyramid menangkap 403 ini, mencari `@forbidden_view_config`, dan menemukan *view* `login`.
    12. *View* `login` dieksekusi, me-*render* `login.pt`. Pengguna melihat halaman *login*.

2.  **Pengguna *Login* sebagai 'editor' (password 'editor'):**
    1.  `POST /login` -> *View* `login` memvalidasi, memanggil `remember(request, 'editor')`, dan me-*redirect* kembali ke `/howdy` (via `came_from`).

3.  **Permintaan `GET /howdy` (Pengguna 'editor'):**
    1.  `GET /howdy` (sekarang dengan *cookie* autentikasi).
    2.  *Root factory* (`Root`) dipanggil (`context`).
    3.  *Router* mencocokkan rute `hello`.
    4.  Pyramid melihat `permission='edit'`.
    5.  Pyramid memanggil `security_policy.permits(request, context, 'edit')`.
    6.  Di dalam `permits`, `effective_principals` dipanggil. *Cookie* divalidasi, `userid` adalah `'editor'`. *Method* mengembalikan `[Everyone, Authenticated, 'u:editor', 'group:editors']`.
    7.  `permits` memeriksa ACL pada `context` (`Root.__acl__`).
    8.  ACL: `(Allow, 'group:editors', 'edit')`. Ini **cocok**, karena pengguna *adalah* anggota `'group:editors'`.
    9.  `permits` mengembalikan `True`.
    10. Izin diberikan.
    11. *View* `hello` yang sebenarnya dieksekusi, me-*render* `hello.pt`. Pengguna melihat halaman `hello`.

---

## 3. Kontekstualisasi Arsitektur: Keamanan Berbasis *Resource*

* **Authn vs. Authz:** Materi ini secara jelas memisahkan **Authentication** (AuthN - *Siapa Anda?* - ditangani oleh `identity` dan `authenticated_userid`) dari **Authorization** (AuthZ - *Apa yang boleh Anda lakukan?* - ditangani oleh `permits` dan ACL).
* **ACL dan *Resource***: Filosofi keamanan Pyramid **berbasis *resource***. Izin tidak global; izin terikat pada *resource* (objek `context`). `Root` memiliki ACL-nya sendiri. Jika kita memiliki *resource* `Page` (dari materi 19), setiap objek `Page` dapat memiliki ACL-nya sendiri (misalnya, beberapa halaman bersifat publik, beberapa bersifat pribadi).
* ***Principals***: Sistem ini tidak mengikat izin ke *username*. Izin terikat pada *principal* (seperti `'group:editors'`). `SecurityPolicy` kemudian bertanggung jawab untuk memetakan `userid` (`'editor'`) ke *principal* tersebut. Ini adalah abstraksi yang kuat yang memisahkan "peran" (`editors`) dari "identitas" (`editor`).
* ***Forbidden View***: Menggunakan `@forbidden_view_config` adalah pola standar di Pyramid. Ini memberikan satu titik masuk untuk menangani semua penolakan izin, yang biasanya berarti menampilkan halaman *login* (jika anonim) atau halaman "Akses Ditolak" (jika *login* tapi tidak punya izin).
