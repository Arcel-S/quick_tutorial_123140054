# Analisis Kode: *Renderer* JSON untuk AJAX/API

Pada tahap ini, diperkenalkan konsep **renderer non-HTML**, khususnya *renderer* **JSON**. Ini adalah komponen kunci untuk membangun *endpoint* API yang digunakan oleh *frontend* JavaScript (AJAX) atau aplikasi *mobile*.

-----

## 1\. Analisis Teknis dan Perubahan Struktural

Perubahan ini menambahkan *endpoint* API baru yang menggunakan kembali logika *view* yang ada, tetapi "mengemasnya" dalam format yang berbeda (JSON, bukan HTML).

  * **`tutorial/__init__.py` (Dimodifikasi):**

      * Sebuah rute baru ditambahkan:
        ```python
        config.add_route('hello_json', '/howdy.json')
        ```
      * **Alasan Desain:** Rute ini membuat *endpoint* baru yang secara eksplisit ditujukan untuk mengembalikan data JSON, yang ditandai dengan ekstensi `.json`.

  * **`tutorial/views.py` (Modifikasi Kunci):**

      * *Method* `hello(self)` sekarang memiliki **dua dekorator `@view_config` yang ditumpuk (stacked)**:
        ```python
        @view_config(route_name='hello')
        @view_config(route_name='hello_json', renderer='json')
        def hello(self):
            return {'name': 'Hello View'}
        ```
      * **Analisis `hello_json`:** Dekorator kedua ini (`@view_config(route_name='hello_json', renderer='json')`) menambahkan **pemetaan kedua** ke *method* `hello` yang sama.
      * **Analisis `renderer='json'`:** Ini adalah inti dari materi ini. Alih-alih menggunakan *default* kelas (`renderer='home.pt'`), dekorator ini **meng-override** *renderer* khusus untuk rute `hello_json`. `json` adalah *renderer* bawaan Pyramid.

  * **`tutorial/home.pt` (Tidak Berubah):**

      * Templat HTML tidak disentuh.

-----

## 2\. Alur Eksekusi: HTML vs. JSON

*Method* `hello(self)` yang sama sekarang memiliki dua alur eksekusi yang berbeda tergantung pada rute yang cocok:

  * **Alur Permintaan HTML (misalnya, `GET /howdy`)**

    1.  Permintaan masuk ke `GET /howdy`.
    2.  `pserve` -\> `waitress` -\> `pyramid` router.
    3.  Router mencocokkan rute `hello` (URL `/howdy`).
    4.  Pyramid melihat `@view_config(route_name='hello')`.
    5.  Dekorator ini **tidak memiliki** `renderer`, sehingga ia menggunakan *default* kelas: `renderer='home.pt'`.
    6.  *Method* `hello(self)` dipanggil, mengembalikan `{'name': 'Hello View'}`.
    7.  Pyramid mencegat `dict` ini dan memberikannya ke *renderer* **Chameleon (`home.pt`)**.
    8.  Respons **HTML** (`<h1>Hi Hello View</h1>`) dikirim ke *browser*.

  * **Alur Permintaan JSON (misalnya, `GET /howdy.json`)**

    1.  Permintaan masuk ke `GET /howdy.json` (misalnya, dari panggilan `fetch()` JavaScript).
    2.  `pserve` -\> `waitress` -\> `pyramid` router.
    3.  Router mencocokkan rute `hello_json` (URL `/howdy.json`).
    4.  Pyramid melihat `@view_config(route_name='hello_json', renderer='json')`.
    5.  Dekorator ini **memiliki** `renderer='json'`, yang meng-override *default* kelas.
    6.  *Method* `hello(self)` dipanggil, mengembalikan `{'name': 'Hello View'}`.
    7.  Pyramid mencegat `dict` ini dan memberikannya ke *renderer* **JSON**.
    8.  *Renderer* JSON mengubah `dict` menjadi *string* `{"name": "Hello View"}`.
    9.  *Renderer* secara otomatis membuat objek `Response` dengan *header* `Content-Type: application/json`.
    10. Respons **JSON** dikirim ke *client*.

-----

## 3\. Kontekstualisasi Arsitektur: Logika Terpadu, Beragam Representasi

Tahap ini adalah demonstrasi brilian dari arsitektur *renderer* Pyramid dan prinsip SoC.

  * **Reusability (Penggunaan Kembali):** Logika bisnis inti di dalam `hello(self)`—yang menentukan data apa yang harus ditampilkan—hanya ditulis **satu kali**.
  * **Pemisahan Representasi:** *Framework* (melalui konfigurasi `renderer`) menangani **bagaimana** data tersebut disajikan. Dalam satu kasus, sebagai HTML (untuk *browser*), dan di kasus lain, sebagai JSON (untuk API/AJAX).
  * **API vs. UI:** Ini adalah pola arsitektur yang sangat umum. `View` bertindak sebagai sumber data, dan *renderer* yang berbeda digunakan untuk menyajikan data tersebut ke *channel* yang berbeda (UI web dan API).

-----

## 4\. Dampak pada Pengujian (`tutorial/tests.py`)

  * **Unit Tests (`TutorialViewTests`):**

      * **Tidak ada perubahan.** *Unit test* sudah memvalidasi bahwa *method* `hello()` mengembalikan `dict` yang benar. Karena logika ini tidak berubah, tes tetap lulus. Ini sekali lagi membuktikan nilai dari pengujian kontrak data *view* secara terisolasi.

  * **Functional Tests (`TutorialFunctionalTests`):**

      * Tes baru, `test_hello_json`, ditambahkan.
      * Tes ini secara eksplisit memanggil *endpoint* `.json`: `self.testapp.get('/howdy.json', status=200)`.
      * Tes ini memvalidasi **kedua** bagian dari kontrak *renderer* JSON:
        1.  **Konten:** `self.assertIn(b'{"name": "Hello View"}', res.body)`
        2.  **Header:** `self.assertEqual(res.content_type, 'application/json')`