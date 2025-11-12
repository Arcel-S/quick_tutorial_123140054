# Analisis Kode: Integrasi *Database* dengan SQLAlchemy

Pada tahap ini, aplikasi mengalami evolusi paling signifikan: mengganti *database* tiruan (*mock*) dalam memori (sebuah `dict` Python) dengan **database SQL** persisten yang dikelola oleh **SQLAlchemy**, sebuah *Object-Relational Mapper* (ORM).

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan ini bersifat fundamental dan menyentuh seluruh lapisan aplikasi, mulai dari konfigurasi, definisi model data, hingga logika *view*.

* **`setup.py` (Dimodifikasi):**
    * **Dependensi Baru:** `sqlalchemy`, `pyramid_tm` (Transaction Manager), dan `zope.sqlalchemy` ditambahkan ke `install_requires`.
    * **`pyramid_tm` & `zope.sqlalchemy`:** Ini adalah komponen kunci. `pyramid_tm` mengintegrasikan *transaction manager* ke dalam siklus *request* Pyramid. `zope.sqlalchemy` bertindak sebagai "lem" yang membuat sesi SQLAlchemy "sadar" akan *transaction manager* tersebut.
    * **`console_scripts` Entry Point:** Sebuah *entry point* baru ditambahkan: `'initialize_tutorial_db = tutorial.initialize_db:main'`. Ini mendaftarkan sebuah perintah *command-line* baru (`initialize_tutorial_db`) yang akan digunakan untuk membuat tabel *database*.

* **`development.ini` (Dimodifikasi):**
    * **`pyramid.includes = ... pyramid_tm`:** Mengaktifkan *tween* (middleware) *transaction manager* untuk seluruh aplikasi.
    * **`sqlalchemy.url = sqlite:///%(here)s/sqltutorial.sqlite`:** Mendefinisikan **koneksi *database***. Ini adalah praktik terbaik, karena konfigurasi *database* (lokasi, *username*, *password*) disimpan di luar kode, di file `.ini`. `%(here)s` adalah variabel yang menunjuk ke direktori yang berisi file `.ini` itu sendiri.

* **`tutorial/models.py` (Baru):**
    * File ini sekarang mendefinisikan **skema *database***.
    * **`DBSession = scoped_session(...)` dan `register(DBSession)`:** Ini adalah *boilerplate* untuk membuat *database session* global yang *thread-safe* dan mengikatnya ke *transaction manager* (`pyramid_tm` via `zope.sqlalchemy`).
    * **`Base = declarative_base()`:** Ini adalah *base class* yang akan digunakan oleh semua model ORM.
    * **`class Page(Base)`:** Ini adalah **Model ORM**. Alih-alih *mock dictionary*, `Page` sekarang adalah *class* yang memetakan ke tabel `wikipages` di *database*. Kolom (`uid`, `title`, `body`) didefinisikan secara deklaratif menggunakan `Column(...)`.

* **`tutorial/initialize_db.py` (Baru):**
    * Ini adalah **skrip *standalone*** yang berfungsi sebagai *database migrator* sederhana.
    * **Tujuan:** Skrip ini membaca `development.ini` untuk menemukan URL *database*, terhubung ke *database*, dan memanggil `Base.metadata.create_all(engine)`. Perintah ini memberi tahu SQLAlchemy untuk mengeksekusi *statement* `CREATE TABLE` untuk semua model yang mewarisi dari `Base` (yaitu, *class* `Page`).
    * **`with transaction.manager:`:** Karena skrip ini berjalan di luar *request* web Pyramid, ia tidak memiliki *transaction manager* otomatis. Blok `with` ini secara manual mengelola *commit* atau *rollback* transaksi saat menambahkan "Root page" awal.

* **`tutorial/views.py` (Modifikasi Kunci):**
    * **`pages = {...}` (Dihapus):** *Mock database* dalam memori **dihapus**.
    * **`from .models import DBSession, Page`:** *View* sekarang mengimpor *session* *database* dan model `Page`.
    * **Logika *View* Diubah Total:** Semua logika *view* sekarang menjalankan **kueri SQLAlchemy** untuk berinteraksi dengan *database* persisten:
        * **`wiki_view`:** Menggunakan `DBSession.query(Page).order_by(Page.title)` untuk mengambil semua halaman.
        * **`wikipage_add`:** Menggunakan `DBSession.add(Page(...))` untuk membuat *record* baru dan `DBSession.query(Page).filter_by(...).one()` untuk mengambil ID yang baru dibuat.
        * **`wikipage_edit`:** Menggunakan `DBSession.query(Page).filter_by(uid=uid).one()` untuk mengambil *record* yang ada, lalu memodifikasi atributnya (`page.title = ...`, `page.body = ...`).

---

## 2. Alur Eksekusi (dengan *Transaction Manager*)

Alur kerja *request-to-response* sekarang menyertakan *database* dan manajemen transaksi secara otomatis.

1.  Permintaan masuk ke `POST /add`.
2.  `pserve` -> `waitress` -> `pyramid_tm` (tween).
3.  **`pyramid_tm` memulai transaksi baru.**
4.  *Router* mencocokkan `wikipage_add` dan memanggil `WikiViews.wikipage_add`.
5.  *View* memvalidasi *form* (via `deform`). Validasi berhasil.
6.  *View* mengeksekusi `DBSession.add(Page(title='...', body='...'))`.
7.  *View* mengeksekusi `DBSession.query(...)` untuk mendapatkan ID baru.
8.  *View* mengembalikan respons `HTTPFound` (redirect).
9.  `pyramid_tm` (tween) melihat *request* berhasil (tidak ada *exception*).
10. **`pyramid_tm` secara otomatis me-*commit* transaksi.** Data baru disimpan secara permanen di file `sqltutorial.sqlite`.
11. Respons *redirect* dikirim ke *browser*.

Jika *exception* terjadi (misalnya, `validate` gagal dan tidak ditangani, atau *database* *error*), *tween* `pyramid_tm` akan **secara otomatis me-*rollback* transaksi**, mencegah data yang korup masuk ke *database*.

---

## 3. Kontekstualisasi Arsitektur: Lapisan Persistensi (ORM)

* **Abstraksi *Database* (ORM):** Ini adalah perubahan arsitektural terbesar. Aplikasi tidak lagi peduli dengan penyimpanan data; ia hanya berinteraksi dengan objek Python (`Page`). SQLAlchemy menangani penerjemahan interaksi objek (misalnya, `page.title = 'Baru'`) menjadi *statement* SQL (`UPDATE wikipages SET title='Baru' ...`).
* **Manajemen Transaksi Otomatis:** Integrasi `pyramid_tm` adalah fitur Pyramid yang sangat kuat. *View code* (logika bisnis) menjadi **sangat bersih** karena tidak perlu khawatir tentang `db.commit()` atau `db.rollback()`. *View* hanya perlu melakukan operasi data; *framework* menangani integritas transaksi.
* **Injeksi Konfigurasi:** URL *database* disuntikkan dari `.ini` ke `main` (`__init__.py`), yang kemudian mengonfigurasi *engine* SQLAlchemy. Ini sekali lagi menunjukkan filosofi *decoupling* Pyramid.
* ***Console Scripts***: Pengenalan *entry point* `console_scripts` menunjukkan bagaimana fungsionalitas terkait aplikasi (seperti inisialisasi DB) dapat dikelola sebagai bagian dari paket Python.

---

## 4. Dampak pada Pengujian (`tutorial/tests.py`)

Pengujian menjadi jauh lebih kompleks karena sekarang harus berinteraksi dengan *database* yang sebenarnya (meskipun *in-memory*).

* **`_initTestingDB()` (Helper Baru):** Fungsi *helper* ini adalah **kunci** untuk pengujian.
    * Ia membuat *engine* SQLite **in-memory** (`sqlite://`). Ini sangat cepat dan mengisolasi setiap *run* tes.
    * Ia memanggil `Base.metadata.create_all(engine)` untuk **membuat skema** di *database* *in-memory*.
    * Ia mengikat `DBSession` ke *engine* tes ini.
    * Ia menambahkan data awal ("FrontPage") sehingga *view* yang mengambil data (`GET`) dapat diuji.
* **`setUp` / `tearDown`:**
    * `setUp`: Memanggil `_initTestingDB()` untuk membuat *database* bersih untuk **setiap tes**.
    * `tearDown`: Memanggil `self.session.remove()` dan `testing.tearDown()` untuk membersihkan *database* dan konfigurasi setelah **setiap tes**, memastikan isolasi.
* **Functional Tests:** *Setup* tes fungsional diubah untuk memuat aplikasi dari `.ini` menggunakan `get_app('development.ini')`. Ini berarti tes fungsional **berjalan melawan file *database* `sqltutorial.sqlite` yang sebenarnya**, bukan *database* *in-memory*.