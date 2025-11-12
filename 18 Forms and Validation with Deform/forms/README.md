# Analisis Kode: *Form Handling* dan Validasi dengan `deform`

Pada tahap ini, aplikasi beralih dari penanganan *form* HTML manual ke penggunaan *library* `deform`. Ini adalah langkah arsitektural yang signifikan untuk mengabstraksi pembuatan *form*, validasi data, dan *rendering* *error* ke dalam sistem berbasis **skema**.

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan ini sangat besar, menggantikan hampir semua logika *view* dan templat sebelumnya dengan *workflow* (alur kerja) berbasis *form* yang baru.

* **`setup.py` (Dimodifikasi):**
    * Dependensi `deform` ditambahkan ke `install_requires`. Ini adalah dependensi *runtime* baru. `deform` secara otomatis membawa `colander` sebagai dependensinya sendiri.

* **`tutorial/__init__.py` (Dimodifikasi):**
    * **Rute Baru:** Rute `home` dan `hello` lama dihapus dan diganti dengan serangkaian rute berorientasi *resource* (CRUD): `wiki_view` (`/`), `wikipage_add` (`/add`), `wikipage_view` (`/{uid}`), dan `wikipage_edit` (`/{uid}/edit`).
    * **`config.add_static_view('deform_static', 'deform:static/')`:** Ini adalah kunci. Mirip dengan materi *static assets*, ini memberi tahu Pyramid untuk menyajikan file CSS dan JS *internal* milik `deform` (untuk *widget* dan *styling*) di bawah URL `/deform_static/`.

* **`tutorial/views.py` (Modifikasi Kunci - Inti Analisis):**
    * **`pages = {...}`:** Sebuah *database* tiruan (*mock*) dalam memori diperkenalkan untuk menyimpan data wiki.
    * **`class WikiPage(colander.MappingSchema)`:** Ini adalah **Skema**. Menggunakan `colander`, ini mendefinisikan "bentuk" data. Ini mendeklarasikan bahwa data `WikiPage` harus memiliki `title` (sebuah *string*) dan `body` (sebuah *string* yang harus di-*render* menggunakan `RichTextWidget`).
    * **`class WikiViews`:** *View class* ini sekarang sepenuhnya didedikasikan untuk operasi CRUD pada *resource* `WikiPage`.
    * **`@property def wiki_form(self)`:** *Helper* ini membuat *instance* `deform.Form` yang terikat pada skema `WikiPage`. Ini adalah objek utama yang akan menangani *rendering* dan validasi.
    * **`@property def reqts(self)`:** *Helper* ini memanggil `self.wiki_form.get_widget_resources()` untuk mendapatkan daftar file CSS/JS yang dibutuhkan oleh *widget* *form* (khususnya, `RichTextWidget`).
    * **`wikipage_add(self)` dan `wikipage_edit(self)`:** Kedua *view* ini mengikuti **pola *form processing* standar**:
        1.  **Cek `POST`:** Periksa apakah *form* telah di-submit (`if 'submit' in self.request.params`).
        2.  **Validasi:** Coba validasi data `POST` terhadap skema: `appstruct = self.wiki_form.validate(controls)`.
        3.  **Gagal (ValidationFailure):** Jika gagal, tangkap *exception* `deform.ValidationFailure` dan **render ulang *form*** (`return dict(form=e.render())`). `deform` secara otomatis menyuntikkan pesan *error* dan data yang diisi sebelumnya ke dalam HTML *form*.
        4.  **Sukses:** Jika berhasil, `appstruct` berisi data Python yang bersih dan tervalidasi. Lakukan aksi (simpan ke *database* `pages`).
        5.  **Redirect (Post-Redirect-Get):** *Redirect* ke *view* lain (misalnya, `wikipage_view`) menggunakan `HTTPFound`. Ini adalah pola **Post-Redirect-Get (PRG)** untuk mencegah *double-submit* pada *form*.
        6.  **`GET` (Render Awal):** Jika ini adalah permintaan `GET` (bukan `POST`), cukup *render* *form* yang kosong (atau yang sudah diisi, dalam kasus `wikipage_edit`).

* **`tutorial/templates/wikipage_addedit.pt` (Baru):**
    * **Pemuatan *Asset* Deform:** Templat ini memuat CSS/JS yang diperlukan oleh `deform` menggunakan `request.static_url('deform:static/...')` dan *helper* `view.reqts`.
    * **`$ {structure: form}`:** Ini adalah *output* kunci. Alih-alih menulis `<input>` HTML secara manual, kita hanya memberi tahu Chameleon untuk me-*render* variabel `form` (yang berisi `deform.Form`) sebagai HTML mentah (`structure:`). `deform` menangani semua pembuatan *field*, pelabelan, dan penyisipan pesan *error*.

---

## 2. Alur Eksekusi (Penanganan *Form* dengan Validasi)

1.  Pengguna mengunjungi `GET /add` (`wikipage_add`).
2.  `wikipage_add` dieksekusi. `'submit'` tidak ada di `request.params`.
3.  *View* me-*render* *form* kosong (`form = self.wiki_form.render()`).
4.  Konteks `{'form': form}` dikirim ke templat `wikipage_addedit.pt`.
5.  Templat me-*render* HTML *form* lengkap (termasuk *widget* `RichTextWidget`).
6.  Pengguna mengisi *form* (tapi membiarkan `title` kosong) dan menekan "submit".
7.  *Browser* mengirimkan `POST /add`.
8.  `wikipage_add` dieksekusi lagi. `'submit'` **ada** di `request.params`.
9.  `self.wiki_form.validate(controls)` dipanggil.
10. `colander` melihat `title` (yang wajib) kosong dan me-*raise* `deform.ValidationFailure`.
11. Blok `except` menangkap *exception* (`e`).
12. *View* mengembalikan `dict(form=e.render())`. `e.render()` adalah HTML *form* yang di-*render* ulang, sekarang dengan pesan *error* "Required" di sebelah *field* `title`.
13. Templat me-*render* *form* yang berisi *error* tersebut.
14. Pengguna mengisi `title` dan `body`, lalu menekan "submit" lagi.
15. `POST /add` dieksekusi. `self.wiki_form.validate(controls)` **berhasil**.
16. `appstruct` berisi `dict` Python yang bersih (misalnya, `{'title': 'Judul Baru', 'body': '<p>Konten</p>'}`).
17. *View* menyimpan data ini ke *database* `pages`.
18. *View* mengembalikan `HTTPFound` untuk me-*redirect* *browser* ke URL *view* halaman baru (misalnya, `/103`).

---

## 3. Kontekstualisasi Arsitektur: Skema dan *Form Controller*

* **Pemisahan Logika Validasi:** Dengan `colander`, logika validasi (`title` adalah *string* wajib) didefinisikan secara deklaratif di **skema**, bukan di dalam *view*. Ini membuat *view* lebih bersih dan skema dapat digunakan kembali (reusable).
* **Generasi *Form* Otomatis:** Dengan `deform`, *rendering* HTML *form* sepenuhnya diabstraksi. *Developer* hanya perlu mendefinisikan skema, dan `deform` membuat HTML, menangani *widget* (seperti *rich text editor*), dan *rendering* *error*.
* **Pola *Self-Posting Form* dan PRG:** Materi ini mengimplementasikan dua pola desain web yang sangat penting:
    1.  ***Self-Posting Form***: URL yang sama (`/add`) menangani `GET` (menampilkan *form*) dan `POST` (memproses *form*).
    2.  ***Post-Redirect-Get (PRG)***: Setelah `POST` berhasil, aplikasi tidak mengembalikan HTML, melainkan *redirect* 302. Ini mencegah pengguna menekan "refresh" dan mengirim ulang *form* secara tidak sengaja.
* **Integrasi *Asset*:** Ini menunjukkan bagaimana *add-on* (seperti `deform`) dapat mengelola dan menyajikan *static asset* mereka sendiri (`deform:static/`), dan bagaimana aplikasi dapat mengintegrasikannya.

---

## 4. Dampak pada Pengujian (`tutorial/tests.py`)

* **Unit Tests (`TutorialViewTests`):**
    * Tes ini diubah total untuk menguji *view* baru `wiki_view` dan memvalidasi bahwa ia mengembalikan data *database* tiruan yang benar.

* **Functional Tests (`TutorialFunctionalTests`):**
    * Tes ini **diperluas secara masif** untuk mencakup alur kerja CRUD yang baru.
    * `test_home`, `test_add_page`, `test_edit_page`: Ini adalah tes `GET` sederhana untuk memastikan halaman-halaman tersebut di-*load* dengan benar (status 200).
    * `test_post_wiki` dan `test_edit_wiki`: Ini adalah tes *full-stack* yang paling penting. Mereka **mensimulasikan `POST` *form*** (`self.testapp.post(...)`), memvalidasi bahwa aplikasi merespons dengan *redirect* 302, dan kemudian **mengikuti *redirect*** (`self.testapp.get('/103', ...)` untuk memvalidasi bahwa data telah disimpan dengan benar.
