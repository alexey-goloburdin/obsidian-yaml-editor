Простейший скрипт просмотра и массового изменения YAML-метаданных в заметках Obsidian — `main.py`.

Запуск:

```bash
uv python main.py
```

Скрипт писал на скорую руку для себя, переиспользовать можно только после изучения.

`NOTES_DIRECTORY` — директория с заметками (md-файлами).

`update_yaml_field` — основная Python-функция, которая тебе вероятно понадобится, можешь в ней вывести значения YAML-полей с метаданными или изменять их.

Выбираются сейчас только заметки, начинающиеся со слова «Книга». Шаблон для имени выбираемых файлов задаётся в `FILE_NAME_PATTERN`.
