# Analisis Kode: Organisasi dengan *View Classes*

Pada tahap ini, diperkenalkan refaktorisasi arsitektural dari *view* berbasis fungsi (Fungsional) ke *view* berbasis kelas (Berorientasi Objek/OOP). Ini adalah pola untuk mengorganisasi logika yang terkait secara tematik.

---

## 1. Analisis Teknis dan Perubahan Struktural

Fungsionalitas aplikasi tidak berubah, tetapi implementasi di `tutorial/views.py` diubah secara signifikan untuk menggunakan *class*.

* **`tutorial/views.py` (Dimodifikasi secara Total):**
    * **`class TutorialViews`:** Dibuat sebuah kelas baru yang menampung logika *view* yang sebelumnya merupakan fungsi terpisah.
    * **`__init__(self, request)`:** Ini adalah *constructor* kelas. Ketika Pyramid memetakan sebuah permintaan ke *view class*, Pyramid akan **menginstansiasi** kelas tersebut *untuk setiap permintaan* dan secara otomatis menyuntikkan (`inject`) objek `request` ke dalam *constructor*. Kode ini menyimpannya sebagai `self.request` agar dapat diakses oleh metode lain di dalam kelas.
    * **`@view_defaults(renderer='home.pt')`:** Ini adalah dekorator level-kelas. Tujuannya adalah untuk menerapkan prinsip **DRY (Don't Repeat Yourself)**. Karena semua *view* dalam kelas ini menggunakan *renderer* yang sama (`home.pt`), kita mendefinisikannya satu kali di level kelas.
    * **`@view_config(...)`:** Dekorator level-metode sekarang menjadi lebih sederhana. Mereka tidak lagi perlu mendeklarasikan `renderer='...'` karena mereka **mewarisi** (inherit) konfigurasi *default* dari kelas. Mereka hanya perlu mendefinisikan apa yang unik, yaitu `route_name`.
    * **`home(self)` dan `hello(self)`:** *View* sekarang adalah *method* dari *class*. Mereka menerima `self` (sebagai *instance* dari `TutorialViews`) dan dapat mengakses *request* melalui `self.request` (meskipun dalam contoh sederhana ini tidak digunakan).

* **`tutorial/__init__.py` (Tidak Berubah):**
    * File ini tidak perlu diubah. Mekanisme `config.scan('.views')` cukup pintar untuk menemukan dekorator `@view_config` baik pada fungsi maupun pada *method* di dalam *class*.

---

## 2. Filosofi Konfigurasi: Pola OOP pada *View*

Pergeseran dari fungsi ke kelas adalah pilihan arsitektural untuk skalabilitas dan pemeliharaan.

* **Mengapa Menggunakan *Class*?**
    * **Grouping (Pengelompokan):** Ini secara logis mengelompokkan *view* yang terkait. Misalnya, dalam aplikasi nyata, Anda mungkin memiliki `BlogViews` (dengan metode `index`, `get_post`, `create_post`) dan `UserViews` (dengan metode `login`, `logout`, `profile`).
    * **Berbagi State dan Logika:** Semua metode dalam *class* berbagi *instance* yang sama. Ini sangat berguna untuk:
        1.  Berbagi *state* (seperti `self.request`).
        2.  Membuat fungsi *helper* yang dapat digunakan kembali. (Contoh: `def _get_user(self): ...` yang dapat dipanggil oleh *view* lain di kelas yang sama).
    * **DRY (Don't Repeat Yourself):** Seperti yang ditunjukkan oleh `@view_defaults`, konfigurasi yang berulang (seperti *renderer*, *permission*, dll.) dapat didefinisikan satu kali untuk semua *view* di dalam kelas.

---

## 3. Kontekstualisasi Arsitektur dan Skalabilitas

Pola *View Class* sangat penting untuk membangun aplikasi yang kompleks dan *API RESTful*.

* **Skalabilitas:** Pola ini jauh lebih mudah dikelola daripada puluhan fungsi *view* yang terpisah dalam satu file.
* **API RESTful:** Pola ini adalah fondasi alami untuk *REST API*. Sebuah *class* tunggal dapat mewakili satu *resource* (misalnya, `/post/{id}`) dan menggunakan *method* yang berbeda untuk *verb* HTTP yang berbeda:
    * `def get(self):` (untuk `request_method='GET'`)
    * `def post(self):` (untuk `request_method='POST'`)
    * `def delete(self):` (untuk `request_method='DELETE'`)

---

## 4. Dampak pada Pengujian (`tutorial/tests.py`)

*Functional test* tidak berubah, tetapi *unit test* **harus** beradaptasi dengan arsitektur *class* yang baru.

* **Unit Tests (`TutorialViewTests`):**
    * Tes ini sekarang harus mengimpor `TutorialViews` (bukan fungsi `home`/`hello`).
    * Alur tes berubah:
        1.  Membuat `DummyRequest`.
        2.  **Menginstansiasi *view class*** dengan *request* tersebut: `inst = TutorialViews(request)`.
        3.  **Memanggil *method*** pada *instance* tersebut: `response = inst.home()`.
    * Asersi tetap sama (`self.assertEqual(...)`) karena *kontrak* *view* (mengembalikan *dict*) tidak berubah.

* **Functional Tests (`TutorialFunctionalTests`):**
    * **Tidak ada perubahan sama sekali.**
    * **Mengapa?** Ini adalah poin arsitektural yang penting. *Functional test* adalah tes *black-box*. Tes ini tidak peduli *bagaimana* *view* diimplementasikan (sebagai fungsi atau *class*). Tes ini hanya peduli bahwa mengirimkan `GET` ke URL `/` mengembalikan HTML yang diharapkan. Ini membuktikan bahwa refaktorisasi internal tidak merusak perilaku eksternal aplikasi.
