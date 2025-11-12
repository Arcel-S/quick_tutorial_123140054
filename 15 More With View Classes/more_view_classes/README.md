# Analisis Kode: *View Predicates* dan *View Classes* Lanjutan

Pada tahap ini, diperkenalkan konsep arsitektural yang kuat: **View Predicates** (Predikat *View*). Ini menunjukkan bagaimana satu *route* (URL) dapat diarahkan ke *beberapa method* yang berbeda di dalam *view class* yang sama, berdasarkan kriteria dari *request* itu sendiri (seperti *method* GET vs. POST, atau parameter form).

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan ini mengkonsolidasikan beberapa tindakan (*actions*) ke dalam satu *view class* yang diikat ke satu *route* dinamis.

* **`tutorial/__init__.py` (Dimodifikasi):**
    * Rute `hello` diubah dari `/howdy` (statis, dari materi yang disalin) menjadi `/howdy/{first}/{last}` (dinamis). Ini adalah **resource URL** utama.
    * Rute `home` (`/`) tetap ada.

* **`tutorial/views.py` (Modifikasi Kunci - Inti Analisis):**
    * **`class TutorialViews`:** Kelas ini sekarang menangani beberapa logika *view* yang berbeda.
    * **`@view_defaults(route_name='hello')`:** Ini adalah dekorator level-kelas. Ini menerapkan prinsip **DRY (Don't Repeat Yourself)** dengan menetapkan bahwa, secara *default*, semua *method* *view* di dalam kelas ini akan terikat pada rute bernama `'hello'`.
    * **`__init__(self, request)`:** *Constructor* menyimpan `self.request` (untuk digunakan oleh *method* lain) dan juga `self.view_name` sebagai *state* yang dapat dibagikan.
    * **`@property def full_name(self)`:** Ini adalah *helper property* yang menunjukkan bagaimana logika dapat dibagikan. Ia membaca `request.matchdict` (dari rute dinamis) untuk membuat sebuah *string*.
    * **`home(self)`:** *Method* ini secara eksplisit **meng-override** *default* kelas dengan `@view_config(route_name='home', ...)`-nya sendiri.
    * **`hello(self)` (GET View):** *Method* ini *tidak* memiliki `route_name`, sehingga ia menggunakan *default* kelas (`route_name='hello'`). Ini adalah *handler* *default* untuk rute tersebut, yang secara implisit merespons `request_method='GET'`.
    * **`edit(self)` (POST View):** *Method* ini juga menggunakan *default* `route_name='hello'`, tetapi menambahkan *predicate* (predikat): **`request_method='POST'`**.
    * **`delete(self)` (POST View Spesifik):** *Method* ini *juga* menggunakan `route_name='hello'` dan `request_method='POST'`, tetapi menambahkan *predicate* yang lebih spesifik: **`request_param='form.delete'`**.

* **`tutorial/templates/` (Diperluas):**
    * Dibuat beberapa templat baru (`hello.pt`, `edit.pt`, `delete.pt`) untuk menangani *renderer* yang berbeda yang ditentukan dalam *view class*.
    * **`hello.pt`:** Templat ini sekarang berisi *form* HTML dengan dua tombol `submit` yang berbeda nama: `<input ... name="form.edit" ...>` dan `<input ... name="form.delete" ...>`.

---

## 2. Alur Eksekusi: *View Predicates*

Perubahan ini adalah demonstrasi paling jelas dari **View Dispatch** (Penerusan *View*) berbasis predikat. Satu URL (`/howdy/jane/doe`) sekarang dapat memiliki 3 perilaku berbeda:

1.  **Permintaan `GET /howdy/jane/doe`:**
    * `route_name='hello'` cocok.
    * Pyramid mencari *view* yang cocok.
    * `edit` dan `delete` gagal karena mereka memerlukan `POST`.
    * `hello` cocok (karena `GET` adalah *default*).
    * **`hello(self)` dieksekusi**, me-*render* `hello.pt`.

2.  **Permintaan `POST` dari tombol "Save" (`form.edit`):**
    * `route_name='hello'` cocok.
    * `request_method='POST'` cocok.
    * Pyramid mengevaluasi *view* `POST`.
    * `delete` diperiksa terlebih dahulu (lebih spesifik) dan gagal (karena `form.delete` tidak ada di *request*).
    * `edit` diperiksa dan cocok.
    * **`edit(self)` dieksekusi**, me-*render* `edit.pt`.

3.  **Permintaan `POST` dari tombol "Delete" (`form.delete`):**
    * `route_name='hello'` cocok.
    * `request_method='POST'` cocok.
    * Pyramid mengevaluasi *view* `POST`.
    * `delete` diperiksa dan **cocok** (karena `form.delete` ada di *request*).
    * **`delete(self)` dieksekusi**, me-*render* `delete.pt`.

---

## 3. Kontekstualisasi Arsitektur: Pola *Resource-Action*

* **Pola *View Class* (Revisi):** Materi ini menunjukkan kekuatan sebenarnya dari *view class*: tidak hanya untuk *grouping*, tetapi untuk mengelola **seluruh siklus hidup (*lifecycle*) dari satu *resource***. `TutorialViews` sekarang mengelola *resource* `hello` (`/howdy/{first}/{last}`).
* **Pola RESTful:** Ini adalah fondasi dari API RESTful. Satu URL *resource* (misalnya, `/api/users/123`) dapat dipetakan ke satu *class*, dan *method* yang berbeda (`GET`, `POST`, `PUT`, `DELETE`) dipetakan ke *method* yang berbeda di dalam *class* tersebut menggunakan *predicate* `request_method`.
* **Shared State (`view`):** Templat sekarang dapat mengakses `view.view_name` dan `view.full_name`. Ketika *renderer* digunakan dengan *view class*, Pyramid secara otomatis menyuntikkan *instance* dari *class* (yang kita sebut `self` di kode) ke dalam templat sebagai variabel bernama `view`. Ini memungkinkan templat untuk memanggil *helper property* dan mengakses *state* dari *class*.
* **URL Generation:**
    * **`request.route_url(...)`:** Templat `home.pt` sekarang menggunakan `request.route_url('hello', first='jane', last='doe')`. Ini adalah cara yang aman untuk membuat URL dinamis.
    * **`request.current_route_url()`:** Templat `hello.pt` (*form*) menggunakan `action="${request.current_route_url()}"`. Ini adalah *helper* yang sangat berguna yang membuat URL *kembali ke dirinya sendiri*, yang sempurna untuk *form* yang mem-POST ke URL yang sama yang menampilkannya.

---

## 4. Dampak pada Pengujian (`tutorial/tests.py`)

* **Unit Tests (`TutorialViewTests`):**
    * Tes disederhanakan untuk hanya menguji *view* `home`.
    * Untuk menguji `edit` atau `delete` secara unit, `DummyRequest` sekarang harus disiapkan dengan lebih kompleks (misalnya, `request.method = 'POST'`, `request.params = {'form.delete': 'Delete'}`) untuk memenuhi predikat *view*.

* **Functional Tests (`TutorialFunctionalTests`):**
    * Tes fungsional sangat penting untuk memvalidasi alur kerja baru ini. Tes ini perlu diperluas untuk mem-POST ke URL `/howdy/jane/doe` dengan *payload* yang berbeda (misalnya, menyertakan `form.edit` vs `form.delete`) dan menegaskan bahwa templat yang benar (`edit.pt` vs `delete.pt`) yang dikembalikan.