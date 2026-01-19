import os
import struct
import pyzstd
import csv
import re

def log(msg):
    print(f"[REPACK] {msg}")

def apply_translation_to_dat(dat_dir, translation_tsv):
    translations = {}
    with open(translation_tsv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader) # skip header
        for row in reader:
            if len(row) >= 2:
                translations[row[0]] = row[1]
    
    log(f"Loaded {len(translations)} translations.")
    
    # Duyệt qua các file .dat để thay thế text
    for filename in sorted(os.listdir(dat_dir)):
        if not filename.endswith('.dat') or filename.endswith('_0.dat'):
            continue
            
        path = os.path.join(dat_dir, filename)
        with open(path, 'rb') as f:
            data = f.read()
            
        # Cấu trúc file .dat: [count_full(4)] [unk(4)] [count_text(4)] ...
        count_full = struct.unpack('<I', data[0:4])[0]
        # Giữ nguyên phần header và code
        header_end = 4 + 4 + 4 + 12 + count_full + 17
        
        new_texts = []
        offsets = []
        current_offset = 0
        
        # Đọc ID và Text cũ để thay thế
        for i in range(count_full):
            entry_pos = header_end + (i * 16)
            id_bytes = data[entry_pos:entry_pos+8].hex()
            rel_offset = struct.unpack('<I', data[entry_pos+8:entry_pos+12])[0]
            length = struct.unpack('<I', data[entry_pos+12:entry_pos+16])[0]
            
            # Lấy text mới nếu có, không thì dùng text cũ
            text_pos = entry_pos + 8 + rel_offset
            old_text = data[text_pos:text_pos+length].decode('utf-8', errors='ignore')
            new_text = translations.get(id_bytes, old_text)
            
            encoded_text = new_text.encode('utf-8')
            new_texts.append(encoded_text)
            offsets.append(current_offset)
            current_offset += len(encoded_text)
            
        # Xây dựng lại file .dat mới
        new_dat = bytearray(data[:header_end])
        # Viết lại bảng offset
        for i in range(count_full):
            entry_pos = header_end + (i * 16)
            new_dat.extend(data[entry_pos:entry_pos+8]) # ID
            # Tính toán offset tương đối mới: từ vị trí sau trường offset đến text
            # Trong cấu trúc gốc: offset_text là khoảng cách từ (entry_pos + 12) đến text
            new_offset = (header_end + count_full * 16 + offsets[i]) - (entry_pos + 12)
            new_dat.extend(struct.pack('<I', new_offset))
            new_dat.extend(struct.pack('<I', len(new_texts[i])))
            
        # Thêm toàn bộ text mới vào cuối
        for t in new_texts:
            new_dat.extend(t)
            
        with open(path, 'wb') as f:
            f.write(new_dat)
    log("Applied translations to .dat files.")

def pak_file(dat_dir, output_file):
    try:
        files = [f for f in sorted(os.listdir(dat_dir)) if f.endswith('.dat')]
        
        with open(output_file, 'wb') as outfile:
            # Magic header
            outfile.write(b'\xEF\xBE\xAD\xDE\x01\x00\x00\x00')
            outfile.write(struct.pack('<I', len(files) - 1))
            
            archive = b''
            offsets = []
            for filename in files:
                with open(os.path.join(dat_dir, filename), 'rb') as infile:
                    data = infile.read()
                
                offsets.append(len(archive))
                comp_data = pyzstd.compress(data)
                header = struct.pack('<BII', 4, len(comp_data), len(data))
                archive += header + comp_data
            
            # Viết bảng offset (trừ file cuối)
            for i in range(len(offsets) - 1):
                outfile.write(struct.pack('<I', offsets[i]))
            
            # Viết offset cuối cùng (tổng kích thước archive)
            outfile.write(struct.pack('<I', len(archive)))
            outfile.write(archive)
            
        log(f"✅ Repack complete: {output_file}")
        return True
    except Exception as e:
        log(f"❌ Repack error: {e}")
        return False

if __name__ == "__main__":
    dat_dir = "work/translate_words_map_zh_tw" # Thư mục chứa các file .dat đã giải nén
    translation_tsv = "translation_vn.tsv"
    output_file = "translate_words_map_vn" # File kết quả không đuôi
    
    if os.path.exists(dat_dir) and os.path.exists(translation_tsv):
        apply_translation_to_dat(dat_dir, translation_tsv)
        pak_file(dat_dir, output_file)
    else:
        log("Missing dat directory or translation file.")
