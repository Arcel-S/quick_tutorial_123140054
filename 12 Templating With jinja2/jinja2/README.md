# Analisis Kode: Modularitas *Templating* (Jinja2)

Pada tahap ini, didemonstrasikan salah satu filosofi inti Pyramid: **netralitas *tooling***. Ini membuktikan bahwa *templating engine* adalah komponen yang dapat diganti (*pluggable*). Aplikasi ini secara fungsional identik dengan Materi 9 (View Classes), namun *renderer* (mesin templat) diganti dari Chameleon (`.pt`) menjadi Jinja2 (`.jinja2`).

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan ini berfokus pada penggantian komponen *rendering* tanpa menyentuh logika bisnis inti.

* **`setup.py` (Dimodifikasi):**
    * Dependensi `pyramid_jinja2` ditambahkan ke dalam daftar `install_requires`. Ini adalah dependensi *runtime* baru karena aplikasi sekarang bergantung padanya untuk me-*render* templat.

* **`tutorial/__init__.py` (Dimodifikasi):**
    * Ini adalah inti dari perubahan. Panggilan `config.include('pyramid_chameleon')` (dari materi sebelumnya) **diganti** menjadi `config.include('pyramid_jinja2')`.
    * Dengan satu baris perubahan ini, *Application Factory* (`main`) sekarang mengaktifkan *renderer* Jinja2 alih-alih Chameleon.

* **`tutorial/views.py` (Dimodifikasi):**
    * Perubahan di sini minimal namun sangat penting.
    * Dekorator `@view_defaults` diubah dari `renderer='home.pt'` menjadi `renderer='home.jinja2'`.
    * Logika di dalam *method* `home()` dan `hello()` (yang mengembalikan *dictionary*) **sama sekali tidak berubah**.

* **`tutorial/home.pt` (Dihapus/Tidak Terpakai):**
    * Templat Chameleon dari materi sebelumnya tidak lagi dirujuk.

* **`tutorial/home.jinja2` (Baru):**
    * File ini menggantikan `home.pt`.
    * File ini berisi HTML yang setara, tetapi menggunakan sintaks Jinja2 (`{{ name }}`) alih-alih sintaks Chameleon (`${name}`) untuk substitusi variabel.

---

## 2. Kontekstualisasi Arsitektur: *Pluggable Renderers*

Tahap ini adalah demonstrasi sempurna dari arsitektur Pyramid yang *pluggable* dan filosofi "agnostik".

* **Pemisahan Tanggung Jawab:** Ini menegaskan pemisahan yang diperkenalkan di Materi 8.
    * **Tanggung Jawab *View***: Hanya mengembalikan `dict` (data).
    * **Tanggung Jawab *Renderer***: Mengambil `dict` itu dan mengubahnya menjadi HTML.
* **Netralitas *Framework***: Pyramid tidak peduli *bagaimana* `dict` diubah menjadi HTML, selama ada *renderer* yang terdaftar untuk ekstensi file yang ditentukan (dalam hal ini, `.jinja2`).
* **Mekanisme `config.include`:** Panggilan `config.include('pyramid_jinja2')` menjalankan kode inisialisasi dari paket `pyramid_jinja2`, yang mendaftarkan "pabrik *renderer*" baru. Pabrik ini memberi tahu Pyramid, "Jika Anda melihat *renderer* yang diakhiri dengan `.jinja2`, gunakan saya untuk menanganinya."
* **Fleksibilitas:** Sebuah aplikasi Pyramid bahkan dapat menggunakan **beberapa *renderer* secara bersamaan**. Satu *view* dapat diatur ke `renderer='page.pt'` (Chameleon) dan *view* lain diatur ke `renderer='widget.jinja2'` (Jinja2), selama kedua *add-on* tersebut di-*include*.

---

## 3. Dampak pada Pengujian (`tutorial/tests.py`)

Perubahan arsitektural ini **tidak memerlukan perubahan pada *test suite***, yang merupakan poin penting.

* **Unit Tests (`TutorialViewTests`):**
    * **Tidak ada perubahan.**
    * **Mengapa?** *Unit test* menguji *kontrak* dari *method* *view*. Kontraknya adalah "method `home()` harus mengembalikan *dictionary* yang berisi `{'name': 'Home View'}`". Karena logika *view* tidak berubah, *unit test* tetap valid dan lulus. Ini membuktikan bahwa *unit test* berhasil mengisolasi logika bisnis dari lapisan presentasi.

* **Functional Tests (`TutorialFunctionalTests`):**
    * **Tidak ada perubahan.**
    * **Mengapa?** *Functional test* adalah tes *black-box*. Tes ini memvalidasi *output* HTML akhir. Karena templat `home.pt` dan `home.jinja2` (dalam contoh sederhana ini) menghasilkan HTML yang identik secara fungsional (misalnya, keduanya mengandung `<h1>Hi Home View</h1>`), *functional test* yang ada juga tetap lulus.

**Kesimpulan Evaluasi:** Tahap ini membuktikan bahwa lapisan presentasi (template) dapat sepenuhnya ditukar tanpa memengaruhi logika bisnis (*view*) atau pengujian yang ada. Ini adalah kekuatan besar dari arsitektur Pyramid yang *decoupled* (terpisah).