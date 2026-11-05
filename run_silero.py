import torch
import re
import numpy as np
import wave
import tkinter as tk
import unicodedata

# ===== НАСТРОЙКИ =====
voice = 'kseniya'
sample_rate = 48000
MIN_CHUNK_CHARS = 30
MAX_CHUNK_CHARS = 300
speed = 'x-slow'

# ===== ЗАМЕНА ЦИФР НА СЛОВА =====
def replace_digits_with_words(text: str) -> str:
    digit_map = {
        '0': ' ноль ', '1': ' один ', '2': ' два ', '3': ' три ',
        '4': ' четыре ', '5': ' пять ', '6': ' шесть ', '7': ' семь ',
        '8': ' восемь ', '9': ' девять '
    }
    return ''.join(digit_map.get(ch, ch) for ch in text)

# ===== ЗАМЕНА НЕРУССКИХ КИРИЛЛИЧЕСКИХ БУКВ =====
def replace_non_russian_cyrillic(text: str) -> str:
    mapping = {
        # украинский / белорусский
        'ґ': 'г', 'Ґ': 'Г',
        'є': 'е', 'Є': 'Е',
        'і': 'и', 'І': 'И',
        'ї': 'йи', 'Ї': 'Йи',
        'ў': 'у', 'Ў': 'У',
        # сербский / македонский
        'ј': 'й', 'Ј': 'Й',
        'љ': 'ль', 'Љ': 'Ль',
        'њ': 'нь', 'Њ': 'Нь',
        'ћ': 'ч', 'Ћ': 'Ч',
        'ђ': 'дж', 'Ђ': 'Дж',
        'џ': 'дж', 'Џ': 'Дж',
        'ѓ': 'г', 'Ѓ': 'Г',
        'ќ': 'к', 'Ќ': 'К',
        'ѕ': 'дз', 'Ѕ': 'Дз',
        # тюркские языки СНГ (казахский, киргизский, туркменский,
        # азербайджанский, татарский, башкирский) и таджикский
        'ә': 'а', 'Ә': 'А',
        'ғ': 'г', 'Ғ': 'Г',
        'қ': 'к', 'Қ': 'К',
        'ң': 'нг', 'Ң': 'Нг',
        'ө': 'о', 'Ө': 'О',
        'ұ': 'у', 'Ұ': 'У',
        'ү': 'у', 'Ү': 'У',
        'һ': 'х', 'Һ': 'Х',
        'җ': 'дж', 'Җ': 'Дж',
        'ҳ': 'х', 'Ҳ': 'Х',
        'ҷ': 'дж', 'Ҷ': 'Дж',
        'ӣ': 'и', 'Ӣ': 'И',
        'ӯ': 'у', 'Ӯ': 'У',
        'ҙ': 'з', 'Ҙ': 'З',
        'ҫ': 'с', 'Ҫ': 'С',
    }
    return ''.join(mapping.get(ch, ch) for ch in text)

# ===== ЗАМЕНА КИРИЛЛИЧЕСКИХ АББРЕВИАТУР =====
def replace_cyrillic_abbreviations(text: str) -> str:
    name_map = {
        'А': 'а', 'Б': 'бэ', 'В': 'вэ', 'Г': 'гэ', 'Д': 'дэ',
        'Е': 'е', 'Ё': 'ё', 'Ж': 'жэ', 'З': 'зэ', 'И': 'и',
        'Й': 'и краткое', 'К': 'ка', 'Л': 'эл', 'М': 'эм',
        'Н': 'эн', 'О': 'о', 'П': 'пэ', 'Р': 'эр', 'С': 'эс',
        'Т': 'тэ', 'У': 'у', 'Ф': 'эф', 'Х': 'ха', 'Ц': 'цэ',
        'Ч': 'че', 'Ш': 'ша', 'Щ': 'ща', 'Ъ': 'твёрдый знак',
        'Ы': 'ы', 'Ь': 'мягкий знак', 'Э': 'э', 'Ю': 'ю', 'Я': 'я'
    }
    def is_upper_cyr(ch): return ('А' <= ch <= 'Я') or ch == 'Ё'

    result = []
    i, length = 0, len(text)
    while i < length:
        ch = text[i]
        if is_upper_cyr(ch):
            j = i
            while j < length and is_upper_cyr(text[j]):
                j += 1
            run_len = j - i
            if run_len >= 2:
                for k in range(i, j):
                    result.append(' ' + name_map.get(text[k], text[k]) + ' ')
                i = j
                continue
            result.append(ch)
            i += 1
            continue
        result.append(ch)
        i += 1
    return ''.join(result)

# ===== ЗАМЕНА IPA-СИМВОЛОВ =====
def replace_ipa_symbols(text: str) -> str:
    text = text.replace('iː', ' и-долгий ')
    text = text.replace('i:', ' и-долгий ')
    text = text.replace('uː', ' у-долгий ')
    text = text.replace('u:', ' у-долгий ')
    ipa_map = {
        'ɪ': ' и-краткий ', 'ʊ': ' у-краткий ', 'ɛ': ' э ',
        'ə': ' э ', 'ʌ': ' а ', 'ɑ': ' а ', 'ɔ': ' о ',
        'ʃ': ' ш ', 'ʒ': ' ж ', 'θ': ' с ', 'ð': ' з ',
        'ŋ': ' н ', 'ː': '',
    }
    return ''.join(ipa_map.get(ch, ch) for ch in text)

# ===== ЗАМЕНА ЛАТИНСКИХ БУКВ =====
def replace_latin_letters(text: str) -> str:
    latin_map_lower = {
        'a': 'а', 'b': 'б', 'c': 'ч', 'd': 'д', 'e': 'э',
        'f': 'ф', 'g': 'г', 'h': 'х', 'i': 'и', 'j': 'дж',
        'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
        'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т',
        'u': 'у', 'v': 'в', 'w': 'в', 'x': 'кс', 'y': 'й', 'z': 'з'
    }
    latin_map_upper_name = {
        'A': ' Эй ', 'B': ' Би ', 'C': ' Си ', 'D': ' Ди ', 'E': ' И ',
        'F': ' Эф ', 'G': ' Джи ', 'H': ' Эйч ', 'I': ' Ай ', 'J': ' Джей ',
        'K': ' Кей ', 'L': ' Эл ', 'M': ' Эм ', 'N': ' Эн ', 'O': ' Оу ',
        'P': ' Пи ', 'Q': ' Кью ', 'R': ' Ар ', 'S': ' Эс ', 'T': ' Ти ',
        'U': ' Ю ', 'V': ' Ви ', 'W': ' Дабл-Ю ', 'X': ' Экс ', 'Y': ' Уай ', 'Z': ' Зед '
    }
    result = []
    i, length = 0, len(text)
    while i < length:
        ch = text[i]
        if 'a' <= ch <= 'z':
            result.append(latin_map_lower.get(ch, ch))
        elif 'A' <= ch <= 'Z':
            next_is_lower_latin = (i + 1 < length and 'a' <= text[i + 1] <= 'z')
            if next_is_lower_latin:
                result.append(latin_map_lower.get(ch.lower(), ch))
            else:
                result.append(latin_map_upper_name.get(ch, ch))
        else:
            result.append(ch)
        i += 1
    return ''.join(result)

# ===== ЗАМЕНА ГРЕЧЕСКИХ БУКВ =====
def replace_greek_letters(text: str) -> str:
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
    return ''.join(greek_map.get(ch.lower(), ch) for ch in text)

# ===== СКОБКИ И КАВЫЧКИ → ";" =====
def replace_brackets_and_quotes(text: str) -> str:
    return re.sub(r'[\(\)\[\]\{\}<>"\'«»„“`‛]', ';', text)

# ===== ПРОЧИЕ НЕДОПУСТИМЫЕ → ПРОБЕЛ =====
def replace_other_symbols(text: str) -> str:
    return re.sub(r'[^\w.,!?;:-\—–]', ' ', text)

# ===== УПРАВЛЯЮЩИЕ СИМВОЛЫ =====
def remove_control_characters(text: str) -> str:
    control_chars = ''.join(chr(c) for c in range(32) if c not in (9, 10, 13))
    control_chars += chr(127)
    return re.sub('[' + re.escape(control_chars) + ']', '', text)

# ===== ДИАКРИТИКА (только для не-русских символов) =====
def remove_diacritics(text: str) -> str:
    def process(ch: str) -> str:
        if ch in 'ёЁ' or 'а' <= ch.lower() <= 'я':
            return ch
        nfkd = unicodedata.normalize('NFKD', ch)
        stripped = ''.join(c for c in nfkd if not unicodedata.combining(c))
        return stripped.replace('ß', 'ss')
    return ''.join(process(ch) for ch in text)

# ===== ЖЁСТКАЯ ОЧИСТКА =====
def ultimate_clean(text: str) -> str:
    allowed = r'[^а-яА-ЯёЁa-zA-Z0-9\s.,!?;:-\—–]'
    cleaned = re.sub(allowed, ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# ===== НОРМАЛИЗАЦИЯ =====
def normalize_semicolons(text): return re.sub(r';{2,}', ';', text)

def normalize_punctuation_runs(text: str) -> str:
    exceptions = {'!?', '?!', '...'}
    def repl(m):
        s = m.group(0)
        return s if s in exceptions else s[0]
    return re.sub(r'[.,!?]{2,}', repl, text)

def normalize_dashes(text):
    return re.sub(r'[-–—]{2,}', '—', text)

def normalize_newlines(text):
    text = text.replace('\r\n', '\n')
    return re.sub(r'\n{2,}', '.', text)

def normalize_whitespace(text):
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

# ===== БУФЕР ОБМЕНА =====
def get_text_from_clipboard():
    root = tk.Tk()
    root.withdraw()
    try:
        content = root.clipboard_get().strip()
    except tk.TclError:
        content = ""
    root.destroy()
    return content

# ===== ЭКРАНИРОВАНИЕ ДЛЯ SSML =====
def escape_for_ssml(s: str) -> str:
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;'))

# ===== АГРЕССИВНАЯ ОЧИСТКА ДЛЯ SSML =====
def sanitize_for_ssml(s: str) -> str:
    s = re.sub(r'[^а-яА-ЯёЁa-zA-Z0-9\s.,!?]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# ===== ПОЛУЧЕНИЕ ТЕКСТА И ПРЕДОБРАБОТКА =====
text = get_text_from_clipboard()
if not text:
    print("Ошибка: буфер обмена пуст или не содержит текста.")
    print("Скопируйте нужный текст и запустите скрипт снова.")
    exit(1)

original_text = text
text = remove_control_characters(text)
text = replace_non_russian_cyrillic(text)    # ← до remove_diacritics!
text = remove_diacritics(text)
text = replace_ipa_symbols(text)
text = replace_digits_with_words(text)
text = replace_cyrillic_abbreviations(text)
text = replace_latin_letters(text)
text = replace_greek_letters(text)
text = replace_brackets_and_quotes(text)
text = replace_other_symbols(text)
text = ultimate_clean(text)
text = normalize_semicolons(text)
text = normalize_punctuation_runs(text)
text = normalize_dashes(text)
text = normalize_newlines(text)
text = normalize_whitespace(text)

print("Текст для озвучивания (первые 100 символов):")
print(text[:100] + "..." if len(text) > 100 else text)
print("-" * 40)

# ===== РАЗБИЕНИЕ НА ФРАГМЕНТЫ (оконный алгоритм) =====
def split_text_into_chunks(text, min_chars, max_chars):
    """
    Непрерывное разбиение текста на чанки по окну.

    Окно поиска разделителя: [start + min_chars, start + max_chars]
    включительно. Разделитель можно выбирать ровно на нижней границе окна.

    Если до конца текста осталось <= min_chars — весь остаток текста
    становится последним чанком.
    Если осталось < max_chars — окно идёт до конца текста.
    Иначе окно идёт от start + min_chars до start + max_chars включительно.

    Приоритеты разделителей (поиск от конца окна к началу):
      1) . ! ?   (непрерывная серия таких символов считается одним
                  разделителем, поэтому "..." не разрезается)
      2) ; :
      3) ,
      4) пробел / перенос строки

    Знаки препинания включаются в текущий чанк.
    Пробел / перенос строки в текущий чанк не включаются — они
    становятся ведущими символами следующего чанка.
    Если разделитель не найден — принудительная резка по верхней границе
    окна, при этом символ на верхней границе входит в текущий чанк.
    Закрывающая фигурная скобка разделителем не считается.
    """
    chunks = []
    start = 0
    n = len(text)

    level1 = '.!?'
    level2 = ';:'
    level3 = ','
    level4 = ' \n\r\t'

    while start < n:
        remaining = n - start

        # Остаток не больше минимума — это последний чанк
        if remaining <= min_chars:
            chunks.append(text[start:])
            break

        # Границы окна поиска (включительно)
        win_lo = start + min_chars
        win_hi = min(start + max_chars, n - 1)

        split_pos = None
        split_is_whitespace = False

        # Уровень 1: . ! ?  (серия подряд идущих — один разделитель)
        for i in range(win_hi, win_lo - 1, -1):
            if text[i] in level1:
                j = i
                while j + 1 < n and text[j + 1] in level1:
                    j += 1
                split_pos = j
                split_is_whitespace = False
                break

        # Уровень 2: ; :
        if split_pos is None:
            for i in range(win_hi, win_lo - 1, -1):
                if text[i] in level2:
                    split_pos = i
                    split_is_whitespace = False
                    break

        # Уровень 3: ,
        if split_pos is None:
            for i in range(win_hi, win_lo - 1, -1):
                if text[i] in level3:
                    split_pos = i
                    split_is_whitespace = False
                    break

        # Уровень 4: пробел / перенос строки
        if split_pos is None:
            for i in range(win_hi, win_lo - 1, -1):
                if text[i] in level4:
                    split_pos = i
                    split_is_whitespace = True
                    break

        if split_pos is None:
            # Принудительная резка: верхняя граница окна входит в чанк
            chunks.append(text[start:win_hi + 1])
            start = win_hi + 1
        elif split_is_whitespace:
            # Пробел/перенос не включаем в текущий чанк
            chunks.append(text[start:split_pos])
            # Пробел станет ведущим символом следующего чанка
            start = split_pos
        else:
            # Знак препинания включаем в текущий чанк
            chunks.append(text[start:split_pos + 1])
            start = split_pos + 1

    return chunks

def save_wav(file_path, audio_np, sample_rate):
    audio_int16 = (audio_np * 32767).astype(np.int16)
    with wave.open(file_path, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_int16.tobytes())

# ===== СИНТЕЗ =====
print("Загрузка модели Silero...")
device = torch.device('cpu')
torch.set_num_threads(4)
model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                          model='silero_tts',
                          language='ru',
                          speaker='v5_5_ru')
model.to(device)

print("Разбивка текста на фрагменты...")
chunks = split_text_into_chunks(text, MIN_CHUNK_CHARS, MAX_CHUNK_CHARS)
print(f"Получено {len(chunks)} фрагментов "
      f"(минимум {MIN_CHUNK_CHARS}, максимум {MAX_CHUNK_CHARS} символов).")
print(f"Скорость речи: {speed} (через SSML)")

audio_parts = []
for i, chunk in enumerate(chunks, 1):
    print(f"Синтез фрагмента {i}/{len(chunks)}...")

    attempts = [
        ("обычный",
         f'<speak><prosody rate="{speed}">{escape_for_ssml(chunk)}</prosody></speak>'),
        ("агрессивно очищенный",
         f'<speak><prosody rate="{speed}">{escape_for_ssml(sanitize_for_ssml(chunk))}</prosody></speak>'),
    ]

    audio = None
    for attempt_idx, (label, ssml_text) in enumerate(attempts, 1):
        print(f"  → попытка {attempt_idx} ({label}), ssml_text: {ssml_text[:200]!r}")
        try:
            audio = model.apply_tts(ssml_text=ssml_text,
                                    speaker=voice,
                                    sample_rate=sample_rate)
            break
        except Exception as e:
            print(f"  ! попытка {attempt_idx} не удалась: "
                  f"{type(e).__name__}: {e}")

    if audio is None:
        print(f"  !!! все SSML-попытки провалились, синтез без SSML "
              f"(темп будет нормальным, не {speed})")
        audio = model.apply_tts(text=chunk,
                                speaker=voice,
                                sample_rate=sample_rate)

    audio_parts.append(audio.cpu())

print("Склейка аудио...")
final_audio_np = np.concatenate([part.numpy() for part in audio_parts])
output_file = "silero_output.wav"
save_wav(output_file, final_audio_np, sample_rate)
print(f"Готово! Аудио сохранено в файл: {output_file}")