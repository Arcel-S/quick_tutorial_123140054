# Analisis Kode: Pengenalan *Unit Testing* dengan `pytest`

Analisis berfokus pada penambahan infrastruktur *testing* (pengujian) ke dalam proyek. Ini adalah langkah penting dalam siklus hidup pengembangan perangkat lunak untuk memastikan kualitas dan stabilitas kode.

-----

## 1\. Analisis Teknis dan Perubahan Struktural

Logika aplikasi inti di `tutorial/__init__.py` **tidak berubah**. Perubahan difokuskan pada penambahan konfigurasi pengujian dan sebuah modul tes baru.

  * **`setup.py` (Dimodifikasi):**

      * Dependensi `pytest` ditambahkan ke dalam daftar `dev_requires` di bawah *extra* `[dev]`.
      * **Alasan Desain:** Ini melanjutkan filosofi **Pemisahan Dependensi Lingkungan**. `pytest` adalah *test runner*, sebuah alat bantu pengembangan, bukan dependensi *runtime* aplikasi. Memisahkannya ke `[dev]` memastikan *tooling* pengujian tidak di-instal di server produksi, yang menghemat sumber daya dan mengurangi *attack surface*.

  * **`tutorial/tests.py` (Baru):**

      * Ini adalah modul baru yang berisi *test suite* untuk paket `tutorial`.
      * Modul ini menggunakan kombinasi dari pustaka `unittest` (standar Python) untuk struktur (`TestCase`, `setUp`, `tearDown`, `assertEqual`) dan `pyramid.testing` untuk *helpers* spesifik Pyramid.

  * **Alur Eksekusi Pengujian:**

      * Sebuah alur kerja baru diperkenalkan, terpisah dari `pserve`:
        ```bash
        $VENV/bin/pytest tutorial/tests.py -q
        ```
      * Perintah ini menginstruksikan *test runner* `pytest` untuk menemukan semua tes di dalam file `tutorial/tests.py`, menjalankannya, dan melaporkan hasilnya.

-----

## 2\. Analisis `tutorial/tests.py` (Pola *Unit Test* Pyramid)

File ini mendemonstrasikan pola dasar untuk *unit testing* sebuah *view* Pyramid.

  * **`import unittest` vs `pyramid.testing`:**

      * `unittest.TestCase` menyediakan kerangka kerja dasar pengujian (struktur kelas, *assertions*, *setup/teardown*).
      * `pyramid.testing` menyediakan *helper* vital untuk mengisolasi komponen Pyramid.

  * **`setUp(self)` dan `tearDown(self)`:**

      * `testing.setUp()` (dan `tearDown()`) adalah *helper* yang menyiapkan dan membersihkan lingkungan Pyramid minimal untuk pengujian. Ini menciptakan *request* tiruan (mock) dan *registry* konfigurasi minimal. Ini sangat penting untuk menguji kode yang bergantung pada infrastruktur Pyramid (misalnya, `request.registry.settings`).

  * **Analisis `test_hello_world(self)`:**

    1.  **Isolasi Impor:** `from tutorial import hello_world` diimpor *di dalam* metode tes. Ini adalah praktik *unit testing* yang disengaja untuk memastikan setiap tes berjalan dalam isolasi maksimum dan untuk menghindari *side-effect* di level modul yang dapat mencemari tes lain.
    2.  **`testing.DummyRequest()`:** Ini adalah **konsep kunci**. Alih-alih menjalankan server dan membuat permintaan HTTP nyata, kita membuat *instance* objek `DummyRequest` (sebuah *mock* atau *test double*). Objek ini mensimulasikan `request` yang dibutuhkan oleh *view* `hello_world`.
    3.  **Eksekusi Langsung:** *View* (`hello_world`) dipanggil **sebagai fungsi Python biasa**, dengan `DummyRequest` yang disuntikkan sebagai argumennya: `response = hello_world(request)`.
    4.  **Asersi:** Tes memverifikasi *kontrak* dari fungsi tersebut. Dalam hal ini, kontraknya adalah "fungsi ini harus mengembalikan objek `Response` dengan `status_code` 200 OK".

-----

## 3\. Kontekstualisasi Arsitektur: *Unit* vs. *Functional Testing*

Materi ini secara spesifik memperkenalkan **Unit Testing**, yang memiliki perbedaan fundamental dari *Functional Testing*.

  * **Unit Testing (Contoh Ini):**

      * **Fokus:** Menguji satu "unit" (fungsi `hello_world`) secara terisolasi.
      * **Metode:** Memanggil fungsi secara langsung dengan objek tiruan (`DummyRequest`).
      * **Keuntungan:** Sangat cepat, tidak memerlukan server, dan dapat menunjukkan dengan tepat fungsi mana yang gagal.
      * **Kelemahan:** Tes ini **tidak memverifikasi *routing***. Tes ini akan **LULUS** meskipun konfigurasi rute (`config.add_route`) di `__init__.py` salah atau dihapus.

  * **Functional Testing (Langkah Selanjutnya):**

      * **Fokus:** Menguji keseluruhan *stack* aplikasi, dari *routing* hingga *response*.
      * **Metode:** Membuat permintaan HTTP (simulasi) ke URL (misalnya `GET /`) dan memeriksa respons HTTP.
      * **Keuntungan:** Memverifikasi bahwa semua komponen (rute, *view*, *middleware*) terintegrasi dengan benar.
      * **Kelemahan:** Lebih lambat dan tidak dapat menunjukkan lokasi *error* secara spesifik (misalnya, "error 500 di `/`" bisa jadi karena *view* rusak *atau* rute rusak).

Arsitektur `pyramid.testing` sangat kuat karena menyediakan *tooling* ringan (`DummyRequest`) untuk *unit testing* yang cepat, yang melengkapi *tooling* *functional testing* (seperti `WebTest`).

-----

## 4\. Evaluasi Kekuatan vs. Keterbatasan

  * **Kekuatan:**

      * **Jaring Pengaman (Safety Net):** Developer sekarang dapat melakukan *refactoring* (misalnya, mengubah teks HTML di `hello_world`) dan menjalankan `pytest` untuk memvalidasi bahwa mereka tidak merusak perilaku inti (kontrak) dari *view*.
      * **Pemisahan *Testing*:** Menetapkan `dev_requires` adalah praktik profesional yang memisahkan *tooling* pengembangan dari dependensi *runtime*.
      * **Kecepatan Umpan Balik:** Menjalankan `pytest` jauh lebih cepat daripada me-restart server (`pserve`), membuka *browser*, dan memeriksa hasilnya secara manual.

  * **Keterbatasan (dari Tes Saat Ini):**

      * **Cakupan Tes Lemah:** Tes saat ini hanya memeriksa `status_code == 200`. Tes ini akan tetap lulus meskipun *view* mengembalikan `Response('Terjadi Error!')`. Tes yang lebih kuat juga akan melakukan asersi pada *body* respons (misalnya, `self.assertIn(b'Hello World', response.body)`).
      * **Isolasi Penuh:** Seperti yang disebutkan, tes ini tidak menjamin aplikasi *secara keseluruhan* berfungsi, hanya unit `hello_world` saja.
