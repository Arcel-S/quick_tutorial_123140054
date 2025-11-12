# Analisis Kode: Abstraksi HTML dengan *Templating*

Pada Templating, terjadi perubahan arsitektural yang fundamental dalam cara aplikasi menghasilkan respons. *Hard-coded* HTML di dalam logika *view* (Python) dihilangkan dan digantikan oleh sistem *templating* eksternal.

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan ini menyentuh hampir setiap bagian dari aplikasi, dari dependensi hingga logika *view* dan pengujian.

* **`setup.py` (Dimodifikasi):**
    * Dependensi `pyramid_chameleon` ditambahkan ke dalam daftar `install_requires` (inti).
    * **Alasan Desain:** Berbeda dengan `pytest` atau `debugtoolbar`, *templating engine* adalah dependensi **runtime**. Aplikasi tidak dapat berjalan tanpanya, sehingga ia harus berada di `install_requires`, bukan `extras_require['dev']`.

* **`tutorial/__init__.py` (Dimodifikasi):**
    * Baris baru `config.include('pyramid_chameleon')` ditambahkan.
    * **Alasan Desain:** Ini adalah panggilan **imperatif** yang "mengaktifkan" *add-on* *templating*. Panggilan ini memberi tahu Pyramid untuk mengenali *renderer* `.pt` (Chameleon) dan bagaimana cara menanganinya. Ini menunjukkan arsitektur Pyramid yang *pluggable* untuk komponen-komponen inti.

* **`tutorial/views.py` (Sangat Dimodifikasi):**
    * **`from pyramid.response import Response` dihapus.** *View* tidak lagi bertanggung jawab membuat objek `Response`.
    * **`@view_config(..., renderer='home.pt')`:** Argumen `renderer` ditambahkan ke dekorator. Ini adalah **koneksi kunci**. Ini memberi tahu Pyramid bahwa *output* dari fungsi ini tidak boleh dikembalikan langsung ke klien. Sebaliknya, *output* tersebut harus digunakan sebagai *konteks* untuk me-*render* templat `home.pt`.
    * **`return {'name': 'Home View'}`:** Ini adalah perubahan paling signifikan. *View* sekarang hanya mengembalikan **Python dictionary** (data). Tanggung jawab *view* telah berubah dari "membuat halaman HTML" menjadi "menyiapkan data untuk halaman".

* **`tutorial/home.pt` (Baru):**
    * Ini adalah file templat (Chameleon). Ini adalah file HTML murni dengan sintaks minimal (`${name}`) untuk substitusi variabel.
    * **Alasan Desain:** Ini adalah perwujudan sejati dari **Separation of Concerns (SoC)**. Desainer *frontend* sekarang dapat mengedit file `.pt` ini (HTML, CSS) tanpa menyentuh logika bisnis di `views.py`. Sebaliknya, *backend developer* dapat mengubah logika di `views.py` tanpa merusak HTML.

* **`development.ini` (Dimodifikasi):**
    * `pyramid.reload_templates = true` ditambahkan. Ini adalah pengaturan *quality-of-life* untuk pengembangan, yang memerintahkan Pyramid untuk me-*reload* file templat (`.pt`) jika berubah, tanpa perlu me-restart server `pserve`.

---

## 2. Alur Eksekusi Baru (dengan *Renderer*)

Alur kerja untuk satu permintaan kini telah berubah:

1.  Permintaan HTTP masuk ke `GET /`.
2.  `pserve` -> `waitress` -> `pyramid` router.
3.  Router mencocokkan rute `home` (URL `/`).
4.  Pyramid melihat *view* yang dikonfigurasi untuk rute `home` memiliki `renderer='home.pt'`.
5.  Pyramid **memanggil** fungsi *view* `home(request)`.
6.  Fungsi `home` dieksekusi dan **mengembalikan sebuah *dictionary*:** `{'name': 'Home View'}`.
7.  Pyramid **mencegat** *dictionary* ini.
8.  Pyramid memuat templat `home.pt` dan meneruskan *dictionary* tersebut sebagai *konteks* *rendering*.
9.  *Templating engine* (Chameleon) menggantikan `${name}` dengan `'Home View'`.
10. Pyramid mengambil HTML yang sudah di-*render*, secara otomatis membungkusnya dalam objek `Response` (dengan `status_code` 200 dan `content_type` `text/html`), dan mengirimkannya ke *browser*.

---

## 3. Kontekstualisasi Arsitektur: Pergeseran Tanggung Jawab

Tahap ini secara formal memisahkan **logika bisnis** dari **presentasi**.

* **Sebelumnya (Materi 7):**
    * `View` = Bertanggung jawab atas logika **DAN** presentasi (HTML).
    * `View` mengembalikan `Response` (HTML *string*).
* **Sekarang (Materi 8):**
    * `View` = Hanya bertanggung jawab atas **logika** (mengumpulkan data).
    * `View` mengembalikan `dict` (data/konteks).
    * `Renderer` (Chameleon) = Bertanggung jawab atas **presentasi** (HTML).

Arsitektur ini jauh lebih bersih dan merupakan pola standar di hampir semua *framework* web modern (MVC, MVT, dll.).

---

## 4. Dampak pada Pengujian (`tutorial/tests.py`)

Perubahan arsitektur ini juga berdampak langsung pada strategi pengujian:

* **Unit Tests (`TutorialViewTests`):**
    * Tes ini **tidak lagi** memeriksa `response.status_code` atau `response.body`.
    * Tes ini sekarang **menguji kontrak data *view***.
    * `response = home(request)` sekarang mengembalikan *dictionary*.
    * Asersi diubah menjadi `self.assertEqual('Home View', response['name'])`. Ini memvalidasi bahwa *view* menghasilkan data yang benar.

* **Functional Tests (`TutorialFunctionalTests`):**
    * Tes ini **tidak berubah** secara filosofis. Tes ini masih memanggil `self.testapp.get('/')`.
    * Tes ini **masih memeriksa HTML** (`self.assertIn(b'<h1>Hi Home View', res.body)`).
    * **Peran Kunci:** *Functional test* sekarang menjadi **satu-satunya** tes yang memvalidasi bahwa *view* (data) dan *template* (HTML) telah **terintegrasi dengan benar** dan menghasilkan *output* HTML akhir yang diharapkan.