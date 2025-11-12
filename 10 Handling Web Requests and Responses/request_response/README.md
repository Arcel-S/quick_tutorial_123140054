# Analisis Kode: Kontrol Manual HTTP (Request/Response) (Dok. 10)

Pada tahap ini, fokus bergeser dari penggunaan `renderer` (templat) kembali ke penanganan manual objek **Request** dan **Response**. Ini adalah langkah fundamental untuk menunjukkan kontrol penuh atas siklus HTTP, yang penting untuk *redirect*, API, dan penanganan *header* kustom.

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan arsitektural utama terjadi di `tutorial/views.py` dengan menghapus ketergantungan pada *renderer* templat.

* **`tutorial/__init__.py` (Dimodifikasi):**
    * Rute (`routes`) disederhanakan. Rute `/howdy` (bernama `hello`) dihapus dan digantikan oleh rute `/plain` (bernama `plain`).

* **`tutorial/views.py` (Modifikasi Kunci):**
    * **`@view_defaults` (Dihapus):** Dekorator `@view_defaults(renderer='home.pt')` dari materi sebelumnya telah **dihapus**.
    * **Implikasi Penghapusan:** Karena *renderer* *default* tidak lagi ditentukan, semua *view* dalam *class* ini sekarang **wajib** mengembalikan objek `Response` yang valid, bukan lagi `dict`.
    * **`home(self)`:** *View* ini tidak lagi mengembalikan *data dictionary*. Sebaliknya, ia mengembalikan *instance* dari `HTTPFound(location='/plain')`. Ini adalah *class* *exception* khusus yang digunakan Pyramid untuk menghasilkan respons **HTTP 302 Redirect**.
    * **`plain(self)`:** Ini adalah *view* baru yang juga tidak menggunakan *renderer*. *View* ini secara eksplisit mengimpor dan membuat objek `Response` secara manual, mengatur `content_type` dan `body`-nya.

* **`tutorial/home.pt` (Tidak Terpakai):**
    * File templat ini tidak lagi digunakan oleh *view* mana pun dalam logika aplikasi saat ini.

---

## 2. Analisis Kunci: Interaksi Request dan Response

Tahap ini secara eksplisit mendemonstrasikan cara berinteraksi dengan *request* yang masuk dan membuat *response* keluar.

* **Membaca Objek `Request` (Berbasis `WebOb`):**
    * Pyramid menggunakan *library* `WebOb` untuk objek `request`-nya.
    * **`self.request.params.get('name', ...)`:** Ini adalah API kunci. `request.params` adalah *dictionary* gabungan yang secara transparan berisi data dari **GET query string** (misalnya, `?name=...`) dan **POST form data**.
    * **`self.request.url`:** Ini adalah contoh introspeksi *request*, di mana *view* dapat mengakses URL lengkap yang digunakan untuk memanggilnya.

* **Membuat Objek `Response` (Kontrol Penuh):**
    * Ada dua cara yang ditunjukkan di sini:
    1.  **Manual (`Response`):** Di *view* `plain`, `return Response(content_type='text/plain', body=body)` digunakan. Ini memberi developer kontrol penuh atas *status code*, *content-type*, dan *body* mentah. Ini adalah pola esensial untuk membangun **API**.
    2.  **Via *Exception* (`HTTPFound`):** Di *view* `home`, `return HTTPFound(...)` digunakan. Ini adalah cara pintas yang umum di Pyramid. Dengan mengembalikan *class* *exception* HTTP, Pyramid akan menangkapnya dan mengubahnya menjadi `Response` yang sesuai (dalam hal ini, status 302 dengan *header* `Location: /plain`).

---

## 3. Kontekstualisasi Arsitektur: Renderer vs. Kontrol Manual

Materi ini mengkontraskan dua model desain yang berbeda untuk *view*:

1.  **Model Berbasis *Renderer*** (Materi 8 & 9):
    * **Tanggung Jawab *View***: Mengembalikan `dict` (data/konteks).
    * **Tanggung Jawab *Framework***: Mengambil `dict`, merendernya dengan templat, dan membuat `Response` HTML.
    * **Kekuatan:** Pemisahan konsep (SoC) yang sangat baik.

2.  **Model Kontrol Manual** (Materi 10 ini):
    * **Tanggung Jawab *View***: Mengembalikan objek `Response` yang lengkap.
    * **Tanggung Jawab *Framework***: Hanya mengirimkan `Response` tersebut.
    * **Kekuatan:** Kontrol penuh atas protokol HTTP (status, *header*, *body*). Penting untuk *redirect*, API (JSON/XML), dan respons non-HTML.

Aplikasi dunia nyata akan **menggunakan kedua model ini**: *renderer* untuk halaman web, dan kontrol manual untuk *endpoint* API dan *redirect*.

---

## 4. Dampak pada Pengujian (`tutorial/tests.py`)

Perubahan arsitektur *view* ini **mengharuskan** perubahan pada *unit test*.

* **Unit Tests (`TutorialViewTests`):**
    * `test_home`: Sekarang melakukan asersi bahwa `response.status` adalah `'302 Found'`, memvalidasi logika *redirect*.
    * `test_plain_without_name`: Memeriksa `response.body` (sebuah *byte-string*) untuk *string default* (`b'No Name Provided'`).
    * `test_plain_with_name`: Mendemonstrasikan cara **menyuntikkan data ke `DummyRequest`** (`request.GET['name'] = 'Jane Doe'`) untuk mensimulasikan *query string*.

* **Functional Tests (`TutorialFunctionalTests`):**
    * `test_plain_with_name`: Menunjukkan cara *functional test* memanggil *endpoint* dengan *query string* nyata: `self.testapp.get('/plain?name=Jane%20Doe', ...)`.
    * Tes ini memvalidasi *secara end-to-end* bahwa `request.params` berhasil membaca *query string* dan `Response` manual telah dibuat dengan benar.