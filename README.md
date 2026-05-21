# Process Costing Web (MVP)

Облачное web-приложение для расчета производственных процессов, себестоимости и генерации PDF-документов (КП и счет с НДС).

## Что реализовано

- Авторизация пользователей (JWT).
- База операций (`OperationCatalog`) с ручным добавлением и импортом CSV (под выгрузку из Google Sheet БД.ОП).
- Проекты расчета (аналог листа `ЗКЗ`) с 4 диапазонами объема.
- Технические карты по изделиям (`Assembly`, аналоги `КБ1..КБN`).
- Спецификация комплектующих по сборкам (`СПЯ`).
- Групповая спецификация по всем сборкам (`ЗКП`) — агрегируется автоматически.
- Финальный расчет по 4 тиражам (`Кол-во1..Кол-во4`) с:
  - материалами,
  - трудозатратами,
  - операционными расходами,
  - маржинальностью,
  - НДС.
- Генерация PDF:
  - `КП с НДС`
  - `Счет с НДС`.

## Соответствие Google Sheet -> Приложение

- `БД.ОП` -> `OperationCatalog` (`/api/operations`, `/api/operations/import-csv`)
- `ЗКЗ` -> `CalculationProject` + `Assembly` с `qty_tier_1..4`
- `СПЯ` -> `ComponentSpec` (`/api/assemblies/{id}/components`)
- `ЗКП` -> `grouped_components` в `/api/projects/{id}/calculation`
- `КБ1..КБN` -> `Assembly` + `RouteStep` (`/api/assemblies/{id}/route-steps`)
- `Кол-во1..4` -> `assemblies[].tiers[]` в результате расчета
- `КП с НДС` -> `/api/projects/{id}/pdf/offer?tier=1..4`
- `Счет с НДС` -> `/api/projects/{id}/pdf/invoice?tier=1..4`

## Запуск локально

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Открыть в браузере: `http://127.0.0.1:8000`

Swagger API: `http://127.0.0.1:8000/docs`

## Запуск на Windows 11 + Google Chrome

### Вариант 1: одним кликом (BAT)

```bat
scripts\windows\start.bat
```

Что делает скрипт:

1. Создает `.venv` (если ее нет)
2. Ставит зависимости
3. Создает `.env` из `.env.example`
4. Открывает `http://127.0.0.1:8000` в Google Chrome
5. Стартует backend

### Вариант 2: PowerShell (гибкий)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start.ps1
```

Полезные флаги:

```powershell
# Не открывать браузер
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start.ps1 -NoBrowser

# Пропустить повторную установку зависимостей
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start.ps1 -SkipInstall

# Запуск на другом порту
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start.ps1 -Port 8080
```

Если Chrome не установлен, скрипт откроет адрес в браузере по умолчанию.

## Структура проекта

```text
app/
  main.py                  # FastAPI endpoints
  database.py              # DB config and session
  models.py                # SQLModel entities
  schemas.py               # API schemas
  security.py              # auth helpers
  services/
    calculations.py        # pricing and aggregation logic
    pdf_builder.py         # PDF generation
  static/index.html        # simple demo frontend
tests/
  test_calculations.py
```

## Пример импорта операций (CSV)

Поддерживаются колонки:

- `group_code`, `operation_name`, `unit`, `minutes_per_cycle`, `rate_per_hour`
- или русские аналоги: `Группа`, `Операция`, `Ед`, `Минуты`, `Ставка_час`

## Дальше для production

1. Перейти с SQLite на PostgreSQL.
2. Добавить роли (менеджер/технолог/админ) и разграничение доступа между организациями.
3. Добавить версионирование расчетов и историю изменений.
4. Подключить прямую синхронизацию с Google Sheets API (по сервисному аккаунту).
5. Добавить шаблоны печати КП/счета с фирменным стилем и реквизитами.