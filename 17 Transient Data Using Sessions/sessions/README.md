# Analisis Kode: Persistensi Data Transien dengan *Sessions*

Pada tahap ini, diperkenalkan konsep **session** (sesi), sebuah mekanisme fundamental untuk menyimpan data yang terkait dengan pengguna spesifik di antara beberapa *request*. Ini adalah langkah pertama menuju aplikasi *stateful* (misalnya, *login*, keranjang belanja).

-----

## 1\. Analisis Teknis dan Perubahan Struktural

Perubahan ini melibatkan konfigurasi "pabrik sesi" (*session factory*) di `__init__.py` dan penggunaan objek `session` baru di dalam *view*.

  * **`tutorial/__init__.py` (Modifikasi Kunci):**

      * **`from pyramid.session import SignedCookieSessionFactory`:** Mengimpor implementasi sesi *default* (bawaan) Pyramid.
      * **`my_session_factory = SignedCookieSessionFactory(...)`:** Sebuah *session factory* dibuat.
          * **`'itsaseekreet'`:** Ini adalah **kunci rahasia (secret key)**. *Factory* ini bekerja dengan menyimpan *semua* data sesi di dalam *cookie* di *browser* klien. Kunci rahasia ini digunakan untuk **menandatangani (sign)** *cookie* tersebut secara kriptografis, untuk mencegah pengguna memalsukan atau mengubah data sesi mereka.
      * **`config = Configurator(..., session_factory=my_session_factory)`:** *Factory* yang baru dibuat disuntikkan ke dalam `Configurator` Pyramid saat inisialisasi. Ini adalah cara Pyramid mengaktifkan sistem sesi.

  * **`tutorial/views.py` (Dimodifikasi):**

      * **`@property def counter(self):`:** Sebuah *property* baru ditambahkan ke *view class*. Ini adalah logika inti dari materi ini.
      * **`session = self.request.session`:** Setelah *session factory* dikonfigurasi, objek `request` secara otomatis memiliki atribut `session`. Objek ini berperilaku seperti *dictionary* Python biasa.
      * **Logika Counter:** Kode di dalam *property* `counter` memeriksa apakah kunci `'counter'` sudah ada di sesi. Jika ya, nilainya ditambah satu. Jika tidak, nilainya diinisialisasi ke 1.
      * **Pola *Get-or-Create*:** Ini adalah pola *stateful* yang umum: membaca data dari sesi, memodifikasinya, dan menyimpannya kembali. Pyramid menangani penyimpanan data sesi ke *cookie* secara otomatis di akhir *request*.

  * **`tutorial/home.pt` (Dimodifikasi):**

      * Templat diperbarui untuk menampilkan *counter* baru:
        ```html
        <p>Count: ${view.counter}</p>
        ```
      * **`view.counter`:** Ini memanggil *property* `counter` pada *instance* `TutorialViews` (yang disuntikkan sebagai `view`), yang pada gilirannya memicu logika untuk mengambil dan menambah nilai *counter* di dalam sesi.

-----

## 2\. Alur Eksekusi (dengan *Session*)

1.  **Request Pertama (dari *Browser* Baru):**

      * `GET /` -\> Rute `home` -\> `TutorialViews.home` dipanggil.
      * Templat `home.pt` di-*render*.
      * `view.counter` diakses.
      * `self.request.session` diakses. Karena ini *request* baru, *cookie* sesi belum ada. `SignedCookieSessionFactory` membuat *dictionary* sesi baru yang kosong.
      * `'counter' in session` bernilai `False`.
      * `session['counter'] = 1` ditetapkan.
      * *Property* mengembalikan `1`. HTML `Count: 1` di-*render*.
      * **Pada akhir *request***, Pyramid mengambil *dictionary* `session` (`{'counter': 1}`), men-serialisasikannya, menandatanganinya dengan `'itsaseekreet'`, dan mengirimkannya ke *browser* sebagai *header* `Set-Cookie`.

2.  **Request Kedua (dari *Browser* yang Sama):**

      * `GET /howdy` -\> Rute `hello` -\> `TutorialViews.hello` dipanggil.
      * Templat `home.pt` di-*render* (karena `@view_defaults`).
      * `view.counter` diakses.
      * `self.request.session` diakses. Kali ini, *browser* mengirimkan *cookie* sesi dari *request* sebelumnya.
      * Pyramid membaca *cookie*, memverifikasi tanda tangannya (menggunakan `'itsaseekreet'`), dan men-deserialisasi datanya menjadi `session = {'counter': 1}`.
      * `'counter' in session` bernilai `True`.
      * `session['counter'] += 1` (sekarang menjadi 2).
      * *Property* mengembalikan `2`. HTML `Count: 2` di-*render*.
      * **Pada akhir *request***, Pyramid melihat `session` telah dimodifikasi. Ia membuat *cookie* baru dengan data `{'counter': 2}`, menandatanganinya, dan mengirimkannya ke *browser* (menimpa *cookie* lama).

-----

## 3\. Kontekstualisasi Arsitektur: *Stateful* vs. *Stateless*

HTTP pada dasarnya *stateless* (setiap *request* adalah independen). *Session* adalah mekanisme untuk menciptakan ilusi *state* (keadaan) yang persisten untuk pengguna.

  * **Pabrik Sesi (*Session Factory*):** Ini adalah implementasi dari **Pola Pabrik (Factory Pattern)**. `Configurator` tidak tahu *bagaimana* sesi bekerja; ia hanya tahu bahwa ia memiliki "pabrik" yang dapat dipanggil untuk *membuat* objek sesi untuk setiap *request*.
  * ***Backend* Sesi:**
      * **`SignedCookieSessionFactory` (Contoh ini):** Seluruh data disimpan di *cookie* klien.
          * **Pro:** Sangat cepat, tidak memerlukan *database* di sisi server. Sepenuhnya *stateless* di sisi *server*.
          * **Kontra:** Tidak aman untuk data sensitif (data di-*sign*, tapi **tidak dienkripsi**), memiliki batas ukuran (sekitar 4KB).
      * **Sesi Sisi Server (misalnya, `pyramid_redis_sessions`):** Hanya ID unik yang disimpan di *cookie* klien. Data sebenarnya (`{'counter': 2}`) disimpan di *database* server (seperti Redis).
          * **Pro:** Aman untuk data sensitif, tidak ada batasan ukuran.
          * **Kontra:** Memerlukan *lookup* *database* pada setiap *request*, menambah *overhead*.

-----

## 4\. Dampak pada Pengujian (`tutorial/tests.py`)

  * **Tidak ada perubahan pada tes.**
  * **Mengapa?**
      * **Unit Tests:** `testing.DummyRequest()` *tidak* memiliki *session factory* yang terkonfigurasi, sehingga `request.session` akan gagal. Namun, *unit test* yang ada **tidak menguji *property* `counter`**. Mereka hanya menguji *method* `home` dan `hello`. Karena *method* tersebut tidak berubah (mereka masih mengembalikan *dict*), tes yang ada tetap lulus. Untuk menguji *property* `counter` secara unit, `DummyRequest` perlu dibuat dengan *session factory* tiruan, yang lebih rumit.
      * **Functional Tests:** `TestApp` **tidak** secara *default* mempertahankan *cookie* di antara *request*. Setiap panggilan `.get()` adalah *request* baru yang terisolasi tanpa *cookie* sebelumnya. Oleh karena itu, *functional test* yang ada (yang tidak memeriksa *counter*) tetap lulus. Untuk menguji *counter*, *functional test* perlu diperbarui untuk memeriksa `Count: 1` pada setiap panggilan, atau `TestApp` harus dikonfigurasi untuk mengelola *cookie*.
