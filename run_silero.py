import torch
import re
import numpy as np
import wave
import tkinter as tk
import unicodedata
# import html  # не используется

# ===== НАСТРОЙКИ =====
voice = 'kseniya'
sample_rate = 48000
max_chunk_chars = 300
speed = 'x-slow'

# ===== ЗАМЕНА ЦИФР НА СЛОВА =====
def replace_digits_with_words(text: str) -> str:
    digit_map = {
        '0': ' ноль ', '1': ' один ', '2': ' два ', '3': ' три ',
        '4': ' четыре ', '5': ' пять ', '6': ' шесть ', '7': ' семь ',
        '8': ' восемь ', '9': ' девять '
    }
    return ''.join(digit_map.get(ch, ch) for ch in text)

# ===== ЗАМЕНА IPA-СИМВОЛОВ =====
def replace_ipa_symbols(text: str) -> str:
    text = text.replace('iː', ' и-долгий ')
    text = text.replace('i:', ' и-долгий ')
    text = text.replace('uː', ' у-долгий ')
    text = text.replace('u:', ' у-долгий ')
    ipa_map = {
        'ɪ': ' и-краткий ',
        'ʊ': ' у-краткий ',
        'ɛ': ' э ',
        'ə': ' э ',
        'ʌ': ' а ',
        'ɑ': ' а ',
        'ɔ': ' о ',
        'ʃ': ' ш ',
        'ʒ': ' ж ',
        'θ': ' с ',
        'ð': ' з ',
        'ŋ': ' н ',
        'ː': '',
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
    i = 0
    length = len(text)
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

# ===== ДИАКРИТИКА =====
def remove_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text)
    without_diacritics = ''.join(ch for ch in nfkd if not unicodedata.combining(ch))
    return without_diacritics.replace('ß', 'ss')

# ===== ЖЁСТКАЯ ОЧИСТКА =====
def ultimate_clean(text: str) -> str:
    allowed = r'[^а-яА-ЯёЁa-zA-Z0-9\s.,!?;:-\—–]'
    cleaned = re.sub(allowed, ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# ===== НОРМАЛИЗАЦИЯ =====
def normalize_semicolons(text): return re.sub(r';{2,}', ';', text)

def normalize_punctuation_runs(text: str) -> str:
    """
    Сворачивает цепочки из .,!? длиной >= 2 в один символ,
    кроме '!?', '?!' и '...'.
    """
    exceptions = {'!?', '?!', '...'}

    def repl(m):
        s = m.group(0)
        return s if s in exceptions else s[0]

    return re.sub(r'[.,!?]{2,}', repl, text)

def normalize_dashes(text):
    """
    Любая цепочка из 2 и более дефисов подряд
    (любого вида: ASCII '-', en-dash '–', em-dash '—')
    превращается в одно тире '—'.
    Одиночный дефис любого вида остаётся как есть.
    """
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
text = replace_ipa_symbols(text)
text = replace_digits_with_words(text)
text = replace_latin_letters(text)
text = replace_greek_letters(text)
text = replace_brackets_and_quotes(text)
text = remove_diacritics(text)
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

# ===== РАЗБИЕНИЕ НА ФРАГМЕНТЫ =====
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
            for sub in split_long_sentence(sent, max_chars):
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
chunks = split_text_into_chunks(text, max_chunk_chars)
print(f"Получено {len(chunks)} фрагментов (максимум {max_chunk_chars} символов).")
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