<div align="center">
<img width="1500" height="500" alt="KavunBanner" src="https://github.com/user-attachments/assets/e5aa6518-dfac-4bdf-9242-29ca01d355c2" />
</div>

---

Kavun, yeni başlayanlar için uygun, high-level bir programlama dilidir. Python, BASIC ve HyperTalk'tan esinlenerek, okunabilir ve anlaşılır olacak şekilde tasarlanmıştır, Türkçe benzeri bir syntax kullanır ve ana dili Türkçe olanlara programlama dillerinin nasıl çalıştığını anlatmakda yardımcı olmak için tanıdık bir yazım biçimi oluşturmayı hedefler.

Kavun is a beginner-friendly, high-level interpreted programming language. Inspired by Python, BASIC, and HyperTalk, it uses a natural Turkish-like syntax, designed to be readable and expressive. This language strives to have a very readable code base for native Turkish speakers to help understand how programming languages work while keeping in-tact the basic functionalities.
```kavun
"Merhaba Dünya!" yaz
```
## 🍈Katkıda Bulunun!

Kavun halka açık ve büyümeye hazır bir programlama dil krokisidir. Yardım etmek isterseniz:

- "Pull request" göndererek özellik(feature), örnek, düzenleme ya da hata düzeltmesi ekleyebilirsin
- Yeni `.kvn` örnek dosyalarıyla dili tanıtmaya katkı sağlayabilirsin
- Kendi derleyicinizi(compiler) veya yorumlayıcınızı(interpreter) yapmak isterseniz bu projeyi forklayın!

Yapılan her katkı değerlidir. Kodlamaya yeni başlayanlara Türkçe tabanlı bir dil kazandırmak için birlikte çalışalım!

## Temel Özellikler (Key Features)

- Turkish-inspired syntax (`eşittir`, `yaz`, `ise`, `bitir`, etc.) and syntax structure, similar to a spoken language, making it very easy to understand.
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
```
---
### Girdi ve Yazdırma (Input & Output)

```kavun
"Merhaba dünya" yaz
isim eşittir cevap()
// cevap(isim)
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
    eğer i 5 eşit ise:
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
Her iki yazım da aynı sonucu verir. Tercihinize göre istediğinizi kullanabilirsiniz:

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
