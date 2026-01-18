import os
import csv
import time
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor

# Cấu hình Gemini API
API_KEY = "AIzaSyCchGLebhB2aNwukTXJ7Zh1sYTknahxLQk"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

def translate_batch(texts, target_lang="Vietnamese"):
    prompt = f"Translate the following game strings from Traditional Chinese to {target_lang}. Keep the original format, tags (like #Y, #E, [xxxx]), and variables. Return only the translated strings, one per line. Do not add any explanations.\n\n"
    prompt += "\n".join(texts)
    
    try:
        response = model.generate_content(prompt)
        translated_content = response.text.strip()
        return translated_content.split('\n')
    except Exception as e:
        print(f"Error during translation: {e}")
        return None

def process_tsv(input_path, output_path, batch_size=30, limit=100):
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
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
        
        if translated_texts:
            for j in range(min(len(batch), len(translated_texts))):
                translated_rows.append([batch[j][0], translated_texts[j]])
        else:
            # Fallback to original if translation fails
            for row in batch:
                translated_rows.append(row)
        
        time.sleep(1) # Rate limiting

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        writer.writerows(translated_rows)
    
    print(f"Translation saved to {output_path}")

if __name__ == "__main__":
    # Đường dẫn file đã trích xuất từ trước
    input_tsv = "/home/ubuntu/extracted_text.tsv"
    output_tsv = "/home/ubuntu/Wwm-Translation/translation_vn.tsv"
    
    # Dịch thử nghiệm 100 dòng đầu tiên
    process_tsv(input_tsv, output_tsv, limit=100)
