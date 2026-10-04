# Дашборд продаж

Проект живёт в карточке вольта `~/SecondBrain/60-projects/finansy-hh-career.md` (блоки `## STATE` и `## ПРАВИЛА`). Здесь только техника; правила сюда не копировать.

## Что где

- `index.html` - оболочка: вёрстка и отрисовка, цифр внутри нет.
- `data.js` - все данные, собирается генератором. Руками не править.
- `generator/build_data.py` собирает `data.js` из двух CSV, `generator/verify_data.py` сверяет источники. `generator/insights.json` - «Выводы месяца», единственный ручной вход.
- `generator/_legacy/` - старая схема, не запускать. Подробности - `generator/README.md`.

## Обновить локально

```bash
cd generator
curl -sL "https://docs.google.com/spreadsheets/d/1rW2eTi6WAfNMsM2w_40DS0cMo58SwGtDvWU8vvZCqe8/export?format=csv&gid=0" -o svod.csv
curl -sL "https://docs.google.com/spreadsheets/d/1SWX2-_K6q2mbldHgXwO-HjMKUD037mjwVmlMXzIy7dw/export?format=csv&gid=246856888" -o fakt.csv
python3 build_data.py && python3 verify_data.py
```

Проверить вид: открыть `index.html` в браузере. Штатный путь - скилл `/update-dashboard` (то же плюс черновик выводов и проверка боевой страницы).

## Выкладка

Коммит `data.js` и `git push` в `main` - GitHub Pages обновится сам: https://osokhneva-debug.github.io/sales-dashboard-q1-2026/

Автоматика 5-го числа, два независимых пути:
- GitHub Action `.github/workflows/update.yml` в 06:00 UTC: только цифры, без выводов;
- задача `dashboard-update` на сервере `assistant-hel` (`~/.claude/scripts/dashboard-update.sh`, headless Claude): цифры, проверка страницы и отчёт в Telegram. `DASH_DRY=1` - прогон без публикации. Лог: `~/.claude/logs/dashboard-update.log`.

## Данные

Своих данных на сервере нет: источник - две Google-таблицы выше (выгрузка CSV по ссылке). Расчёты и выводы - в `~/Projects/hh-analytics`.
