# Analisis Kode: *Functional Testing* dengan `WebTest`

Pada tahap ini, diperkenalkan **Functional Testing** (Pengujian Fungsional) untuk melengkapi *Unit Testing* dari materi sebelumnya. Pengujian ini memvalidasi alur kerja *end-to-end* aplikasi, dari *routing* hingga *response*.

---

## 1. Analisis Teknis dan Perubahan Struktural

Logika aplikasi inti di `tutorial/__init__.py` **tidak berubah**. Perubahan difokuskan pada penambahan *tooling* pengujian.

* **`setup.py` (Dimodifikasi):**
    * Dependensi `webtest` ditambahkan ke dalam daftar `dev_requires` (di bawah *extra* `[dev]`).
    * **Alasan Desain:** `webtest` adalah *test harness* yang mensimulasikan permintaan HTTP *full-stack* terhadap aplikasi WSGI. Seperti `pytest`, ini adalah *tooling* pengembangan, bukan dependensi *runtime* aplikasi, sehingga ditempatkan di `extras_require['dev']` untuk menjaga lingkungan produksi tetap bersih.

* **`tutorial/tests.py` (Diperluas):**
    * File ini diperluas dengan *test suite* kedua: kelas `TutorialFunctionalTests`.
    * *Unit test suite* (`TutorialViewTests`) dari materi sebelumnya tetap ada. Ini menunjukkan bahwa kedua jenis pengujian dapat hidup berdampingan dalam satu file.

---

## 2. Analisis `TutorialFunctionalTests` (Pola *Functional Test*)

Kelas baru ini mendemonstrasikan pola *functional testing* yang secara fundamental berbeda dari *unit testing*.

### 2.1. Metode `setUp(self)`

Metode *setup* ini tidak lagi membuat `DummyRequest`. Sebaliknya, ia **membangun seluruh aplikasi Pyramid**:

1.  **Impor Pabrik:** `from tutorial import main` mengimpor *application factory* (`main`) yang didefinisikan dalam `__init__.py`.
2.  **Instansiasi Aplikasi:** `app = main({})` memanggil pabrik tersebut untuk membuat *instance* lengkap dari aplikasi WSGI. Ini menginisialisasi `Configurator`, mendaftarkan rute, dan mendaftarkan *view*.
3.  **Inisialisasi `TestApp`:** `self.testapp = TestApp(app)` membungkus *instance* aplikasi WSGI (`app`) ke dalam *test harness* `webtest`. Objek `self.testapp` ini sekarang menjadi *client* simulasi untuk berinteraksi dengan aplikasi.

### 2.2. Metode `test_hello_world(self)`

Metode tes ini menunjukkan alur kerja *functional test*:

1.  **Simulasi Request:** `res = self.testapp.get('/', status=200)` adalah inti dari tes ini. Ini **mensimulasikan permintaan HTTP GET ke URL root (`/`)**. Ini tidak memanggil fungsi `hello_world` secara langsung.
2.  **Validasi *Stack*:** `WebTest` menerima permintaan ini, meneruskannya ke *router* Pyramid, yang mencocokkan rute `'/'` ke *view* `hello_world`, mengeksekusi *view* tersebut, dan menerima `Response`. Parameter `status=200` secara otomatis melakukan asersi bahwa respons HTTP adalah 200 OK.
3.  **Asersi *Body***: `self.assertIn(b'<h1>Hello World!</h1>', res.body)` memvalidasi konten dari respons. Ini membuktikan bahwa *view* yang benar telah dieksekusi dan menghasilkan HTML yang diharapkan.
    * **Catatan (b'' literal):** Asersi menggunakan *byte-string* (`b'...'`) karena `res.body` dari `WebTest` mengembalikan *raw bytes* dari respons, bukan *string* yang sudah di-decode.

---

## 3. Kontekstualisasi Arsitektur: *Unit* vs. *Functional Testing*

Tahap ini secara jelas mengilustrasikan perbedaan dan pentingnya dua lapisan pengujian:

* **Unit Test (dari Materi 5):**
    * **Fokus:** Menguji satu "unit" (fungsi `hello_world`) secara terisolasi.
    * **Metode:** Memanggil `hello_world(DummyRequest())`.
    * **Celah:** Tes ini **tidak tahu apa-apa** tentang *routing*. Jika developer secara tidak sengaja mengubah `config.add_route('hello', '/')` menjadi `config.add_route('hello', '/home')`, *unit test* akan **tetap LULUS**, meskipun aplikasi secara fungsional rusak.

* **Functional Test (Materi 6 ini):**
    * **Fokus:** Menguji integrasi *full-stack* (HTTP -> Router -> View -> Response).
    * **Metode:** Memanggil `self.testapp.get('/')`.
    * **Jaminan:** Jika developer mengubah rute ke `/home`, tes ini akan **GAGAL** (dengan 404 Not Found). Ini membuktikan bahwa konfigurasi *routing* dan *view* bekerja sama dengan benar.

Kombinasi kedua jenis tes ini memberikan jaring pengaman yang kuat: *unit test* untuk validasi logika yang cepat dan terisolasi, serta *functional test* untuk validasi integrasi *end-to-end*.

---

## 4. Evaluasi Kekuatan vs. Keterbatasan

* **Kekuatan:**
    * **Keyakinan Tinggi:** Tes fungsional memberikan keyakinan tinggi bahwa aplikasi berfungsi seperti yang diharapkan dari perspektif pengguna (HTTP).
    * **Validasi Konfigurasi:** Ini adalah satu-satunya metode (sejauh ini) yang secara aktif menguji konfigurasi *routing* dan integrasinya dengan *view*.
    * **Simulasi Cepat:** `WebTest` menyediakan simulasi *full-stack* ini **tanpa** *overhead* jaringan atau menjalankan server HTTP (`waitress`) yang sebenarnya, sehingga tetap cepat untuk dijalankan.

* **Keterbatasan:**
    * **Lebih Lambat dari Unit Test:** Meskipun cepat, `TestApp` harus menginisialisasi seluruh aplikasi (`main({})`), yang membuatnya lebih lambat daripada *unit test* yang hanya memanggil satu fungsi.
    * **Kurang Spesifik Saat Gagal:** Jika `testapp.get('/')` gagal, itu bisa jadi karena *routing* rusak (404) atau *view* rusak (500). *Unit test* lebih baik dalam menunjukkan kegagalan pada fungsi spesifik.