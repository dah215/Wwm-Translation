import os
import csv
import time
import google.generativeai as genai

# Lấy API Key từ biến môi trường (bảo mật hơn)
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCchGLebhB2aNwukTXJ7Zh1sYTknahxLQk")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

def translate_batch(texts, target_lang="Vietnamese"):
    prompt = f"Translate the following game strings from Traditional Chinese to {target_lang}. Keep the original format, tags (like #Y, #E, [xxxx]), and variables. Return only the translated strings, one per line. Do not add any explanations.\n\n"
    prompt += "\n".join(texts)
    
    try:
        response = model.generate_content(prompt)
        translated_content = response.text.strip()
        # Xử lý trường hợp AI trả về thừa hoặc thiếu dòng
        lines = translated_content.split('\n')
        return lines
    except Exception as e:
        print(f"Error during translation: {e}")
        return None

def process_tsv(input_path, output_path, batch_size=20, limit=500):
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        # Nếu không có file đầu vào, tạo file mẫu để tránh lỗi workflow
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("ID\tOriginalText\n")
        return

    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        for row in reader:
            if len(row) >= 2 and row[1].strip():
                rows.append(row)
            if len(rows) >= limit:
                break

    print(f"Translating {len(rows)} rows in batches of {batch_size}...")
    
    translated_rows = []
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        texts = [row[1] for row in batch]
        
        print(f"Processing batch {i//batch_size + 1}...")
        translated_texts = translate_batch(texts)
        
        if translated_texts and len(translated_texts) >= len(batch):
            for j in range(len(batch)):
                translated_rows.append([batch[j][0], translated_texts[j]])
        else:
            print(f"Batch {i//batch_size + 1} failed or returned inconsistent results. Using original text.")
            for row in batch:
                translated_rows.append(row)
        
        time.sleep(2) # Tránh bị giới hạn API (Rate limit)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        writer.writerows(translated_rows)
    
    print(f"Translation saved to {output_path}")

if __name__ == "__main__":
    input_tsv = "extracted_text.tsv"
    output_tsv = "translation_vn.tsv"
    
    # Tăng giới hạn dịch lên 500 dòng mỗi lần chạy tự động
    process_tsv(input_tsv, output_tsv, limit=500)
