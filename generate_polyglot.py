#!/usr/bin/env python3
"""
Polyglot Repository Generator for GitHub Linguist
==================================================
Автоматически скачивает languages.yml из репозитория github-linguist/linguist
и создает файлы размером ровно по 500 байт для каждого языка программирования.

Установка зависимостей:
    pip install pyyaml requests
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
import requests
import yaml

LINGUIST_LANGUAGES_URL = (
    "https://raw.githubusercontent.com/github-linguist/linguist/master/lib/linguist/languages.yml"
)
TARGET_FILE_SIZE = 500  # байт


def sanitize_filename(name: str) -> str:
    """
    Очищает и нормализует имя файла для совместимости с Windows, Linux и macOS.
    - Заменяет недопустимые символы (< > : " / \\ | ? * и управляющие ASCII 0-31) на '_'.
    - Удаляет завершающие пробелы и точки (критично для файловой системы Windows).
    - Защищает от зарезервированных системных имен Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9).
    """
    # Заменяем запрещенные символы
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # Удаляем концевые точки и пробелы
    sanitized = sanitized.strip(". ")

    # Проверка на системные зарезервированные имена Windows
    windows_reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if sanitized.upper() in windows_reserved:
        sanitized = f"{sanitized}_lang"

    return sanitized or "language"


def generate_exact_bytes_content(language_name: str, target_bytes: int = TARGET_FILE_SIZE) -> bytes:
    """
    Генерирует ровно target_bytes байт валидного UTF-8 текста.
    Включает комментарий с именем языка, читаемые строки и точный байтовый паддинг.
    """
    clean_name = language_name.replace("\r", " ").replace("\n", " ").strip()
    header = f"// Language: {clean_name}\n".encode("utf-8")

    if len(header) >= target_bytes:
        return header[: target_bytes - 1] + b"\n"

    line = f"// GitHub Linguist test file for {clean_name}\n".encode("utf-8")
    data = bytearray(header)

    while len(data) + len(line) <= target_bytes - 1:
        data.extend(line)

    remaining = target_bytes - len(data)
    if remaining == 1:
        data.extend(b"\n")
    elif remaining == 2:
        data.extend(b"#\n")
    else:
        # remaining >= 3: '//' + '=' * (remaining - 3) + '\n'
        pad = b"//" + b"=" * (remaining - 3) + b"\n"
        data.extend(pad)

    if len(data) != target_bytes:
        raise ValueError(f"Размер содержимого {len(data)} не равен ожидаемым {target_bytes} байт")

    return bytes(data)


def render_progress_bar(current: int, total: int, lang_name: str, width: int = 30) -> None:
    """Выводит динамическую полосу прогресса в консоль."""
    if total == 0:
        return
    fraction = current / total
    filled = int(width * fraction)
    bar = "█" * filled + "░" * (width - filled)
    percent = fraction * 100
    display_lang = (lang_name[:18] + "..") if len(lang_name) > 20 else lang_name.ljust(20)
    msg = f"\r\033[1;36m[{bar}]\033[0m {percent:5.1f}% ({current}/{total}) \033[33m{display_lang}\033[0m"
    sys.stdout.write(msg)
    sys.stdout.flush()


def download_languages_yml(url: str = LINGUIST_LANGUAGES_URL) -> dict:
    """Скачивает и парсит актуальный languages.yml с GitHub."""
    print(f"\033[1;34m[↓]\033[0m Скачивание languages.yml с {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PolyglotRepoGenerator/1.0)",
        "Accept": "text/yaml,text/plain,*/*",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    print(f"\033[1;32m[✓]\033[0m Файл успешно загружен ({len(response.content):,} байт). Парсинг YAML...")
    data = yaml.safe_load(response.content)
    if not isinstance(data, dict):
        raise ValueError("Некорректная структура languages.yml: ожидался словарь на верхнем уровне.")
    print(f"\033[1;32m[✓]\033[0m Успешно загружено описаний языков: {len(data):,}")
    return data


def print_git_instructions(repo_dir: Path) -> None:
    """Печатает подробную инструкцию по публикации в Git/GitHub."""
    instructions = f"""
\033[1;32m================================================================================\033[0m
\033[1;37m🚀 ИНСТРУКЦИЯ: КАК ОПУБЛИКОВАТЬ РЕПОЗИТОРИЙ НА GITHUB\033[0m
\033[1;32m================================================================================\033[0m

1. Перейдите в созданную папку репозитория:
   \033[1;33mcd {repo_dir.name}\033[0m

2. Инициализируйте новый локальный Git-репозиторий:
   \033[1;33mgit init\033[0m

3. Переименуйте ветку по умолчанию в main:
   \033[1;33mgit branch -M main\033[0m

4. Добавьте сгенерированные файлы и сделайте коммит:
   \033[1;33mgit add .\033[0m
   \033[1;33mgit commit -m "feat: initial polyglot linguist repository with balanced languages"\033[0m

5. Создайте новый пустой репозиторий на GitHub и привяжите его remote:
   \033[1;33mgit remote add origin https://github.com/<ВАШ_АККАУНТ>/<ИМЯ_РЕПОЗИТОРИЯ>.git\033[0m

6. Отправьте ветку на GitHub:
   \033[1;33mgit push -u origin main\033[0m

\033[1;36m💡 Совет по GitHub Linguist:\033[0m
   В папку уже добавлен файл \033[1m.gitattributes\033[0m с директивой:
   \033[33msrc/* linguist-detectable=true\033[0m
   Благодаря одинаковому размеру каждого файла ({TARGET_FILE_SIZE} байт) и этой директиве,
   Linguist распознает все созданные языки и равномерно распределит проценты!
\033[1;32m================================================================================\033[0m
"""
    print(instructions)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Генератор Polyglot репозитория со всеми языками из GitHub Linguist"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="polyglot_repo",
        help="Путь к создаваемой папке (по умолчанию: polyglot_repo)",
    )
    parser.add_argument(
        "--programming-only",
        action="store_true",
        help="Создавать файлы только для языков с type: 'programming' (без data, markup, prose)",
    )
    parser.add_argument(
        "--bytes",
        type=int,
        default=TARGET_FILE_SIZE,
        help=f"Размер каждого файла в байтах (по умолчанию: {TARGET_FILE_SIZE})",
    )
    parser.add_argument(
        "--url",
        default=LINGUIST_LANGUAGES_URL,
        help="URL к raw languages.yml",
    )

    args = parser.parse_args()

    # 1. Скачиваем languages.yml
    try:
        languages_data = download_languages_yml(args.url)
    except Exception as e:
        print(f"\033[1;31m[✗] Ошибка при загрузке languages.yml: {e}\033[0m", file=sys.stderr)
        sys.exit(1)

    # 2. Фильтруем языки с полем extensions
    eligible_languages = []
    for lang_name, lang_info in languages_data.items():
        if not isinstance(lang_info, dict):
            continue
        # Проверяем наличие непустого списка extensions
        extensions = lang_info.get("extensions")
        if not extensions or not isinstance(extensions, list):
            continue

        if args.programming_only and lang_info.get("type") != "programming":
            continue

        first_ext = extensions[0]
        if not first_ext.startswith("."):
            first_ext = f".{first_ext}"

        eligible_languages.append((lang_name, first_ext, lang_info))

    total = len(eligible_languages)
    filter_desc = "только type: programming" if args.programming_only else "все с полем extensions"
    print(f"\033[1;34m[i]\033[0m Режим фильтрации: {filter_desc}")
    print(f"\033[1;34m[i]\033[0m Отобрано языков для создания файлов: \033[1;37m{total}\033[0m")

    # 3. Подготавливаем директории polyglot_repo/src/
    repo_dir = Path(args.output).resolve()
    src_dir = repo_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Создаем .gitattributes, чтобы Linguist обязательно учитывал все файлы в статистике
    gitattributes_path = repo_dir / ".gitattributes"
    gitattributes_content = (
        "# GitHub Linguist configuration\n"
        "# Mark all files in src/ as detectable code to guarantee inclusion in language statistics\n"
        "src/* linguist-detectable=true\n"
    )
    with open(gitattributes_path, "w", encoding="utf-8") as f:
        f.write(gitattributes_content)

    print(f"\033[1;34m[i]\033[0m Целевая папка: \033[1m{src_dir}\033[0m")
    print(f"\033[1;34m[i]\033[0m Генерация файлов по {args.bytes} байт...")

    start_time = time.time()
    generated_count = 0
    errors = []

    # 4. Создаем файлы с прогресс-баром
    for idx, (lang_name, ext, _) in enumerate(eligible_languages, start=1):
        safe_name = sanitize_filename(lang_name)
        filename = f"{safe_name}{ext}"
        filepath = src_dir / filename

        try:
            content = generate_exact_bytes_content(lang_name, target_bytes=args.bytes)
            with open(filepath, "wb") as f:
                f.write(content)
            generated_count += 1
        except OSError as os_err:
            # Резервный вариант на случай ограничений конкретной ОС
            try:
                fallback_name = f"lang_{idx}{ext}"
                fallback_path = src_dir / fallback_name
                with open(fallback_path, "wb") as f:
                    f.write(content)
                generated_count += 1
            except Exception as e2:
                errors.append((lang_name, f"{os_err} | fallback error: {e2}"))
        except Exception as e:
            errors.append((lang_name, str(e)))

        render_progress_bar(idx, total, lang_name)

    elapsed = time.time() - start_time
    print()  # Перенос строки после progress bar

    # 5. Итоги
    print(f"\n\033[1;32m[✓] Завершено за {elapsed:.2f} сек!\033[0m")
    print(f"    • Успешно сгенерировано файлов: \033[1;32m{generated_count:,}\033[0m из \033[1m{total:,}\033[0m")
    print(f"    • Размер каждого файла: \033[1m{args.bytes} байт\033[0m")
    print(f"    • Общий размер: \033[1m{generated_count * args.bytes:,} байт\033[0m")

    if errors:
        print(f"\033[1;33m[!] Ошибок при создании файлов ({len(errors)}):\033[0m")
        for err_lang, err_msg in errors[:5]:
            print(f"    - {err_lang}: {err_msg}")
        if len(errors) > 5:
            print(f"    ... и еще {len(errors) - 5} ошибок.")

    # 6. Инструкция по Git
    print_git_instructions(repo_dir)


if __name__ == "__main__":
    main()
