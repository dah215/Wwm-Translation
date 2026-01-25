import os
import csv
import time
import google.generativeai as genai

# Cấu hình API
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Lỗi: Biến môi trường GEMINI_API_KEY chưa được đặt.")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def translate_batch(texts, target_lang="Vietnamese"):
    prompt = f"Translate the following game strings from Traditional Chinese to {target_lang}. Keep the original format, tags (like #Y, #E, [xxxx]), and variables. Return only the translated strings, one per line. Do not add any explanations.\n\n"
    prompt += "\n".join(texts)
    
    try:
        response = model.generate_content(prompt)
        translated_content = response.text.strip()
        lines = translated_content.split('\n')
        return lines
    except Exception as e:
        print(f"Error during translation: {e}")
        return None

def load_existing_translations(output_path):
    translations = {}
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 2:
                    translations[row[0]] = row[1]
    return translations

def process_tsv(input_path, output_path, batch_size=20, max_batches_per_run=17):
    """
    Giới hạn số batch mỗi lần chạy để tránh vượt quota
    Free tier: 20 requests/day, nên dùng tối đa 15 batches để an toàn
    """
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    # Tải các bản dịch đã có
    existing_translations = load_existing_translations(output_path)
    print(f"Loaded {len(existing_translations)} existing translations.")

    rows_to_translate = []
    all_rows_info = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            row_id = row[0]
            original_text = row[1]
            all_rows_info.append(row_id)
            
            # Chỉ dịch nếu chưa có trong file kết quả
            if row_id not in existing_translations and original_text.strip():
                rows_to_translate.append(row)

    if not rows_to_translate:
        print("✅ All rows are already translated!")
        return

    # Giới hạn số lượng rows dựa trên max_batches_per_run
    max_rows = batch_size * max_batches_per_run
    if len(rows_to_translate) > max_rows:
        rows_to_translate = rows_to_translate[:max_rows]
        print(f"⚠️ Limiting to {len(rows_to_translate)} rows ({max_batches_per_run} batches) to avoid quota limits.")
    
    print(f"Translating {len(rows_to_translate)} new rows in {(len(rows_to_translate) + batch_size - 1) // batch_size} batches...")
    
    new_translations = {}
    success_count = 0
    fail_count = 0
    
    for i in range(0, len(rows_to_translate), batch_size):
        batch = rows_to_translate[i:i+batch_size]
        texts = [row[1] for row in batch]
        batch_num = i // batch_size + 1
        total_batches = (len(rows_to_translate) + batch_size - 1) // batch_size
        
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
        
        translated_texts = translate_batch(texts)
        
        if translated_texts and len(translated_texts) >= len(batch):
            for j in range(len(batch)):
                new_translations[batch[j][0]] = translated_texts[j]
            success_count += len(batch)
            print(f"✅ Batch {batch_num} successful")
        else:
            fail_count += len(batch)
            print(f"❌ Batch {batch_num} failed. Skipping.")
        
        # Tăng thời gian chờ để tránh rate limit
        if i + batch_size < len(rows_to_translate):
            wait_time = 4
            print(f"Waiting {wait_time} seconds before next batch...")
            time.sleep(wait_time)

    # Cập nhật và lưu lại toàn bộ
    existing_translations.update(new_translations)
    
    # Ghi lại file kết quả
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        for row_id, text in existing_translations.items():
            writer.writerow([row_id, text])
    
    print(f"\n{'='*50}")
    print(f"✅ Translation completed!")
    print(f"   Successfully translated: {success_count} rows")
    print(f"   Failed: {fail_count} rows")
    print(f"   Total in database: {len(existing_translations)} rows")
    print(f"   Remaining: {len([r for r in rows_to_translate if r[0] not in new_translations])} rows")
    print(f"{'='*50}")

if __name__ == "__main__":
    input_tsv = "extracted_text.tsv"
    output_tsv = "translation_vn.tsv"
    
    # Giảm batch_size xuống 20 và giới hạn 15 batches/lần chạy
    # = 300 dòng mỗi lần chạy (an toàn với free tier 20 requests/day)
    process_tsv(input_tsv, output_tsv, batch_size=20, max_batches_per_run=17)
