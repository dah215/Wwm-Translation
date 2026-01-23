import os
import csv
import time
import google.generativeai as genai

# Cấu hình API
API_KEY = os.environ.get("OPEN_AI")
if not API_KEY:
    print("Lỗi: Biến môi trường OPEN_AI chưa được đặt. Vui lòng tạo một khóa API mới và thêm nó vào mục Secrets của kho lưu trữ GitHub với tên GEMINI_API_KEY.")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gpt-5.2-pro')

def translate_batch(texts, target_lang="Vietnamese"):
    prompt = f"Translate the following game strings from Traditional Chinese to {target_lang}. Keep the original format, tags (like #Y, #E, [xxxx]), and variables. Return only the translated strings, one per line. Do not add any explanations.\\n\\n"
    prompt += "\\n".join(texts)
    
    try:
        response = model.generate_content(prompt)
        translated_content = response.text.strip()
        lines = translated_content.split('\\n')
        return lines
    except Exception as e:
        print(f"Error during translation: {e}")
        return None

def load_existing_translations(output_path):
    translations = {}
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            # Sửa lỗi: delimiter phải là '\t'
            reader = csv.reader(f, delimiter='\t')
            next(reader, None) # skip header
            for row in reader:
                if len(row) >= 2:
                    translations[row[0]] = row[1]
    return translations

def process_tsv(input_path, output_path, batch_size=30, max_rows_per_run=2000):
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    # Tải các bản dịch đã có
    existing_translations = load_existing_translations(output_path)
    print(f"Loaded {len(existing_translations)} existing translations.")

    rows_to_translate = []
    all_rows_info = [] # Để giữ thứ tự và ID

    with open(input_path, 'r', encoding='utf-8') as f:
        # Sửa lỗi: delimiter phải là '\t'
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        for row in reader:
            if len(row) < 2: continue
            row_id = row[0]
            original_text = row[1]
            all_rows_info.append(row_id)
            
            # Chỉ dịch nếu chưa có trong file kết quả
            if row_id not in existing_translations and original_text.strip():
                rows_to_translate.append(row)
            
            if len(rows_to_translate) >= max_rows_per_run:
                break

    if not rows_to_translate:
        print("All rows are already translated or no new rows found.")
        return

    print(f"Translating {len(rows_to_translate)} new rows...")
    
    new_translations = {}
    for i in range(0, len(rows_to_translate), batch_size):
        batch = rows_to_translate[i:i+batch_size]
        texts = [row[1] for row in batch]
        
        print(f"Processing batch {i//batch_size + 1} / {len(rows_to_translate)//batch_size + 1}...")
        translated_texts = translate_batch(texts)
        
        if translated_texts and len(translated_texts) >= len(batch):
            for j in range(len(batch)):
                new_translations[batch[j][0]] = translated_texts[j]
        else:
            print(f"Batch {i//batch_size + 1} failed. Skipping.")
        
        time.sleep(2) # Tăng thời gian chờ để tránh Rate Limit của Gemini Free Tier

    # Cập nhật và lưu lại toàn bộ
    existing_translations.update(new_translations)
    
    # Ghi lại file kết quả (giữ nguyên header)
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        # Sửa lỗi: delimiter phải là '\t'
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        for row_id, text in existing_translations.items():
            writer.writerow([row_id, text])
    
    print(f"Progress updated. Total translated: {len(existing_translations)}")

if __name__ == "__main__":
    input_tsv = "extracted_text.tsv"
    output_tsv = "translation_vn.tsv"
    
    process_tsv(input_tsv, output_tsv, max_rows_per_run=100000)
