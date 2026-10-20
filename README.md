# 🌐 Polyglot Linguist Generator

Скрипт для автоматической генерации сбалансированного репозитория на всех языках, распознаваемых **GitHub Linguist**.

## 📌 Особенности

1. **Актуальная база языков**: Автоматически скачивает свежий `languages.yml` из официального репозитория [`github-linguist/linguist`](https://github.com/github-linguist/linguist).
2. **Все доступные расширения**: Для каждого языка с полем `extensions` создается отдельный файл в `polyglot_repo/src/` с его первым зарегистрированным расширением.
3. **Идеальный баланс (500 байт)**: Каждый файл весит ровно 500 байт UTF-8 текста, гарантируя равномерное процентное распределение в статистике GitHub Linguist.
4. **Кроссплатформенная безопасность**: Корректная обработка запрещенных символов Windows, Linux и macOS (`< > : " / \ | ? *`, управляющие символы и системные имена `CON`, `PRN`, `AUX`, `NUL` и др.).
5. **Красивый консольный вывод**: Динамический индикатор прогресса (progress bar) с процентами и названиями текущих языков.
6. **Готовая конфигурация Linguist**: Автоматическое создание `.gitattributes` с директивой `src/* linguist-detectable=true` для гарантированного учета всех языков.

---

## 🛠️ Установка зависимостей

```bash
pip install pyyaml requests
```

---

## 🚀 Запуск скрипта

### Стандартный запуск (все языки с extensions, 789 файлов):
```bash
python3 generate_polyglot.py
```

### Только языки программирования (`type: programming`, 549 файлов):
```bash
python3 generate_polyglot.py --programming-only
```

### Дополнительные параметры:
- `-o, --output` — путь к целевой папке (по умолчанию: `polyglot_repo`)
- `--bytes` — точный размер каждого файла в байтах (по умолчанию: `500`)
- `--url` — альтернативный URL для скачивания `languages.yml`

---

## 📤 Как опубликовать папку на GitHub

1. Перейдите в созданную папку:
   ```bash
   cd polyglot_repo
   ```

2. Инициализируйте Git и переименуйте ветку в `main`:
   ```bash
   git init
   git branch -M main
   ```

3. Закоммитьте файлы:
   ```bash
   git add .
   git commit -m "feat: initial polyglot linguist repository"
   ```

4. Привяжите ваш удаленный репозиторий:
   ```bash
   git remote add origin https://github.com/<USERNAME>/<REPO_NAME>.git
   ```

5. Отправьте на GitHub:
   ```bash
   git push -u origin main
   ```
