import os
import struct
import pyzstd
import csv

def log(msg):
    print(f"[PROCESS] {msg}")

def extract_file(input_file, output_dir):
    try:
        base_name = os.path.basename(input_file)
        output_subdir = os.path.join(output_dir, base_name)
        os.makedirs(output_subdir, exist_ok=True)
        
        with open(input_file, 'rb') as f:
            magic = f.read(4)
            if magic != b'\xEF\xBE\xAD\xDE':
                log(f"❌ Invalid file format (Magic mismatch): {input_file}")
                return None
            
            f.read(4)
            offset_count_bytes = f.read(4)
            offset_count = struct.unpack('<I', offset_count_bytes)[0] + 1
            
            log(f"Extracting {offset_count} blocks from {input_file}...")
            
            if offset_count == 1:
                comp_block_len = struct.unpack('<I', f.read(4))[0]
                comp_block = f.read(comp_block_len)
                header = comp_block[:9]
                comp_data_part = comp_block[9:]
                comp_type, comp_size, decomp_size = struct.unpack('<BII', header)
                if comp_type == 0x04:
                    decomp_data = pyzstd.decompress(comp_data_part)
                    with open(os.path.join(output_subdir, f"{base_name}_0.dat"), 'wb') as outf:
                        outf.write(decomp_data)
            else:
                offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(offset_count)]
                data_start = f.tell()
                for i in range(offset_count - 1):
                    f.seek(data_start + offsets[i])
                    block_len = offsets[i+1] - offsets[i]
                    comp_block = f.read(block_len)
                    if len(comp_block) < 9: continue
                    header = comp_block[:9]
                    comp_data_part = comp_block[9:]
                    comp_type, comp_size, decomp_size = struct.unpack('<BII', header)
                    if comp_type == 0x04:
                        decomp_data = pyzstd.decompress(comp_data_part)
                        with open(os.path.join(output_subdir, f"{base_name}_{i}.dat"), 'wb') as outf:
                            outf.write(decomp_data)
        return output_subdir
    except Exception as e:
        log(f"❌ Error during extraction: {e}")
        return None

def extract_text_to_tsv(input_dir, output_file):
    try:
        extracted_count = 0
        with open(output_file, 'w', encoding='utf-8', newline='') as outf:
            writer = csv.writer(outf, delimiter='\t')
            writer.writerow(["ID", "OriginalText"])
            for filename in sorted(os.listdir(input_dir)):
                if not filename.endswith('.dat') or filename.endswith('_0.dat'): continue
                with open(os.path.join(input_dir, filename), 'rb') as f:
                    data = f.read()
                    if len(data) < 4: continue
                    count_full = struct.unpack('<I', data[0:4])[0]
                    header_end = 4 + 4 + 4 + 12 + count_full + 17
                    
                    for i in range(count_full):
                        entry_pos = header_end + (i * 16)
                        if entry_pos + 16 > len(data): break
                        id_bytes = data[entry_pos:entry_pos+8].hex()
                        rel_offset = struct.unpack('<I', data[entry_pos+8:entry_pos+12])[0]
                        length = struct.unpack('<I', data[entry_pos+12:entry_pos+16])[0]
                        
                        text_pos = entry_pos + 12 + rel_offset
                        text = data[text_pos:text_pos+length].decode('utf-8', errors='ignore')
                        writer.writerow([id_bytes, text])
                        extracted_count += 1
        log(f"Successfully extracted {extracted_count} strings to {output_file}")
        return True
    except Exception as e:
        log(f"❌ Text extraction error: {e}")
        return False

if __name__ == "__main__":
    input_file = None
    exclude = ['LICENSE', 'README.md', 'requirements.txt', 'gemini_translate.py', 'process_game_file.py', 'repack_game_file.py', 'translation_vn.tsv', 'extracted_text.tsv', 'translate_words_map_vn', 'original_filename.txt']
    
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f not in exclude]
    for f in files:
        if f.startswith('translate_words_map'):
            input_file = f
            break
    if not input_file:
        for f in files:
            if '.' not in f:
                input_file = f
                break
                
    if input_file:
        log(f"Found original file: {input_file}")
        with open("original_filename.txt", "w") as f:
            f.write(input_file)
            
        dat_dir = extract_file(input_file, "work")
        if dat_dir:
            extract_text_to_tsv(dat_dir, "extracted_text.tsv")
            log("Extraction phase complete.")
    else:
        log("❌ No original game file found in the repository root.")
