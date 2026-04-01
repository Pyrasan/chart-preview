import re
from PIL import Image, ImageDraw, ImageFont
import sys
import os

def parse_osu_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cs = 4
    try:
        cs_match = re.search(r'CircleSize:(\d+)', content)
        if cs_match:
            cs = int(cs_match.group(1))
    except:
        pass
    
    if '[HitObjects]' not in content:
        return [], cs
    
    hit_objects_section = content.split('[HitObjects]')[1]
    lines = hit_objects_section.strip().split('\n')
    
    objects = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) >= 5:
            try:
                x = int(parts[0])
                time = int(parts[2])
                obj_type = int(parts[3])
                
                is_circle = (obj_type & 1) != 0
                is_slider = (obj_type & 2) != 0
                is_spinner = (obj_type & 8) != 0
                is_hold = (obj_type & 128) != 0
                
                end_time = time
                if (is_hold or is_spinner) and len(parts) > 5:
                    if ':' in parts[5]:
                        end_time = int(parts[5].split(':')[0])
                    else:
                        try:
                            end_time = int(parts[5])
                        except:
                            end_time = time
                
                lane = x // (512 // cs) if cs > 0 else x // 128
                
                objects.append({
                    'time': time,
                    'end_time': end_time,
                    'type': obj_type,
                    'is_circle': is_circle,
                    'is_slider': is_slider,
                    'is_hold': is_hold or is_spinner,
                    'lane': lane
                })
            except:
                continue
    
    return objects, cs

def generate_chart_preview(objects, num_keys, output_path, scale=2, spacing_ref=100, spacing_ref_ms=50):
    if not objects:
        print("No objects to render")
        return
    
    min_time = min(obj['time'] for obj in objects)
    max_time = max(obj['end_time'] for obj in objects)
    
    lane_width = 80 * scale
    col_width = num_keys * lane_width
    
    px_per_ms = spacing_ref / spacing_ref_ms
    
    total_height_needed = 0
    for i in range(len(objects) - 1):
        time_diff = objects[i+1]['time'] - objects[i]['time']
        if time_diff > 0:
            total_height_needed += time_diff * px_per_ms
    
    max_col_height = 4000 * scale
    min_col_height = 2000 * scale
    
    num_cols = max(1, int(total_height_needed / max_col_height) + 1)
    if num_cols > 30:
        num_cols = 30
    
    col_height = max(min_col_height, min(max_col_height, int(total_height_needed / num_cols)))
    if col_height < min_col_height:
        col_height = min_col_height
    
    canvas_width = num_cols * col_width + 60 * scale
    canvas_height = col_height + 80 * scale
    
    img = Image.new('RGB', (canvas_width, canvas_height), '#1a1a24')
    draw = ImageDraw.Draw(img)
    
    try:
        font_size = int(14 * scale)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    colors_by_keys = {
        4: [('#ffffff', '#ffffff'), ('#87ceeb', '#87ceeb'), ('#87ceeb', '#87ceeb'), ('#ffffff', '#ffffff')],
        5: [('#ffffff', '#ffffff'), ('#87ceeb', '#87ceeb'), ('#ffd700', '#ffd700'), ('#87ceeb', '#87ceeb'), ('#ffffff', '#ffffff')],
        6: [('#ffffff', '#ffffff'), ('#87ceeb', '#87ceeb'), ('#7fdbdb', '#7fdbdb'), ('#7fdbdb', '#7fdbdb'), ('#87ceeb', '#87ceeb'), ('#ffffff', '#ffffff')],
        7: [('#ffffff', '#ffffff'), ('#87ceeb', '#87ceeb'), ('#7fdbdb', '#7fdbdb'), ('#ffd700', '#ffd700'), ('#7fdbdb', '#7fdbdb'), ('#87ceeb', '#87ceeb'), ('#ffffff', '#ffffff')],
        8: [('#ffffff', '#ffffff'), ('#87ceeb', '#87ceeb'), ('#7fdbdb', '#7fdbdb'), ('#ffb6c1', '#ffb6c1'), ('#ffb6c1', '#ffb6c1'), ('#7fdbdb', '#7fdbdb'), ('#87ceeb', '#87ceeb'), ('#ffffff', '#ffffff')],
        9: [('#ffffff', '#ffffff'), ('#87ceeb', '#87ceeb'), ('#7fdbdb', '#7fdbdb'), ('#ffb6c1', '#ffb6c1'), ('#ffd700', '#ffd700'), ('#ffb6c1', '#ffb6c1'), ('#7fdbdb', '#7fdbdb'), ('#87ceeb', '#87ceeb'), ('#ffffff', '#ffffff')],
        10: [('#ffffff', '#ffffff'), ('#87ceeb', '#87ceeb'), ('#7fdbdb', '#7fdbdb'), ('#ffb6c1', '#ffb6c1'), ('#ffd700', '#ffd700'), ('#ffd700', '#ffd700'), ('#ffb6c1', '#ffb6c1'), ('#7fdbdb', '#7fdbdb'), ('#87ceeb', '#87ceeb'), ('#ffffff', '#ffffff')],
    }
    
    if num_keys in colors_by_keys:
        lane_colors = colors_by_keys[num_keys]
    else:
        default_colors = [
            ('#ff4757', '#ff6b7a'), ('#2ed573', '#5aff97'), ('#1e90ff', '#5ab8ff'),
            ('#ffa502', '#ffc04d'), ('#ff6b81', '#ff8fa3'), ('#7bed9f', '#a8f4be'),
            ('#70a1ff', '#96c2ff'), ('#eccc68', '#f0dc9c'), ('#ff7f50', '#ff9f7a'), ('#a55eea', '#c084f0')
        ]
        lane_colors = default_colors[:num_keys]
    
    section_time = (max_time - min_time) / num_cols
    
    for col in range(num_cols):
        col_x = col * col_width + 30 * scale
        
        for i in range(num_keys):
            x = col_x + i * lane_width
            draw.rectangle([x + 4 * scale, 60 * scale, x + lane_width - 4 * scale, canvas_height - 20 * scale], fill='#252533')
            draw.line([x + 4 * scale, 60 * scale, x + 4 * scale, canvas_height - 20 * scale], fill='#353548', width=2 * scale)
        
        draw.line([col_x, 60 * scale, col_x, canvas_height - 20 * scale], fill='#4a4a65', width=3 * scale)
        draw.line([col_x + col_width, 60 * scale, col_x + col_width, canvas_height - 20 * scale], fill='#4a4a65', width=3 * scale)
        
        section_start = col * section_time
        section_end = (col + 1) * section_time
        start_sec = (min_time + section_start) / 1000
        end_sec = (min_time + section_end) / 1000
        draw.text((col_x + 10 * scale, 20 * scale), f"{int(start_sec)}s", fill='#7a7a8c', font=font)
        if col == num_cols - 1:
            draw.text((col_x + col_width - 35 * scale, 20 * scale), f"{int(end_sec)}s", fill='#7a7a8c', font=font)
    
    available_height = canvas_height - 80 * scale
    
    for i in range(8):
        y = 60 * scale + i * ((available_height) // 7)
        draw.line([30 * scale, y, canvas_width - 30 * scale, y], fill='#2a2a3c', width=1 * scale)
    
    def get_col_and_y(obj_time, col_height, section_time, min_time, px_per_ms, num_cols):
        col = int((obj_time - min_time) / section_time)
        if col >= num_cols:
            col = num_cols - 1
        
        section_start_time = min_time + col * section_time
        time_in_section = obj_time - section_start_time
        
        y_pos = 60 * scale + int(time_in_section * px_per_ms)
        y_pos = max(60 * scale, min(y_pos, canvas_height - 20 * scale))
        
        return col, y_pos
    
    for obj in objects:
        col, y_pos = get_col_and_y(obj['time'], col_height, section_time, min_time, px_per_ms, num_cols)
        
        col_x = col * col_width + 30 * scale
        x_pos = col_x + obj['lane'] * lane_width
        
        if obj['lane'] < num_keys:
            fill_color, outline_color = lane_colors[obj['lane']]
        else:
            fill_color = outline_color = '#ffffff'
        
        center_x = x_pos + lane_width // 2
        outer_radius = 22 * scale
        inner_radius = 10 * scale
        
        if obj['is_hold']:
            _, end_y_pos = get_col_and_y(obj['end_time'], col_height, section_time, min_time, px_per_ms, num_cols)
            
            if end_y_pos > y_pos + 15 * scale:
                body_top = y_pos + 6 * scale
                body_bottom = end_y_pos - 6 * scale
                
                if body_bottom > body_top:
                    draw.rectangle([x_pos + 12 * scale, body_top, x_pos + lane_width - 12 * scale, body_bottom], fill=fill_color)
                
                draw.ellipse([x_pos + 6 * scale, y_pos, x_pos + lane_width - 6 * scale, y_pos + 14 * scale], fill=fill_color, outline=outline_color, width=2 * scale)
                draw.ellipse([x_pos + 6 * scale, end_y_pos - 14 * scale, x_pos + lane_width - 6 * scale, end_y_pos], fill=fill_color, outline=outline_color, width=2 * scale)
                
                draw.ellipse([x_pos + 14 * scale, y_pos + 2 * scale, x_pos + lane_width - 14 * scale, y_pos + 12 * scale], fill='#ffffff')
                draw.ellipse([x_pos + 14 * scale, end_y_pos - 12 * scale, x_pos + lane_width - 14 * scale, end_y_pos - 2 * scale], fill='#ffffff')
        
        elif obj['is_slider']:
            draw.ellipse([center_x - 16 * scale, y_pos - 16 * scale, center_x + 16 * scale, y_pos + 16 * scale], fill=fill_color, outline=outline_color, width=2 * scale)
        else:
            draw.ellipse([center_x - outer_radius, y_pos - outer_radius, center_x + outer_radius, y_pos + outer_radius], outline=outline_color, width=3 * scale)
            draw.ellipse([center_x - inner_radius, y_pos - inner_radius, center_x + inner_radius, y_pos + inner_radius], fill='#ffffff')
    
    img.save(output_path, quality=95)
    print(f"Chart preview saved to: {output_path}")
    print(f"Total objects: {len(objects)}, Keys: {num_keys}, Columns: {num_cols}")
    print(f"Spacing: {spacing_ref}px per {spacing_ref_ms}ms (1/4 note)")
    print(f"Time range: {min_time/1000:.1f}s - {max_time/1000:.1f}s ({(max_time-min_time)/1000:.1f}s)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_preview.py <osu_file> [num_keys] [scale] [spacing_px] [spacing_ms]")
        print("")
        print("Parameters:")
        print("  osu_file    - Path to .osu file")
        print("  num_keys    - Number of keys (4-10, default: 4)")
        print("  scale       - Resolution scale 1-4 (default: 2)")
        print("  spacing_px  - Pixels for reference spacing (default: 100)")
        print("  spacing_ms   - Reference time in ms (default: 50)")
        print("")
        print("Example: python generate_preview.py song.osu 4 2 100 50")
        print("  = 4K, 2x scale, 100px per 50ms (1/4 note at ~200BPM)")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    num_keys = 4
    scale = 2
    spacing_px = 100
    spacing_ms = 50
    
    if len(sys.argv) > 2:
        try:
            num_keys = int(sys.argv[2])
        except:
            num_keys = 4
    if len(sys.argv) > 3:
        try:
            scale = int(sys.argv[3])
        except:
            scale = 2
    if len(sys.argv) > 4:
        try:
            spacing_px = int(sys.argv[4])
        except:
            spacing_px = 100
    if len(sys.argv) > 5:
        try:
            spacing_ms = int(sys.argv[5])
        except:
            spacing_ms = 50
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)
    
    objects, cs = parse_osu_file(filepath)
    print(f"Parsed {len(objects)} hit objects, CircleSize: {cs}")
    
    if cs > num_keys:
        num_keys = cs
        print(f"Using {num_keys} keys based on CircleSize")
    
    output_path = f"chart_preview_{num_keys}k.png"
    generate_chart_preview(objects, num_keys, output_path, scale, spacing_px, spacing_ms)