<div align="center">
<img width="1500" height="500" alt="KavunBanner" src="https://github.com/user-attachments/assets/e5aa6518-dfac-4bdf-9242-29ca01d355c2" />
</div>

---
Kavun, yeni başlayanlar için uygun, high-level bir programlama dilidir. Python, BASIC ve HyperTalk'tan esinlenerek, okunabilir ve anlaşılır olacak şekilde tasarlanmıştır, Türkçe benzeri bir syntax kullanır ve ana dili Türkçe olanlara programlama dillerinin nasıl çalıştığını anlatmakda yardımcı olmak için tanıdık bir yazım biçimi oluşturmayı hedefler.

Kavun is a beginner-friendly, high-level interpreted programming language. Inspired by Python, BASIC, and HyperTalk, it uses a natural Turkish-like syntax, designed to be readable and expressive. This language strives to have a very readable code base for native Turkish speakers to help understand how programming languages work while keeping in-tact the basic functionalities.
```kavun
"Merhaba Dünya!" yaz
```
---

## Temel Özellikler (Key Features)

- Turkish-inspired syntax (`eşittir`, `yaz`, `ise`, `bitir`, etc.) and syntax strüçture, similar to a spoken language, making it very easy to understand.
- The language is whitespace sensitive, using “spaces” and indenting instead of curly braces.
- Natural function calls and flow control to keep things straight forward.
- Beginner-friendly and helps to teach the fundamentals of coding.
- Kavun script file's format is `.kvn`

## Dildeki Terimler (Language Guide)

### Değişken Atama (Variable Assignment)

```kavun
a = 5
b eşittir 10
isim eşittir "Ali"
anahtar eşittir doğru // Doğru = True, Yanlış = False
```
---
### Girdi, Temizle ve Yazdırma (Input, Clear & Output)

```kavun
"Merhaba dünya" yaz
isim eşittir cevap()
temizle
"Merhaba " + isim yaz
```
---
### Yorum Satırı (Comments)

```kavun
// Bu bir yorumdur
// This is a comment
```
---
### Koşullar (If / Else)

```kavun
yaş eşittir cevap()

yaş küçüktür 18 ise:
    "Gençsin." yaz
yoksa yaş 18 eşit ise:
    "Tam 18’sin!" yaz
yoksa:
    "Olgunsun." yaz
bitir
```
---
### Karşılaştırmalar (Comparisons):

| Normal         | Kavun               |
|----------------|---------------------|
| =              | eşit (at end)       |
| !=             | farklı (at end)     |
| <              | küçüktür            |
| >              | büyüktür            |
| >=, <=         | >=, <= (no keywords)|
| and            | ve                  |
| or             | veya                |
| not            | değil (at end)      |



```kavun
yaş eşittir cevap()

yaş büyüktür 10 ve yaş küçüktür 20 ise:
    "Gençsin." yaz
bitir

yaş 18 farklı ise:
    "18 değilsin" yaz
bitir
```
---
### Döngüler (Loops)

#### While Döngüsü (While Loop)

```kavun
cevap eşittir ""

cevap "çık" değil iken:
    "Komut girin:" yaz
    komutum eşittir cevap() // cevap(komutum)
bitir
```

#### For Döngüsü (For Loop)

```kavun
i için 1 den 5 kadar:
    i yaz
bitir
```

#### Döngü Kontrol (Loop Control)

```kavun
i için 1 den 10 kadar:
    i yaz
    i 5 eşit ise:
        "Beş bulundu!" yaz
        kır
    bitir
    devam
bitir
```
---
### Fonksiyonlar (Functions)
Kavun, fonksiyon çağırmak için iki farklı yazım tarzını destekler:

Kavun supports two types of function call syntax:
1. Kavun Tarzı
```
3, 4 ile topla işi
```
2. Bilindik Tarz
```
iş topla(3, 4)
```
Her iki yazım da aynı sonuçu verir. Tercihinize göre istediğinizi kullanabilirsiniz:

Both function calls behave the same, use it however you like:
```
a, b ile topla işi:
    a + b dön
bitir

sonuç eşittir iş topla(5, 10)
sonuç yaz
```
---
#### Fonksiyon Tanımı (Function Declaration)

```kavun
a, b ile topla işi:
    a + b dön
bitir
```

#### Fonksiyon Çağrısı (Function Call)

```kavun
sonuç eşittir 3, 4 ile topla işi
sonuç yaz
```

#### Void Fonksiyon (Void Function)

```kavun
isim ile selam_ver işi:
    "Merhaba " + isim yaz
bitir

"Demir" ile selam_ver işi
```

#### Erken Dönüş (Return)
```kavun
sayı ile kontrol_et işi:
    sayı = 0 ise:
        dön
    bitir
    "Devam ediyor" yaz
bitir
```
### Matematik ve Rastgele Sayılar (Math & Random Numbers)

```kavun
// Rastgele sayı üretme
rastgele_sayı()
"Rastgele sayı: " + rastgele yaz

// Belirli aralıkta rastgele sayı
1 ile 10 arasi_rastgele()
"1-10 arası: " + rastgele yaz

// Matematik fonksiyonları
sayi eşittir 16
karekök eşittir karekök(sayi)
kuvvet_sonuç eşittir kuvvet(2, 8)
mutlak_değer eşittir mutlak(-5)
yuvarlanmis eşittir yuvarla(3.14159, 2)
```

### Liste İşlemleri (List Operations)

```kavun
// Liste oluşturma
meyveler eşittir ["elma", "armut", "muz"]
sayilar eşittir [1, 2, 3, 4, 5]

// Liste elemanına erişim
ilk_meyve eşittir meyveler[0]

// Liste elemanı değiştirme
meyveler[1] eşittir "ayva"

// Listeye eleman ekleme
meyveler.ekle("kiraz")

// Listeden eleman silme
meyveler.sil(2)

// Liste uzunluğu
"Liste uzunluğu: " + len(meyveler) yaz
```

### Metin İşlemleri (Text Operations)

```kavun
metin eşittir "Merhaba Kavun!"

// Metin uzunluğu
metin.uzunluk()
"Uzunluk: " + metin_uzunluk yaz

// Büyük/küçük harf dönüşümü
metin.büyük_harf()
metin.küçük_harf()

// Metin arama ve değiştirme
pozisyon eşittir metin_bul(metin, "Kavun")
yeni_metin eşittir metin_degistir(metin, "Kavun", "Dünya")

// Metin kesme
ilk_5 eşittir metin_kes(metin, 0, 5)
```

### Dosya İşlemleri (File Operations)

```kavun
// Dosya yazma
dosya_yaz("test.txt", "Merhaba Dünya!")

// Dosya okuma
dosya_oku("test.txt")
"İçerik: " + dosya_içerik yaz

// Dosyaya ekleme
dosya_ekle("test.txt", "\nYeni satır")

// Dosya kontrolü
dosya_var_mı("test.txt")

// Klasör listesi
klasör_listesi()
```

### Zaman İşlemleri (Time Operations)

```kavun
// Şu anki zaman
şimdi()
"Zaman: " + şu_an yaz

// Tarih ve saat
tarih()
saat()

// Bekleme
2 saniye bekle
```

### Trigonometrik Fonksiyonlar (Trigonometric Functions)

```kavun
açı eşittir 0.5
sin_değer eşittir sin(açı)
cos_değer eşittir cos(açı)
tan_değer eşittir tan(açı)

// Logaritma
log_değer eşittir log(10)
log10_değer eşittir log10(100)
```

### Artı Komutlar (Other Commands)

```kavun
// Yeni satır
yeni_satır

// Bekleme
1.5 saniye bekle

// Ekran temizleme
temizle
```

### Renkli Yazdırma ve Animasyon (Colored Output & Animation)

```kavun
// Renkli yazdırma
"Başarılı!" yeşil_yaz
"Hata!" kırmızı_yaz
"Uyarı!" sarı_yaz
"Bilgi" mavi_yaz
"Özel" mor_yaz
"Not" cyan_yaz

// Animasyonlu yazdırma
"Yükleniyor..." animasyonlu_yaz
2 saniye bekle
animasyon_durdur
```

### ASCII Çizim ve Grafikler (ASCII Drawing & Graphs)

```kavun
// ASCII çizimler
üçgen_çiz(5)      // 5 satırlık üçgen
kare_çiz(4)       // 4x4 kare
kalp_çiz()        // Kalp çizimi

// Basit grafik
veriler eşittir [10, 25, 15, 30, 20]
grafik_çiz(veriler)
```

### Sözlük İşlemleri (Dictionary Operations)

```kavun
// Sözlük oluşturma
kisi eşittir {"isim": "Ahmet", "yas": 25, "sehir": "İstanbul"}

// Sözlük elemanına erişim
isim eşittir kisi["isim"]
yas eşittir kisi["yas"]

// Sözlük elemanı değiştirme
kisi["yas"] eşittir 26

// Sözlük fonksiyonları
anahtarlar eşittir sözlük_anahtarlar(kisi)
değerler eşittir sözlük_değerler(kisi)
uzunluk eşittir sözlük_uzunluk(kisi)

// Sözlük silme
silinen eşittir sözlük_sil(kisi, "telefon")
```
