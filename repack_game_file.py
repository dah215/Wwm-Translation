import os
import struct
import pyzstd
import csv

def log(msg):
    print(f"[REPACK] {msg}")

def apply_translation_to_dat(dat_dir, translation_tsv):
    translations = {}
    if not os.path.exists(translation_tsv):
        log("Translation file not found.")
        return False
        
    with open(translation_tsv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader, None)
        for row in reader:
            if len(row) >= 2:
                translations[row[0]] = row[1]
    
    log(f"Loaded {len(translations)} translations.")
    
    for filename in sorted(os.listdir(dat_dir)):
        if not filename.endswith('.dat') or filename.endswith('_0.dat'):
            continue
            
        path = os.path.join(dat_dir, filename)
        with open(path, 'rb') as f:
            data = f.read()
            
        count_full = struct.unpack('<I', data[0:4])[0]
        header_end = 4 + 4 + 4 + 12 + count_full + 17
        
        new_texts = []
        offsets = []
        current_offset = 0
        
        for i in range(count_full):
            entry_pos = header_end + (i * 16)
            id_bytes = data[entry_pos:entry_pos+8].hex()
            rel_offset = struct.unpack('<I', data[entry_pos+8:entry_pos+12])[0]
            length = struct.unpack('<I', data[entry_pos+12:entry_pos+16])[0]
            
            text_pos = entry_pos + 8 + rel_offset
            old_text = data[text_pos:text_pos+length].decode('utf-8', errors='ignore')
            new_text = translations.get(id_bytes, old_text)
            
            encoded_text = new_text.encode('utf-8')
            new_texts.append(encoded_text)
            offsets.append(current_offset)
            current_offset += len(encoded_text)
            
        new_dat = bytearray(data[:header_end])
        for i in range(count_full):
            entry_pos = header_end + (i * 16)
            new_dat.extend(data[entry_pos:entry_pos+8])
            new_offset = (header_end + count_full * 16 + offsets[i]) - (entry_pos + 12)
            new_dat.extend(struct.pack('<I', new_offset))
            new_dat.extend(struct.pack('<I', len(new_texts[i])))
            
        for t in new_texts:
            new_dat.extend(t)
            
        with open(path, 'wb') as f:
            f.write(new_dat)
    return True

def pak_file(dat_dir, output_file):
    try:
        files = [f for f in sorted(os.listdir(dat_dir)) if f.endswith('.dat')]
        with open(output_file, 'wb') as outfile:
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
            for i in range(len(offsets) - 1):
                outfile.write(struct.pack('<I', offsets[i]))
            outfile.write(struct.pack('<I', len(archive)))
            outfile.write(archive)
        log(f"✅ Repack complete: {output_file}")
        return True
    except Exception as e:
        log(f"❌ Repack error: {e}")
        return False

if __name__ == "__main__":
    # Đọc tên file gốc để xác định thư mục work
    original_filename = "translate_words_map_zh_tw"
    if os.path.exists("original_filename.txt"):
        with open("original_filename.txt", "r") as f:
            original_filename = f.read().strip()
    
    base_name = os.path.splitext(original_filename)[0]
    dat_dir = os.path.join("work", base_name)
    translation_tsv = "translation_vn.tsv"
    output_file = "translate_words_map_vn"
    
    if os.path.exists(dat_dir):
        apply_translation_to_dat(dat_dir, translation_tsv)
        pak_file(dat_dir, output_file)
    else:
        log(f"Missing dat directory: {dat_dir}")
