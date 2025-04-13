import logging
from pathlib import Path
import re
import sys
from typing import List, Tuple, Optional

import yaml

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

NOTES_DIRECTORY = Path("/mnt/c/Users/sterx/knowledge-base")
FILE_NAME_PATTERN = r"^Книга.*\.md$"


class YamlBlockNotFound(Exception):
    """Исключение, сигнализирующее о том, что YAML-блок не найден в содержимом файла."""

    pass


def update_yaml_field(data: dict) -> dict:
    """
    Обновляет одно yaml поле — кастомная логика. Можно просто вывести все значения
    этого поля или изменить эти значения — все или некоторые.
    """
    updated_data = dict(data)
    print(updated_data)
    """
    if not updated_data.get("Progress"):
        updated_data["Progress"] = "<p><progress max=0 value=0></progress></p>"
    """
    return updated_data


def list_note_files(directory: Path) -> List[Path]:
    """
    Отбирает файлы в указанной директории, имена которых соответствуют регулярному выражению.
    Регулярное выражение определяется константой FILE_NAME_PATTERN.

    :param directory: Путь к директории с файлами.
    :return: Список объектов Path, соответствующих найденным файлам.
    """
    return [
        file_path
        for file_path in directory.iterdir()
        if file_path.is_file() and re.match(FILE_NAME_PATTERN, file_path.name)
    ]


def find_yaml_block_indices(content: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Ищет в содержимом файла первый YAML-блок, определяемый как блок,
    обрамлённый строками '---'.


    :param content: Содержимое файла в виде строки.
    :return: Кортеж (start_index, end_index), где start_index — индекс первой строки с '---',
             а end_index — индекс следующей строки с '---'.
             Если блок не найден, возвращается (None, None).
    """
    lines = content.splitlines()

    start_index = None
    end_index = None

    for idx, line in enumerate(lines):
        if line.strip() == "---":
            start_index = idx
            break

    if start_index is None:
        return None, None

    for idx in range(start_index + 1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    return start_index, end_index


def extract_yaml_data(content: str) -> Tuple[dict, int, int]:
    """

    Ищет YAML-блок во всём содержимом файла, используя функцию
    find_yaml_block_indices, и парсит его в словарь.

    Если YAML-блок не найден, генерируется исключение YamlBlockNotFound.

    :param content: Исходное содержимое файла.
    :return: Кортеж (data, start_index, end_index), где data — словарь с данными YAML.
    """
    lines = content.splitlines()
    start_index, end_index = find_yaml_block_indices(content)

    if start_index is None or end_index is None:
        raise YamlBlockNotFound(
            "YAML блок не найден или отсутствует закрывающий разделитель."
        )

    yaml_lines = lines[start_index + 1 : end_index]
    yaml_text = "\n".join(yaml_lines)
    try:
        data = yaml.safe_load(yaml_text)
        return data, start_index, end_index
    except Exception as e:
        logging.error(f"Ошибка при парсинге YAML: {e}")
        raise e


def build_updated_content(
    content: str, start_index: int, end_index: int, updated_yaml: str
) -> str:
    """
    Собирает новое содержимое файла на основе исходных строк, обновленного YAML-блока,
    а также заданных индексов начала и конца YAML блока.

    :param lines: Список строк исходного содержимого файла.
    :param start_index: Индекс строки, где начинается YAML блок.
    :param end_index: Индекс строки, где заканчивается YAML блок.
    :param updated_yaml: Обновленный YAML блок в виде строки.
    :return: Новое содержимое файла в виде строки.
    """
    lines = content.splitlines()
    new_content_lines = []
    new_content_lines.extend(lines[:start_index])
    new_content_lines.append("---")
    new_content_lines.extend(updated_yaml.splitlines())
    new_content_lines.append("---")
    new_content_lines.extend(lines[end_index + 1 :])
    return "\n".join(new_content_lines)


def update_yaml_content(content: str) -> str:
    """
    Обновляет YAML-блок в содержимом файла, заменяя значение указанного поля,
    и возвращает новое содержимое файла. Если YAML-блок не найден или не удаётся его обработать,
    возвращается исходное содержимое.

    :param content: Исходное содержимое файла.

    :param field: Имя поля для обновления.
    :param new_value: Новое значение для поля.
    :return: Новое содержимое файла.
    """
    try:
        data, start_index, end_index = extract_yaml_data(content)
    except YamlBlockNotFound as e:
        logging.error(e)
        return content
    except Exception:
        return content

    if not isinstance(data, dict):
        logging.error("YAML блок не является словарем.")

        return content

    data = update_yaml_field(data)
    updated_yaml = yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip()
    return build_updated_content(content, start_index, end_index, updated_yaml)


def process_file(file_path: Path) -> None:
    """
    Обрабатывает один файл:
    - Читает его содержимое.
    - Обновляет YAML-блок (если найден).
    - Перезаписывает файл, если содержимое изменилось.

    :param file_path: Объект Path, представляющий путь к файлу.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {file_path}: {e}")
        return

    updated_content = update_yaml_content(content)

    if updated_content != content:
        try:
            file_path.write_text(updated_content, encoding="utf-8")
            logging.info(f"Файл {file_path} успешно обновлён.")
        except Exception as e:
            logging.error(f"Ошибка при записи файла {file_path}: {e}")


def main() -> None:
    """
    Основная функция:
    1. Получает список файлов из директории.
    2. Обрабатывает каждый файл, обновляя нужное метаполе в YAML-блоке.
    """
    file_paths = list_note_files(NOTES_DIRECTORY)
    for file_path in file_paths:
        process_file(file_path)


if __name__ == "__main__":
    main()
