# yescut_furigana

A python script that can be used to cut furigana from (clean) Japanese **Novel** scans.

## Motivation

Furigana are small letters written to the right of kanji to facilitate reading/recognition.
If you would like to OCR text from your scans, *especially using [tesseract](github.com/tesseract-ocr)*,
It's probably a good idea to cut furigana first. (Often gives a slight accuracy boost.)

## requirements
 * Python 3.7 (Only for the new format strings; if you dont have 3.7 just fix those bits.)
 * Pillow
 * The files containing text must be in .png format (for now)

## Tips
 
 * The files must be very, very, very clean near the text. Little black specks near the edge are automatically cut out.
 * The algorithm relies heavily on the text being exactly vertical.
 * The algorithm starts off by cutting 1/11 from the top, ans 1/20 each from the sides. Please just feed the whole page. 
 * If the lines are too close together we cannot deal with those pages. A good example would be HenNeko vol. 1.
 * If there are minimal amounts of furigana in the scan, **don't use this.** This tool will do more harm than good.
 * In contrast, if the scan has a LOT of furigana(like the monogatari series) it is a good idea to use this tool.
 
## Usage - Step by step.
Clone this repo.

*First*, As there are quite a few parameters we need to tweak, _we use a config file_. 
You are free to choose any name you want, as long as your shell can handle it. 
Please refer to the [example file](https://github.com/stet-stet/yescut_furigana/blob/master/bakemonoconfig).

*Then", do: `python yes_cut.py (name of your config file)`

Due to copyright concerns I will not be able to post example output images. Sorry for the inconvenience.

## etc etc

Please, use yescut_furigana only to convert the books you have **legally bought** in japan.
I do not hold any responsibilities for what crimes you might choose to commit, if you do.
Please support the authors by legally buying the books if possible.
If you need translations of light novels, check out sites like [Bookwalker](global.bookwalker.jp), where you can legally buy the books.

## Words of caution


