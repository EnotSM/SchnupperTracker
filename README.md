# SchnupperTracker

[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.1-000?logo=flask)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Пошук учнівських практик (Schnupperlehren) та навчальних місць (Lehrstellen) у кантоні Цюрих через API `berufswahl.zh.ch`. Збереження цікавих варіантів, зміна статусу, нотатки.

---

## Що вміє

- фільтр по типу (Schnupperlehre / Lehrstelle), професії (мультивибір тегами), локації
- автокомпліт професій з урахуванням вибраного типу
- пошук через Ajax — сторінка не перезавантажується
- випадкові результати, коли немає пошукового запиту (30 шт.)
- збереження/видалення в особистий список (сердечко на картці)
- ручна зміна статусу: new → sent → waiting → rejection → success
- нотатки до кожної позиції (автосейв через 2с або по втраті фокусу)
- копіювання email / телефону / сайту в буфер
- відкриття адреси в Google Maps
- перехід на сторінку оголошення на berufswahl.zh.ch
- реєстрація + логін (сесії)
- фільтр збережених по статусу

## Старт

```bash
git clone https://github.com/EnotSM/SchnupperTracker.git
cd SchnupperTracker

# nix
nix-shell

# або venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python app.py
```

Відкрий http://localhost:5000

## Cтруктура

```
CRUD/
├── app.py                 # увесь бекенд: маршрути, API, кеш
├── config.py              # налаштування
├── templates/
│   ├── base.html          # навігація, flash, footer
│   ├── index.html         # головна: пошук + результати
│   ├── dashboard.html     # збережені зі статусами
│   ├── login.html
│   └── register.html
├── static/
│   ├── app.js             # вся фронтенд логіка
│   └── style.css
└── AGENTS.md              # доки для AI
```

## API роути

| Маршрут | Що робить |
|---------|-----------|
| `/api/save` POST | зберегти оголошення |
| `/api/unsave` POST | видалити по listing_id |
| `/api/save/<id>` DELETE | видалити по DB id |
| `/api/save/<id>/status` PATCH | змінити статус |
| `/api/save/<id>/note` PATCH | зберегти нотатку |

## Нюанси

- `SECRET_KEY` генерується заново при кожному запуску — сесії скидаються після рестарту
- debug mode, немає CSRF
- professions кешуються у файл на 24 години
- випадкові результати кешуються в пам'яті на 5 хвилин
- API timeout 8 секунд

Сайт використовує API [`berufswahl.zh.ch`](https://berufswahl.zh.ch). Не пов'язаний з кантоном Цюрих.
