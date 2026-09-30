import torch
import re
import numpy as np
import wave
import tkinter as tk
import unicodedata
import html

# ===== НАСТРОЙКИ =====
voice = 'kseniya'          # голос
sample_rate = 48000
max_chunk_chars = 350      # макс. символов в одном фрагменте
speed = 'x-slow'             # скорость речи: 'x-slow', 'slow', 'medium', 'fast', 'x-fast'

# ===== ФУНКЦИЯ ЗАМЕНЫ ЦИФР НА СЛОВА =====
def replace_digits_with_words(text: str) -> str:
    digit_map = {
        '0': ' ноль ',
        '1': ' один ',
        '2': ' два ',
        '3': ' три ',
        '4': ' четыре ',
        '5': ' пять ',
        '6': ' шесть ',
        '7': ' семь ',
        '8': ' восемь ',
        '9': ' девять '
    }
    result = []
    for ch in text:
        if ch in digit_map:
            result.append(digit_map[ch])
        else:
            result.append(ch)
    return ''.join(result)

# ===== ОБНОВЛЁННАЯ ФУНКЦИЯ ЗАМЕНЫ ЛАТИНСКИХ БУКВ =====
def replace_latin_letters(text: str) -> str:
    # Таблица для строчных букв и для заглавных, после которых идёт строчная латинская
    latin_map_lower = {
        'a': 'а', 'b': 'б', 'c': 'ч', 'd': 'д', 'e': 'э',
        'f': 'ф', 'g': 'г', 'h': 'х', 'i': 'и', 'j': 'дж',
        'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
        'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т',
        'u': 'у', 'v': 'в', 'w': 'в', 'x': 'кс', 'y': 'ы', 'z': 'з'
    }
    # Таблица для заглавных букв (английские названия) — все остальные случаи
    latin_map_upper_name = {
        'A': ' Эй ', 'B': ' Би ', 'C': ' Си ', 'D': ' Ди ', 'E': ' И ',
        'F': ' Эф ', 'G': ' Джи ', 'H': ' Эйч ', 'I': ' Ай ', 'J': ' Джей ',
        'K': ' Кей ', 'L': ' Эл ', 'M': ' Эм ', 'N': ' Эн ', 'O': ' Оу ',
        'P': ' Пи ', 'Q': ' Кью ', 'R': ' Ар ', 'S': ' Эс ', 'T': ' Ти ',
        'U': ' Ю ', 'V': ' Ви ', 'W': ' Дабл-Ю ', 'X': ' Экс ', 'Y': ' Уай ', 'Z': ' Зед '
    }

    result = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]

        if 'a' <= ch <= 'z':
            # Строчная латинская — старая таблица
            result.append(latin_map_lower.get(ch, ch))

        elif 'A' <= ch <= 'Z':
            # Заглавная латинская — проверяем следующий символ
            next_is_lower_latin = False
            if i + 1 < length and 'a' <= text[i + 1] <= 'z':
                next_is_lower_latin = True

            if next_is_lower_latin:
                # Сразу после заглавной идёт строчная латинская → старая таблица
                result.append(latin_map_lower.get(ch.lower(), ch))
            else:
                # Во всех остальных случаях → новая таблица (английское название)
                result.append(latin_map_upper_name.get(ch, ch))
        else:
            result.append(ch)

        i += 1

    return ''.join(result)

# ===== ФУНКЦИЯ ЗАМЕНЫ ГРЕЧЕСКИХ БУКВ =====
def replace_greek_letters(text: str) -> str:
    # Замена пробелов между двумя греческими буквами на ","
    text = re.sub(r'([\u0370-\u03FF]) +([\u0370-\u03FF])', r'\1,\2', text)
    greek_map = {
        'α': ' альфа ', 'β': ' бета ', 'γ': ' гамма ', 'δ': ' дельта ',
        'ε': ' эпсилон ', 'ζ': ' дзета ', 'η': ' эта ', 'θ': ' тета ',
        'ι': ' йота ', 'κ': ' каппа ', 'λ': ' лямбда ', 'μ': ' мю ',
        'ν': ' ню ', 'ξ': ' кси ', 'ο': ' омикрон ', 'π': ' пи ',
        'ρ': ' ро ', 'σ': ' сигма ', 'ς': ' сигма ', 'τ': ' тау ',
        'υ': ' ипсилон ', 'φ': ' фи ', 'χ': ' хи ', 'ψ': ' пси ',
        'ω': ' омега '
    }
    result = []
    for ch in text:
        lower_ch = ch.lower()
        if lower_ch in greek_map:
            result.append(greek_map[lower_ch])
        else:
            result.append(ch)
    return ''.join(result)

# ===== ФУНКЦИЯ ЗАМЕНЫ СКОБОК И КАВЫЧЕК НА ";" =====
def replace_brackets_and_quotes(text: str) -> str:
    brackets_and_quotes = r'[()[]{}<>"\'«»„“`‛]'
    return re.sub(brackets_and_quotes, ';', text)

# ===== ЗАМЕНА ПРОЧИХ НЕДОПУСТИМЫХ СИМВОЛОВ НА ПРОБЕЛ =====
def replace_other_symbols(text: str) -> str:
    allowed = r'[^\w.,!?;:-\—–]'
    result = re.sub(allowed, ' ', text)
    return result

# ===== УДАЛЕНИЕ УПРАВЛЯЮЩИХ СИМВОЛОВ =====
def remove_control_characters(text: str) -> str:
    control_chars = ''.join(chr(c) for c in range(32) if c not in (9, 10, 13))
    control_chars += chr(127)
    pattern = '[' + re.escape(control_chars) + ']'
    return re.sub(pattern, '', text)

# ===== УДАЛЕНИЕ ДИАКРИТИКИ =====
def remove_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text)
    without_diacritics = ''.join(ch for ch in nfkd if not unicodedata.combining(ch))
    without_diacritics = without_diacritics.replace('ß', 'ss')
    return without_diacritics

# ===== ЖЁСТКАЯ ОЧИСТКА (БЕЛЫЙ СПИСОК) =====
def ultimate_clean(text: str) -> str:
    """
    Оставляет только:
    - русские буквы (включая Ё)
    - латинские буквы A-Z a-z
    - цифры
    - пробельные символы (пробел, \n, \r, \t)
    - знаки препинания: . , ! ? ; : - — – (дефис и тире)
    Всё остальное заменяет на пробел.
    """
    allowed = r'[^а-яА-ЯёЁa-zA-Z0-9\s.,!?;:-\—–]'
    cleaned = re.sub(allowed, ' ', text)
    # Сжимаем множественные пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# ===== НОРМАЛИЗАЦИЯ ПОСЛЕДОВАТЕЛЬНОСТЕЙ =====
def normalize_semicolons(text: str) -> str:
    return re.sub(r';{2,}', ';', text)

def normalize_dots(text: str) -> str:
    return re.sub(r'\.{4,}', '...', text)

def normalize_dashes(text: str) -> str:
    text = re.sub(r'-{4,}', '---', text)
    text = re.sub(r'–{4,}', '–––', text)
    text = re.sub(r'—{4,}', '———', text)
    return text

def normalize_newlines(text: str) -> str:
    text = text.replace('\r\n', '\n')
    text = re.sub(r'\n{2,}', '.', text)
    return text

def normalize_whitespace(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    return text

# ===== ЧТЕНИЕ ИЗ БУФЕРА ОБМЕНА =====
def get_text_from_clipboard():
    root = tk.Tk()
    root.withdraw()
    try:
        content = root.clipboard_get().strip()
    except tk.TclError:
        content = ""
    root.destroy()
    return content

# ===== ПОЛУЧЕНИЕ ТЕКСТА И ПРЕДОБРАБОТКА =====
text = get_text_from_clipboard()
if not text:
    print("Ошибка: буфер обмена пуст или не содержит текста.")
    print("Скопируйте нужный текст и запустите скрипт снова.")
    exit(1)

original_text = text

# 0. Удаляем управляющие символы
text = remove_control_characters(text)
# 1. Замена цифр на слова
text = replace_digits_with_words(text)
# 2. Замена латинских букв (обновлённая)
text = replace_latin_letters(text)
# 2.1. Замена греческих букв
text = replace_greek_letters(text)
# 3. Замена скобок и кавычек на ";"
text = replace_brackets_and_quotes(text)
# 4. Удаление диакритики
text = remove_diacritics(text)
# 5. Замена прочих недопустимых символов на пробелы
text = replace_other_symbols(text)
# 6. ЖЁСТКАЯ ОЧИСТКА (белый список)
text = ultimate_clean(text)
# 7. Нормализация последовательностей
text = normalize_semicolons(text)
text = normalize_dots(text)
text = normalize_dashes(text)
text = normalize_newlines(text)
# 8. Нормализация пробелов
text = normalize_whitespace(text)

print("Текст для озвучивания (первые 100 символов):")
print(text[:100] + "..." if len(text) > 100 else text)
print("-" * 40)
if original_text != text:
    print("Примечание: выполнена полная очистка текста (удалены управляющие символы, диакритика, оставлены только разрешённые символы).")

# ===== ФУНКЦИИ РАЗБИЕНИЯ ТЕКСТА =====
def split_long_sentence(sentence, max_chars):
    parts = []
    remaining = sentence
    while len(remaining) > max_chars:
        split_pos = -1
        for i in range(max_chars - 1, -1, -1):
            if i < len(remaining) and remaining[i] in (' ', ',', '_'):
                split_pos = i + 1
                break
        if split_pos == -1:
            split_pos = max_chars
        part = remaining[:split_pos].strip()
        if part:
            parts.append(part)
        remaining = remaining[split_pos:].strip()
    if remaining:
        parts.append(remaining)
    return parts

def split_sentences(text):
    sentences = []
    start = 0
    i = 0
    length = len(text)
    while i < length:
        if text[i] in '.!?':
            if i + 1 < length:
                next_char = text[i+1]
                if next_char == ' ':
                    sentences.append(text[start:i+1].strip())
                    start = i+2
                    i += 2
                    continue
                j = i+1
                while j < length and (text[j].isalpha() or text[j].isdigit() or text[j] in '-–'):
                    j += 1
                if j > i+1 and (text[i+1].isupper() or text[i+1].isdigit()):
                    if j < length and text[j-1] == '.':
                        i += 1
                        continue
                    else:
                        sentences.append(text[start:i+1].strip())
                        start = i+1
                        i += 1
                        continue
        i += 1
    if start < length:
        sentences.append(text[start:].strip())
    return [s for s in sentences if s]

def split_text_into_chunks(text, max_chars):
    sentences = split_sentences(text)
    chunks = []
    current = ""
    for sent in sentences:
        if len(sent) > max_chars:
            if current:
                chunks.append(current.strip())
            current = ""
            sub_sentences = split_long_sentence(sent, max_chars)
            for sub in sub_sentences:
                if len(current) + len(sub) + 1 <= max_chars:
                    current += sub + "  "
                else:
                    if current:
                        chunks.append(current.strip())
                    current = sub + "  "
        else:
            if len(current) + len(sent) + 1 <= max_chars:
                current += sent + "  "
            else:
                if current:
                    chunks.append(current.strip())
                current = sent + "  "
    if current:
        chunks.append(current.strip())
    return chunks

def save_wav(file_path, audio_np, sample_rate):
    audio_int16 = (audio_np * 32767).astype(np.int16)
    with wave.open(file_path, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_int16.tobytes())

# ===== ОСНОВНАЯ ЛОГИКА СИНТЕЗА =====
print("Загрузка модели Silero...")
device = torch.device('cpu')
torch.set_num_threads(4)
model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                          model='silero_tts',
                          language='ru',
                          speaker='v5_5_ru')
model.to(device)

print("Разбивка текста на фрагменты...")
chunks = split_text_into_chunks(text, max_chunk_chars)
print(f"Получено {len(chunks)} фрагментов (максимум {max_chunk_chars} символов каждый).")
print(f"Скорость речи: {speed} (через SSML)")

audio_parts = []
for i, chunk in enumerate(chunks, 1):
    print(f"Синтез фрагмента {i}/{len(chunks)}...")
    safe_chunk = html.escape(chunk)
    ssml_text = f'<speak><prosody rate="{speed}">{safe_chunk}</prosody></speak>'
    audio = model.apply_tts(ssml_text=ssml_text, speaker=voice, sample_rate=sample_rate)
    audio_parts.append(audio.cpu())

print("Склейка аудио...")
final_audio_np = np.concatenate([part.numpy() for part in audio_parts])
output_file = "silero_output.wav"
save_wav(output_file, final_audio_np, sample_rate)
print(f"Готово! Аудио сохранено в файл: {output_file}")