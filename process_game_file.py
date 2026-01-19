import os
import struct
import pyzstd
import csv

def log(msg):
    print(f"[PROCESS] {msg}")

def extract_file(input_file, output_dir):
    try:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_subdir = os.path.join(output_dir, base_name)
        os.makedirs(output_subdir, exist_ok=True)
        
        with open(input_file, 'rb') as f:
            magic = f.read(4)
            if magic != b'\xEF\xBE\xAD\xDE':
                log(f"❌ Invalid file format: {input_file}")
                return False
            
            f.read(4)
            offset_count_bytes = f.read(4)
            offset_count = struct.unpack('<I', offset_count_bytes)[0] + 1
            
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
        log(f"❌ Error: {e}")
        return None

def extract_text_to_tsv(input_dir, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as outf:
            writer = csv.writer(outf, delimiter='\t')
            writer.writerow(["ID", "OriginalText"])
            for filename in sorted(os.listdir(input_dir)):
                if not filename.endswith('.dat') or filename.endswith('_0.dat'): continue
                with open(os.path.join(input_dir, filename), 'rb') as f:
                    count_full = struct.unpack('<I', f.read(4))[0]
                    f.read(20)
                    f.read(count_full)
                    f.read(17)
                    data_start = f.tell()
                    for i in range(count_full):
                        f.seek(data_start + (i * 16))
                        id_bytes = f.read(8).hex()
                        offset_text = struct.unpack('<I', f.read(4))[0]
                        length = struct.unpack('<I', f.read(4))[0]
                        f.seek(f.tell() - 8 + offset_text)
                        text = f.read(length).decode('utf-8', errors='ignore')
                        writer.writerow([id_bytes, text])
        return True
    except Exception as e:
        log(f"❌ Text extraction error: {e}")
        return False

if __name__ == "__main__":
    # Tìm file không có đuôi trong thư mục gốc
    input_file = None
    for f in os.listdir('.'):
        if os.path.isfile(f) and '.' not in f and f not in ['LICENSE', 'README']:
            input_file = f
            break
    
    if input_file:
        log(f"Processing original file: {input_file}")
        dat_dir = extract_file(input_file, "work")
        if dat_dir:
            extract_text_to_tsv(dat_dir, "extracted_text.tsv")
            log("Extraction complete. Ready for translation.")
    else:
        log("No original game file found.")
