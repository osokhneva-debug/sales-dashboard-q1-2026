# Генератор дашборда

Данные и оформление разделены (схема с 11.07.2026):

- `../index.html` — **оболочка**: вёрстка + JS-отрисовка, цифр внутри нет. Меняется только когда меняем дизайн/логику отображения.
- `../data.js` — **все данные** (константы `DATA`, `DRILLDOWN`, `PARTNERS`, `STREAMS`, `TAGSTATS`, `INSIGHTS_LOG`). Пересобирается при каждом обновлении. Никогда не редактировать руками.
- `insights.json` — журнал «Выводы месяца» (новые сверху). Единственный ручной вход; попадает в `data.js` при сборке.

## Обновление данных

```bash
cd generator
curl -sL "https://docs.google.com/spreadsheets/d/1rW2eTi6WAfNMsM2w_40DS0cMo58SwGtDvWU8vvZCqe8/export?format=csv&gid=0" -o svod.csv
curl -sL "https://docs.google.com/spreadsheets/d/1SWX2-_K6q2mbldHgXwO-HjMKUD037mjwVmlMXzIy7dw/export?format=csv&gid=246856888" -o fakt.csv
python3 build_data.py    # -> ../data.js
python3 verify_data.py   # sanity: svod vs fakt (CPA до рубля), месяцы, непустые структуры
```

Потом коммит `data.js` → GitHub Pages обновится сам.

## Источники (CSV-export, доступ «по ссылке»)
- Продажи: `1rW2eTi6WAfNMsM2w_40DS0cMo58SwGtDvWU8vvZCqe8` gid=0 («Сводная всех месяцев»)
- Выручка потоков: `1SWX2-_K6q2mbldHgXwO-HjMKUD037mjwVmlMXzIy7dw` gid=246856888 («Факт2025-2026»)

## Автоматика
- GitHub Action `.github/workflows/update.yml`: 3-го числа каждого месяца + ручной запуск (Actions → Monthly dashboard update → Run workflow). Делает ровно те же 4 шага и коммитит `data.js`.
- Локально из Claude Code: скилл `/update-dashboard` (то же + черновик выводов месяца + проверка страницы).

## Бизнес-правила в build_data.py
- Канон школ (`CANON`): EN/RU-дубли слиты (Эдюсон, МБА, City Business School).
- Каждая продажа в GMV-статистике тегов относится либо к профессии, либо к навыку (без двойного счёта).
- Заголовок/период страницы строится в браузере из `DATA.months` — руками не трогать.

## _legacy/
Старая схема (5 скриптов-патчеров + `template.html` с зашитыми данными). Оставлена для истории, не запускать.
