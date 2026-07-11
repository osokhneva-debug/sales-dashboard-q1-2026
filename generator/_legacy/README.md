# Генератор дашборда

Пересобирает `../index.html` из живых Google-таблиц.

## Пайплайн (по порядку)
1. `build.py` — CPA-детализация из «Сводной всех месяцев» (CSV-export), каноника школ, TAGSTATS (GMV проф/навыки). Пишет `template.html` → `index_new.html`.
2. `build_streams2.py` — таб «Обзор» (4 потока из «Факт2025-2026»), KPI, кварталы, накопит.итог, GMV-таблица, таб «Выводы» из `insights.json`, переименование табов.
3. `build_extras.py` — CSV-выгрузка + полная высота таблиц.
4. `build_drilldown.py` — вкладка «Просадки»: MoM+QoQ, Total-направление, инсайты, «фатальные» курсы, фикс графика школ.
5. `build_deltas.py` — единые MoM+QoQ во всех таблицах + KPI.

## Источники (CSV-export, доступ «по ссылке»)
- Продажи: `1rW2eTi6WAfNMsM2w_40DS0cMo58SwGtDvWU8vvZCqe8` gid=0 («Сводная всех месяцев»)
- Выручка потоков: `1SWX2-_K6q2mbldHgXwO-HjMKUD037mjwVmlMXzIy7dw` gid=246856888 («Факт2025-2026»)

## Как гонять
`curl` двух CSV → `svod.csv`/`fakt.csv`, затем `python3 build.py && build_streams2.py && build_extras.py && build_drilldown.py && build_deltas.py`, потом `cp index_new.html ../index.html`.

`insights.json` — журнал «Выводы месяца» (дописывать новый месяц сверху).
