# Analisis Kode: Paket Python

Pada program ini berfokus dalam transisi dari aplikasi *single-file* (Dokumentasi 1) menjadi struktur **Proyek** dan **Paket** Python yang standar.

## 1. Analisis Teknis dan Perubahan Struktural

Dokumen ini mengenalkan tiga file kunci yang mengubah struktur proyek secara fundamental. Kode aplikasi di dalam `app.py` sendiri **tidak berubah** secara logis.

Perubahan utamanya adalah *struktural* dan *lingkungan (environmental)*, diwujudkan oleh file-file berikut:

* `setup.py`
* `tutorial/__init__.py`
* `tutorial/app.py` (Logika identik, lokasi file berubah)

## 2. Analisis `setup.py` (Manajemen Proyek & Dependensi)

File ini adalah "kartu identitas" proyek Python.

* **Fungsi Teknis:** File ini menggunakan `setuptools` untuk mendefinisikan proyek.
* **Analisis Kunci (`install_requires`):**
    * Parameter `install_requires = ['pyramid', 'waitress']` adalah bagian terpenting. Ini secara eksplisit mendeklarasikan dependensi *runtime* proyek.
    * **Mengapa Desain Ini?** Ini adalah fondasi dari **Reproducible Builds**. Sebelumnya (di Dok. 1), dependensi diinstal secara manual. Sekarang, proyek itu sendiri yang "tahu" apa yang dibutuhkannya.
* **Konteks Eksekusi (`pip install -e .`):**
    * Perintah `pip install -e .` (mode *editable*) membaca `setup.py`, menginstal dependensi (`pyramid`, `waitress`), dan membuat *symlink* ke direktori `tutorial`.
    * Ini memungkinkan developer untuk mengedit kode di `tutorial/` dan perubahan tersebut langsung aktif di *virtual environment* tanpa perlu instalasi ulang.

## 3. Analisis `tutorial/__init__.py` (Fondasi Modularitas)

File ini, meskipun (hampir) kosong, memiliki peran arsitektural yang sangat penting.

* **Fungsi Teknis:** Kehadiran file `__init__.py` memberi tahu interpreter Python bahwa direktori `tutorial/` harus diperlakukan sebagai **Paket (Package)**, bukan sekadar folder biasa.
* **Mengapa Desain Ini? (Skalabilitas):**
    * Ini adalah **prasyarat mutlak** untuk memecah aplikasi monolitik.
    * Karena `tutorial` sekarang adalah sebuah paket, kita dapat mulai membuat modul baru di dalamnya (misalnya `tutorial/views.py`, `tutorial/models.py`) dan mengimpornya menggunakan *dot notation* (misal, `from . import views` atau `from tutorial.views import ...`).
    * Di Dok. 1, ini tidak mungkin dilakukan karena aplikasi tersebut bukan bagian dari paket yang terdefinisi.

## 4. Analisis `tutorial/app.py` (Logika & Eksekusi)

* **Logika Aplikasi:** Kode di dalam file ini (Configurator, `hello_world`, `add_route`, `add_view`, `serve`) **identik** dengan Dok. 1. Secara logika, ini masih aplikasi monolitik yang sama.
* **Analisis Metode Eksekusi:**
    * Dokumentasi secara eksplisit menyatakan bahwa menjalankan file ini secara langsung (`python tutorial/app.py`) adalah **"ide yang buruk"** dan "aneh" (*odd duck*).
    * **Mengapa Ini Buruk?** Menjalankan modul di dalam paket secara langsung sebagai skrip dapat menyebabkan masalah besar pada `sys.path` dan *relative import*. Ini **melewatkan/mengesampingkan** seluruh mesin *packaging* dan *entry point* yang seharusnya disediakan oleh `setup.py` dan *runner* WSGI.
    * Ini dilakukan *hanya* untuk tujuan pedagogis (edukasi) agar transisi antar langkah tutorial tetap sederhana.

## 5. Kontekstualisasi Arsitektur dan Evaluasi

### 5.1. Koneksi ke Arsitektur Pyramid (Evolusi)
Langkah ini adalah "jembatan" arsitektural.

* **Dari Dok. 1:** Kita memiliki aplikasi monolitik yang tidak dapat didistribusikan.
* **Di Dok. 2 (Langkah Ini):** Kita telah **"membungkus"** aplikasi monolitik tersebut ke dalam **Paket** yang dapat didistribusikan dan memiliki dependensi yang terdefinisi.
* **Ke Dok. 3 (Langkah Selanjutnya):** Langkah logis berikutnya adalah **memecah** monolith di dalam `tutorial/app.py` menjadi modul-modul yang lebih kecil (`views.py`, `routes.py`, dll.) *di dalam* struktur paket yang baru saja kita buat. Blok `if __name__ == '__main__'` akan digantikan oleh **fungsi pabrik (factory function)** (`def main(...)`) dan *entry point* yang didefinisikan dalam `setup.py` (yang akan dieksekusi oleh *runner* seperti `pserve` melalui file `.ini`).

### 5.2. Evaluasi Kekuatan & Keterbatasan
* **Kekuatan:**
    * **Manajemen Dependensi:** Dependensi proyek kini formal, eksplisit, dan dikelola oleh `pip`.
    * **Fondasi Skalabilitas:** Proyek ini sekarang siap untuk dipecah menjadi beberapa file/modul.
* **Keterbatasan:**
    * **Logika Masih Monolitik:** Aplikasi itu sendiri belum menjadi lebih modular, hanya "bungkus"-nya saja.
    * **Anti-Pattern Eksekusi:** Cara aplikasi ini dijalankan masih merupakan anti-pattern yang harus segera ditinggalkan dalam pengembangan nyata.