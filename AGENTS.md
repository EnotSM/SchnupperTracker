# SchnupperTracker — Проєктна документація для ШІ

## Огляд
Flask-застосунок для пошуку та відстеження учнівських практик (Schnupperlehren) та навчальних місць (Lehrstellen) у кантоні Цюрих. Використовує API `berufswahl.zh.ch`.

## Технічний стек
- **Backend**: Python Flask (монолітний `app.py`), SQLite
- **Frontend**: Jinja2 + Tailwind CSS (CDN) + Vanilla JS (IIFE в `static/app.js`)
- **API**: WordPress JSON API (`admin.berufswahlportal.ch/wp-json/biz/v1`)
- **Dev**: Python 3.11, `nix-shell` або `venv`

## Файлова структура (важливі файли)
```
CRUD/
├── app.py                    # Весь Flask-бекенд (маршрути, логіка, API, кеш)
├── config.py                 # Конфігурація (секретний ключ, URL API, кеш)
├── templates/
│   ├── base.html             # Базовий шаблон (навігація, flash, footer)
│   ├── index.html            # ГОЛОВНА сторінка (пошук + результати)
│   ├── login.html
│   ├── register.html
│   └── dashboard.html        # Збережені анкети користувача (CRUD)
├── static/
│   ├── app.js                # ВСЯ фронтенд-логіка
│   └── style.css             # Кастомні стилі
├── AGENTS.md                 # Цей файл (нотатки для ШІ)
└── requirements.txt          # flask, requests, werkzeug
```

## Маршрути (routes)
| Маршрут | Метод | Призначення |
|---------|-------|-------------|
| `/` | GET | Головна сторінка: пошук + випадкові результати |
| `/register` | GET/POST | Реєстрація (username >= 3 символи, password >= 6) |
| `/login` | GET/POST | Логін (сесія) |
| `/logout` | GET | Вихід |
| `/dashboard` | GET | Збережені анкети з фільтром за статусом |
| `/api/save` | POST | Зберегти анкету |
| `/api/unsave` | POST | Видалити збережену за listing_id |
| `/api/save/<id>` | DELETE | Видалити за DB id |
| `/api/save/<id>/status` | PATCH | Оновити статус (new/sent/waiting/rejection/success) |
| `/api/save/<id>/note` | PATCH | Оновити нотатку |
| `/api/save/<id>/mute` | PATCH | Увімкнути/вимкнути muted |

## Логіка Type Radio (ВАЖЛИВО — фіксили баги)
- **Радіо кнопки** (Schnupperlehre / Lehrstelle) на головній сторінці (`index.html`)
- При кліку: тільки візуальна зміна (checked/unchecked). **НІЯКОГО fetch/reload**
- При повторному кліку на вибране радіо: знімається вибір (custom deselect логіка)
- **Search button** — єдиний спосіб оновити список результатів

### Як працює deselect (важливий нюанс)
```javascript
// В index.html inline script
label.addEventListener('mousedown', function() {
    wasChecked = radio.checked;  // запам'ятовуємо ДО зміни checked
});
label.addEventListener('click', function(e) {
    if (wasChecked) {
        e.preventDefault();
        radio.checked = false;   // деселект
        window.SELECTED_TYPE = '';
        // ... оновлення dropdown професій
    }
});
```
**Чому не `click` напряму**: клік на `<input>` спочатку чекне радіо (browser default behavior), потім подія спливе до `<label>`. Якщо перевіряти `radio.checked` у click-хендлері label — радіо ВЖЕ checked, і деселект не спрацює правильно.

### Radio change handler в app.js
```javascript
// UPDATE SELECTED_TYPE для фільтрації dropdown професій, БЕЗ fetch
radio.addEventListener("change", function () {
    window.SELECTED_TYPE = this.value;
    // оновлюємо dropdown професій
});
```

### Search button handler
```javascript
searchForm.addEventListener("submit", function (e) {
    e.preventDefault();
    // Якщо нічого не вибрано → "/"
    // Інакше → FormData → AJAX fetch
});
```
Натискання Search — **єдиний** спосіб оновити список:
- Без типу: мікс 15 Schnupper + 15 Lehrstelle
- З типом (без професії/локації): 30 випадкових обраного типу
- З професією/локацією: пошук з фільтром за типом

## Кешування для швидкості
### 1. Professions cache (`config.py`)
- `CACHE_DURATION = 86400` (24 години)
- Файл `professions_cache.json` (автоматично .gitignore)
- Оновлюється при застаріванні або відсутності файлу
- 2 API-виклики при оновленні: `apprenticeship-professions` + `professions`

### 2. Result cache (`app.py`)
- In-memory dict `_result_cache`
- `RESULT_CACHE_TTL = 300` (5 хвилин)
- Ключі: `"v1_schnupper"`, `"v1_lehrstelle"`, `"v1_mixed"`
- Кешується random fallback (не кешується пошук з професією/локацією)
- **Version prefix** `"v1_"` для автоматичної інвалідації при зміні формату

### 3. API timeout
- `timeout=8` секунд (зменшено з 15)

## Бази даних
- `schnupper_tracker.db` — основна БД (SQLite, WAL mode, foreign keys ON)
- Таблиці: `users`, `saved_listings`
- `saved_listings.status`: new, sent, waiting, rejection, success
- `saved_listings.muted`: 0/1 (візуальне затемнення)

## Важливі нюанси
1. `SECRET_KEY` генерується через `secrets.token_hex(32)` при кожному старті → сесії скидаються при перезапуску
2. Debug mode ON: `app.run(host="0.0.0.0", port=5000, debug=True)`
3. Немає CSRF захисту
4. В формі є 2 поля: `profession` (multi-select теги) та `location` (текст)
5. `SELECTED_TYPE` використовується для фільтрації професій у випадаючому списку
6. `query_params.get("type", "")` визначає checked стан радіо кнопок
7. AJAX форма замінює тільки `#results-region`, форма і радіо залишаються незмінними

## Типові помилки при роботі
- **Радіо не змінюється при кліку**: перевірити `mousedown`/`click` логіку в index.html
- **Список оновлюється без Search**: перевірити `app.js` — в `change` хендлері радіо не має бути `fetch`
- **Сторінка перезавантажується**: перевірити `window.location.href` — їх не має бути в JS/HTML
- **Professions не оновлюються**: видалити `professions_cache.json`

## Команди для запуску
```bash
# Nix shell
nix-shell

# Або вручну
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
