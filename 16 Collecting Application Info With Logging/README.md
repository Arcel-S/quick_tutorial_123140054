# Analisis Kode: *Logging* Aplikasi

Pada tahap ini, diperkenalkan **logging** (pencatatan log) yang merupakan praktik standar untuk merekam kejadian aplikasi. Ini adalah langkah penting untuk *debugging* saat pengembangan dan pemantauan (*monitoring*) saat produksi.

---

## 1. Analisis Teknis dan Perubahan Struktural

Perubahan utama melibatkan penambahan konfigurasi *logging* di file `.ini` dan pemanggilan *logger* di dalam kode *view*.

* **`development.ini` (Modifikasi Kunci):**
    * File ini **diperluas secara signifikan** dengan menambahkan serangkaian bagian `[logger_...]`, `[handler_...]`, dan `[formatter_...]`.
    * **Analisis Konfigurasi:**
        * **`[loggers]`:** Mendefinisikan nama *logger* yang akan dikonfigurasi. `root` adalah *logger* utama, dan `tutorial` adalah *logger* baru yang spesifik untuk aplikasi kita.
        * **`[handlers]`:** Mendefinisikan *ke mana* log harus dikirim. `console` mendefinisikannya sebagai *standard output* (konsol terminal).
        * **`[formatters]`:** Mendefinisikan *bagaimana* setiap baris log harus diformat. `generic` mendefinisikan format yang menyertakan stempel waktu, level log, nama *logger*, dan pesan.
        * **`[logger_tutorial]`:** Ini adalah konfigurasi inti untuk aplikasi kita. `level = DEBUG` berarti ia akan mencatat semua pesan dari level DEBUG ke atas. `handlers =` (kosong) dan `qualname = tutorial` mengikat *logger* ini ke paket `tutorial`.
        * **`[logger_root]`:** Ini adalah *catch-all* *logger*. `level = INFO` berarti ia hanya akan mencatat pesan INFO dan di atasnya.
    * **Alasan Desain:** Pendekatan ini (menggunakan file `.ini`) sepenuhnya memisahkan **konfigurasi *logging*** dari **kode aplikasi**. Kita dapat mengubah *level log* (misalnya, dari `DEBUG` ke `ERROR`) di server produksi hanya dengan mengedit file `.ini`, tanpa perlu mengubah kode Python atau *me-redeploy* aplikasi.

* **`tutorial/views.py` (Dimodifikasi):**
    * **`import logging`:** Mengimpor pustaka *logging* standar Python.
    * **`log = logging.getLogger(__name__)`:** Ini adalah praktik terbaik. Ini membuat *instance* *logger* yang di-namespaced secara otomatis sesuai dengan nama modul (misalnya, `tutorial.views`). Karena *namespa*cenya diawali dengan `tutorial`, konfigurasinya akan secara otomatis diambil dari bagian `[logger_tutorial]` di file `.ini`.
    * **`log.debug(...)`:** Panggilan ini ditambahkan ke dalam *view* `home` dan `hello`. Ini adalah pernyataan log yang hanya akan menghasilkan *output* jika *level* *logger* `tutorial` diatur ke `DEBUG` (seperti yang kita lakukan di `.ini`).

---

## 2. Alur Eksekusi (dengan *Logging*)

1.  Aplikasi dimulai dengan `pserve development.ini`.
2.  `pserve` membaca konfigurasi *logging* dari `.ini` dan mengonfigurasi pustaka `logging` standar Python.
3.  Permintaan masuk ke `GET /`.
4.  `pserve` -> `waitress` -> `pyramid` router.
5.  Router mencocokkan rute `home` dan memanggil `TutorialViews.home`.
6.  Baris `log.debug('In home view')` dieksekusi.
7.  *Logger* `tutorial.views` memeriksa levelnya. Karena diatur ke `DEBUG`, ia memproses pesan tersebut.
8.  Pesan dikirim ke `handler_console`, diformat oleh `formatter_generic`, dan dicetak ke konsol (`stderr`).
9.  *View* mengembalikan `dict`, dan templat di-*render* seperti biasa.

---

## 3. Kontekstualisasi Arsitektur: *Observability*

*Logging* adalah pilar dari **Observability** (kemampuan untuk mengamati sistem).

* **Standarisasi Python:** Pyramid tidak menciptakan sistem *logging* sendiri. Ia sepenuhnya mengadopsi dan terintegrasi dengan pustaka `logging` bawaan Python. Ini adalah keuntungan besar karena semua *best practice* dan *library* pihak ketiga untuk *logging* (misalnya, mengirim log ke layanan eksternal) dapat langsung digunakan.
* **Granularitas Konfigurasi:** Dengan mendefinisikan *logger* `tutorial` dan `root` secara terpisah, kita mendapatkan kontrol granular. Kita dapat mengatur log aplikasi kita sendiri (`tutorial`) ke level `DEBUG` yang "berisik" sambil menjaga log *framework* lain (`root`) tetap "tenang" di level `INFO`.
* **Integrasi Debug Toolbar:** *Log* yang dihasilkan juga secara otomatis ditangkap oleh `pyramid_debugtoolbar` (jika aktif) dan ditampilkan di panel "Logging" di *browser*, yang sangat berguna untuk *debugging* saat pengembangan.

---

## 4. Dampak pada Pengujian (`tutorial/tests.py`)

* **Tidak ada perubahan pada tes.**
* **Alasan:** Panggilan *logging* adalah *side effect* yang tidak mengubah *output* atau *kontrak* dari *view*. *View* `home` masih mengembalikan `dict` yang sama seperti sebelumnya. Oleh karena itu, *unit test* dan *functional test* yang ada tetap lulus tanpa modifikasi.
* **Catatan Pengujian Lanjutan:** Dimungkinkan untuk menulis tes yang secara khusus melakukan asersi bahwa pesan log tertentu *telah* dicatat (dengan men-setup *handler* log tiruan), tetapi itu di luar cakupan materi ini.