# Analisis Kode: *Routing* Dinamis dengan *Matchdict*

Pada tahap ini, diperkenalkan konsep **dynamic routing** (rute dinamis), di mana bagian dari URL ditangkap sebagai variabel dan diteruskan ke *view*. Ini adalah pola fundamental untuk membuat halaman yang digerakkan oleh data (misalnya, `/users/1`, `/blog/my-post-title`).

-----

## 1\. Analisis Teknis dan Perubahan Struktural

Perubahan inti terjadi pada definisi rute di `__init__.py` dan cara *view* mengakses data di `views.py`.

  * **`tutorial/__init__.py` (Modifikasi Kunci):**

      * Definisi rute `home` diubah secara signifikan:
        ```python
        config.add_route('home', '/howdy/{first}/{last}')
        ```
      * **Analisis Rute:**
          * Rute ini sekarang hanya akan cocok dengan URL yang memiliki tiga segmen (misalnya, `/howdy/amy/smith`).
          * `{first}` dan `{last}` adalah **placeholder** atau "pola pengganti". Mereka memberi tahu *router* untuk menangkap apa pun di segmen URL tersebut dan menyimpannya.
      * Rute `/` dan `/plain` dari materi sebelumnya telah dihapus untuk menyederhanakan contoh.

  * **`tutorial/views.py` (Modifikasi Kunci):**

      * *View* `hello` telah dihapus.
      * *View* `home` (yang sekarang terikat ke rute `home` baru) dimodifikasi untuk **mengakses data dinamis** dari URL:
        ```python
        first = self.request.matchdict['first']
        last = self.request.matchdict['last']
        ```
      * **Analisis `request.matchdict`:**
          * Ini adalah **konsep kunci**. Ketika rute dinamis (`/howdy/{first}/{last}`) cocok dengan URL (`/howdy/amy/smith`), Pyramid mengekstrak nilai-nilai tersebut dan menempatkannya ke dalam *dictionary* khusus pada objek `request` yang disebut `matchdict`.
          * `matchdict` akan berisi: `{'first': 'amy', 'last': 'smith'}`.
          * *View* kemudian mengakses *dictionary* ini untuk mengambil nilai-nilai tersebut dan meneruskannya ke templat.

  * **`tutorial/home.pt` (Dimodifikasi):**

      * Templat diperbarui untuk me-*render* variabel `first` dan `last` baru yang diteruskan dari *view*:
        ```html
        <p>First: ${first}, Last: ${last}</p>
        ```

-----

## 2\. Alur Eksekusi (dengan *Matchdict*)

1.  Permintaan HTTP masuk ke `GET /howdy/Jane/Doe`.
2.  Pyramid *router* memeriksa `config.add_route('home', '/howdy/{first}/{last}')`.
3.  Rute tersebut **cocok** (match).
4.  Pyramid membuat `request.matchdict` berisi `{'first': 'Jane', 'last': 'Doe'}`.
5.  Router memetakan rute `home` ke `TutorialViews.home`.
6.  Pyramid menginstansiasi *view*: `inst = TutorialViews(request)`.
7.  Pyramid memanggil *method* `inst.home()`.
8.  Di dalam `home()`, kode `self.request.matchdict['first']` mengambil `'Jane'` dan `self.request.matchdict['last']` mengambil `'Doe'`.
9.  *View* mengembalikan *dictionary*: `{'name': 'Home View', 'first': 'Jane', 'last': 'Doe'}`.
10. *Renderer* mengambil *dictionary* ini dan me-*render* templat `home.pt`, menghasilkan HTML akhir.

-----

## 3\. Kontekstualisasi Arsitektur: *Query String* vs. *Path Segment*

Tahap ini mengkontraskan dua cara berbeda untuk meneruskan data melalui URL:

  * **Query String (Materi 10):**

      * **Contoh:** `/plain?name=Jane`
      * **Akses:** `request.params.get('name')`
      * **Penggunaan:** Terbaik untuk data opsional, pemfilteran, atau data pencarian (misalnya, `/search?q=pyramid`).

  * **Path Segment / Matchdict (Materi 11 ini):**

      * **Contoh:** `/howdy/Jane/Doe`
      * **Akses:** `request.matchdict['first']`
      * **Penggunaan:** Terbaik untuk mengidentifikasi *resource* secara unik (misalnya, `/users/123`, `/posts/my-title`). Ini adalah inti dari URL RESTful.

Pyramid (melalui `WebOb`) menyediakan mekanisme yang jelas dan berbeda untuk mengakses kedua jenis parameter URL ini.

-----

## 4\. Dampak pada Pengujian (`tutorial/tests.py`)

Kedua *suite* pengujian harus dimodifikasi secara signifikan untuk mencerminkan arsitektur rute baru.

  * **Unit Tests (`TutorialViewTests`):**

      * **Pola Kunci:** Karena *view* sekarang bergantung pada `request.matchdict` untuk dieksekusi, *unit test* **harus mensimulasikan `matchdict` ini**.
      * Kode `request.matchdict['first'] = 'First'` dan `request.matchdict['last'] = 'Last'` ditambahkan.
      * Ini mendemonstrasikan cara menguji *view* yang mengharapkan data rute dinamis secara terisolasi, **tanpa menjalankan *router* yang sebenarnya**.
      * Asersi diubah untuk memvalidasi bahwa data dari `matchdict` tiruan diteruskan dengan benar ke *dictionary* keluaran.

  * **Functional Tests (`TutorialFunctionalTests`):**

      * Tes ini sekarang memanggil URL dinamis yang sebenarnya: `self.testapp.get('/howdy/Jane/Doe', ...)`.
      * Tes ini **memvalidasi keseluruhan alur**: bahwa rute `/howdy/{first}/{last}` didefinisikan dengan benar, bahwa rute tersebut mengekstrak `Jane` dan `Doe`, meneruskannya ke *view* yang benar, dan bahwa *view* serta templat me-*render* nilai-nilai tersebut ke dalam HTML akhir.