# Analisis Kode: Autentikasi Pengguna (Login/Logout)

Pada tahap ini, diperkenalkan lapisan **keamanan (security)** fundamental pertama: **authentication** (autentikasi), atau proses verifikasi "siapa Anda". Ini adalah fondasi untuk membedakan antara pengguna anonim dan pengguna yang sudah *login*.

---

## 1. Analisis Teknis dan Perubahan Struktural

Implementasi ini memerlukan penambahan beberapa komponen kunci yang bekerja bersama:

* **`setup.py` (Dimodifikasi):**
    * Dependensi `bcrypt` ditambahkan. Ini adalah *library* **runtime** yang penting untuk *password hashing*.
    * **Alasan Desain:** Ini adalah praktik keamanan standar. *Password* tidak pernah disimpan sebagai teks biasa. `bcrypt` adalah algoritma *hashing* *one-way* yang kuat dan lambat (yang merupakan fitur) untuk *hashing* *salt* pada *password*.

* **`development.ini` (Dimodifikasi):**
    * Sebuah kunci baru ditambahkan: `tutorial.secret = 98zd`.
    * **Alasan Desain:** Kunci rahasia ini digunakan untuk **menandatangani (sign) *cookie* autentikasi** secara kriptografis. Dengan menyimpannya di `.ini` (bukan di kode), rahasia ini dapat dengan mudah diubah untuk lingkungan produksi tanpa menyentuh kode aplikasi.

* **`tutorial/security.py` (Baru):**
    * Ini adalah modul baru yang mendefinisikan **lapisan autentikasi**.
    * **`USERS = {...}`:** Ini adalah *database* pengguna tiruan (*mock*) dalam memori. Dalam aplikasi nyata, ini akan menjadi kueri ke *database* (misalnya, tabel `User` di SQLAlchemy).
    * **`check_password(pw, hashed_pw)`:** Fungsi *helper* yang menggunakan `bcrypt` untuk membandingkan *password* yang dikirimkan dengan *hash* yang disimpan.
    * **`class SecurityPolicy`:** Ini adalah inti dari implementasi.
        * **`__init__(self, secret)`:** *Constructor* ini mengambil `tutorial.secret` dari `.ini` dan menggunakannya untuk menginisialisasi `AuthTktCookieHelper`.
        * **`AuthTktCookieHelper`:** Ini adalah **mekanisme** autentikasi yang dipilih. Ini mengelola *state* autentikasi dengan membuat dan membaca *cookie* yang ditandatangani (`AuthTkt`).
        * **`identity(self, request)` dan `authenticated_userid(self, request)`:** Ini adalah *method* yang diperlukan oleh *interface* kebijakan Pyramid. Mereka dipanggil di **setiap *request*** untuk memeriksa *cookie* yang masuk, memvalidasinya, dan mengembalikan identitas pengguna (jika ada).
        * **`remember(self, ...)` dan `forget(self, ...)`:** Ini adalah *method* yang menghasilkan *header* HTTP (`Set-Cookie`) yang diperlukan untuk **mengatur** (saat *login*) atau **menghapus** (saat *logout*) *cookie* autentikasi.

* **`tutorial/__init__.py` (Modifikasi Kunci):**
    * Mengimpor `SecurityPolicy` yang baru.
    * Membaca `tutorial.secret` dari `settings`.
    * **`config.set_security_policy(SecurityPolicy(...))`:** Ini adalah **aktivasi** utama. Ini memberi tahu Pyramid untuk menggunakan *class* `SecurityPolicy` kustom kita sebagai *Authentication Policy* di seluruh aplikasi.
    * Menambahkan rute baru untuk `/login` dan `/logout`.

* **`tutorial/views.py` (Dimodifikasi):**
    * **`__init__(self, request)`:** *Constructor* *view* sekarang memeriksa `request.authenticated_userid` (sebuah atribut yang disediakan oleh Pyramid setelah *policy* diatur) dan menyimpannya di `self.logged_in`.
    * **`login(self)` (View Baru):**
        * Ini adalah *view* *form* *self-posting* (seperti di materi `deform`).
        * Jika `GET`, ia hanya me-*render* `login.pt`.
        * Jika `POST`, ia mengambil `login` dan `password` dari `request.params`, memvalidasinya menggunakan `check_password`.
        * **Saat Sukses:** Ia memanggil `remember(request, login)`. Ini adalah API Pyramid tingkat tinggi yang memanggil *method* `remember` pada *policy* kita yang terdaftar, mendapatkan *header* `Set-Cookie`, dan menyertakannya dalam respons `HTTPFound`.
    * **`logout(self)` (View Baru):**
        * Memanggil `forget(request)` untuk mendapatkan *header* yang menghapus *cookie*.
        * Mengembalikan `HTTPFound` (redirect) ke halaman `home` dengan *header* tersebut.

* **`tutorial/home.pt` dan `login.pt` (Dimodifikasi/Baru):**
    * **`view.logged_in`:** Templat sekarang dapat mengakses *flag* `view.logged_in` (ditetapkan di `__init__` *view*).
    * **Render Bersyarat:** Templat `home.pt` menggunakan `tal:condition="view.logged_in is None"` untuk secara dinamis menampilkan tautan "Log In" atau "Logout".

---

## 2. Filosofi Konfigurasi: Kebijakan (Policy) vs. Mekanisme

Tahap ini mengilustrasikan pemisahan yang jelas dalam arsitektur keamanan Pyramid:

* **Kebijakan (Policy):** *Class* `SecurityPolicy` adalah "Kebijakan". Ini mendefinisikan *apa* artinya *login* dalam aplikasi kita (yaitu, ada di `USERS`) dan *method* apa yang digunakan (`identity`, `remember`, `forget`).
* **Mekanisme:** `AuthTktCookieHelper` adalah "Mekanisme". Ini adalah *bagaimana* kebijakan tersebut diterapkan (yaitu, dengan *cookie* yang ditandatangani).

Arsitektur Pyramid bersifat *pluggable*. Kita bisa saja mengganti `AuthTktCookieHelper` dengan *session factory* (dari Materi 17) atau *handler* JWT (*JSON Web Token*) tanpa mengubah logika *view* `login` / `logout` kita. *View* hanya perlu memanggil API tingkat tinggi `remember` dan `forget`, dan *policy* yang terdaftar akan menangani sisanya.

---

## 3. Kontekstualisasi Arsitektur dan Skalabilitas

* **Pemisahan Tanggung Jawab (SoC):** Konfigurasi keamanan (`__init__.py`), logika keamanan (`security.py`), dan logika *view* (`views.py`) sekarang berada di file terpisah, yang sangat baik untuk pemeliharaan.
* **Agnostik *Storage***: `SecurityPolicy` mengabstraksi *backend* pengguna. Saat ini ia menggunakan `dict` `USERS`. Untuk skalabilitas, ini akan diubah untuk mengkueri *database* SQLAlchemy (`DBSession.query(User).filter_by...`). Logika *view* (`login`, `logout`) tidak perlu tahu atau peduli—mereka hanya berinteraksi dengan *policy*.
* ***State* dalam *View* dan Templat:** Pola `self.logged_in = request.authenticated_userid` di `__init__` *view class* adalah cara yang efisien untuk membuat *state* autentikasi tersedia untuk semua *method* *view* dan templat mereka (melalui variabel `view`).

---

## 4. Dampak pada Pengujian (Implisit)

* **Tes Unit yang Ada:** Tes unit untuk `home` dan `hello` yang ada (dari materi `view_classes`) akan **tetap lulus**. *Method* tersebut masih mengembalikan `dict` yang sama; penambahan `self.logged_in` tidak mengubah kontrak *output* mereka.
* **Tes Fungsional Baru (Diperlukan):** Ini adalah satu-satunya cara untuk memvalidasi alur kerja *login*/*logout* secara *end-to-end*. *Test suite* fungsional perlu diperluas untuk:
    1.  Memverifikasi halaman `home` menampilkan "Log In".
    2.  Mem-POST ke `/login` dengan kredensial buruk dan memverifikasi *form* di-*render* ulang dengan pesan *error*.
    3.  Mem-POST ke `/login` dengan kredensial baik (`editor`/`editor`).
    4.  Memverifikasi responsnya adalah `302 Redirect`.
    5.  Mengikuti *redirect* dan memverifikasi halaman `home` (atau halaman `came_from`) sekarang menampilkan "Logout".
    6.  Mengklik `/logout` dan memverifikasi *redirect* kembali ke `home` dengan "Log In" ditampilkan lagi.
