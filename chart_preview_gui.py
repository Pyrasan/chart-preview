import re
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox
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

def parse_hitobjects_text(text):
    objects = []
    lines = text.strip().split('\n')
    
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
                
                lane = x // 128
                
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
    
    return objects

def generate_chart_preview(objects, num_keys, output_path, scale, spacing_px, spacing_ms, col_gap=20, canvas_height=2000):
    if not objects:
        return False
    
    min_time = min(obj['time'] for obj in objects)
    max_time = max(obj['end_time'] for obj in objects)
    total_time = max_time - min_time
    
    lane_width = 80 * scale
    col_width = num_keys * lane_width
    
    px_per_ms = spacing_px / spacing_ms
    
    max_col_height_px = canvas_height * scale
    
    ms_per_col = max_col_height_px / px_per_ms
    
    col_data = {}
    for obj in objects:
        col = int((obj['time'] - min_time) / ms_per_col)
        if col not in col_data:
            col_data[col] = {'min_time': obj['time'], 'max_time': obj['end_time']}
        else:
            col_data[col]['min_time'] = min(col_data[col]['min_time'], obj['time'])
            col_data[col]['max_time'] = max(col_data[col]['max_time'], obj['end_time'])
    
    num_cols = max(col_data.keys()) + 1 if col_data else 1
    
    section_time = ms_per_col
    
    col_gap_px = col_gap * scale
    canvas_width = num_cols * col_width + (num_cols - 1) * col_gap_px + 60 * scale
    
    max_col_h = canvas_height * scale
    img_height = max_col_h + 80 * scale
    
    img = Image.new('RGB', (canvas_width, img_height), '#1a1a24')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", int(14 * scale))
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
    
    col_height_px = canvas_height * scale
    
    for col in range(num_cols):
        col_x = col * (col_width + col_gap_px) + 30 * scale
        
        col_top = canvas_height + 40 * scale
        col_bottom = col_top - col_height_px
        
        for i in range(num_keys):
            x = col_x + i * lane_width
            draw.rectangle([x + 4 * scale, col_bottom, x + lane_width - 4 * scale, col_top], fill='#252533')
            draw.line([x + 4 * scale, col_bottom, x + 4 * scale, col_top], fill='#353548', width=2 * scale)
        
        draw.line([col_x, col_bottom, col_x, col_top], fill='#4a4a65', width=3 * scale)
        draw.line([col_x + col_width, col_bottom, col_x + col_width, col_top], fill='#4a4a65', width=3 * scale)
        
        section_start_time = min_time + col * section_time
        section_end_time = section_start_time + section_time
        start_sec = section_start_time / 1000
        end_sec = section_end_time / 1000
        draw.text((col_x + 10 * scale, col_bottom + 10 * scale), f"{int(start_sec)}s", fill='#7a7a8c', font=font)
        draw.text((col_x + col_width - 35 * scale, col_bottom + 10 * scale), f"{int(end_sec)}s", fill='#7a7a8c', font=font)
    
    for col in range(num_cols):
        col_top = canvas_height + 40 * scale
        col_bottom = col_top - col_height_px
        
        for i in range(8):
            y = col_bottom + i * (col_height_px // 7)
            col_x = col * (col_width + col_gap_px) + 30 * scale
            draw.line([col_x, y, col_x + col_width, y], fill='#2a2a3c', width=1 * scale)
    
    def get_col_and_y(obj_time):
        col = int((obj_time - min_time) / section_time)
        if col >= num_cols:
            col = num_cols - 1
        
        time_in_section = obj_time - min_time - col * section_time
        
        y_pos = (canvas_height + 40 * scale) - int(time_in_section * px_per_ms)
        
        return col, y_pos
    
    for obj in objects:
        col, y_pos = get_col_and_y(obj['time'])
        
        col_x = col * (col_width + col_gap_px) + 30 * scale
        x_pos = col_x + obj['lane'] * lane_width
        
        if obj['lane'] < num_keys:
            fill_color, outline_color = lane_colors[obj['lane']]
        else:
            fill_color = outline_color = '#ffffff'
        
        center_x = x_pos + lane_width // 2
        bar_height = 20 * scale
        bar_top = y_pos - bar_height // 2
        bar_bottom = y_pos + bar_height // 2
        
        if obj['is_hold']:
            hold_duration = obj['end_time'] - obj['time']
            if hold_duration > 10:
                start_col, start_y = get_col_and_y(obj['time'])
                end_col, end_y = get_col_and_y(obj['end_time'])
                
                lane_x = obj['lane'] * lane_width
                
                if start_col == end_col:
                    start_x = start_col * (col_width + col_gap_px) + 30 * scale + lane_x
                    top = min(start_y, end_y) - bar_height // 2
                    bottom = max(start_y, end_y) + bar_height // 2
                    draw.rectangle([start_x + 4 * scale, top, start_x + lane_width - 4 * scale, bottom], fill=fill_color)
                else:
                    for c in range(start_col, end_col + 1):
                        col_x = c * (col_width + col_gap_px) + 30 * scale
                        lane_start_x = col_x + lane_x
                        col_top = canvas_height + 40 * scale
                        col_bottom = col_top - col_height_px
                        
                        if c == start_col:
                            top = min(start_y, col_bottom)
                            bottom = max(start_y, col_bottom)
                            draw.rectangle([lane_start_x + 4 * scale, top - bar_height // 2, lane_start_x + lane_width - 4 * scale, bottom + bar_height // 2], fill=fill_color)
                        elif c == end_col:
                            top = min(col_top, end_y)
                            bottom = max(col_top, end_y)
                            draw.rectangle([lane_start_x + 4 * scale, top - bar_height // 2, lane_start_x + lane_width - 4 * scale, bottom + bar_height // 2], fill=fill_color)
                        else:
                            draw.rectangle([lane_start_x + 4 * scale, col_bottom - bar_height // 2, lane_start_x + lane_width - 4 * scale, col_top + bar_height // 2], fill=fill_color)
        
        elif obj['is_slider']:
            draw.rectangle([x_pos + 4 * scale, bar_top, x_pos + lane_width - 4 * scale, bar_bottom], fill=fill_color)
        else:
            draw.rectangle([x_pos + 4 * scale, bar_top, x_pos + lane_width - 4 * scale, bar_bottom], fill=fill_color)
    
    img.save(output_path, quality=95)
    return True

class ChartPreviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("osu! Chart Preview Generator")
        self.root.geometry("450x650")
        self.root.configure(bg='#1a1a24')
        
        self.file_path = tk.StringVar()
        
        title_label = tk.Label(root, text="osu! Chart Preview Generator", font=("Arial", 18, "bold"), bg='#1a1a24', fg='#ffffff')
        title_label.pack(pady=15)
        
        input_mode_frame = tk.Frame(root, bg='#1a1a24')
        input_mode_frame.pack(pady=5, padx=20, fill='x')
        
        self.input_mode = tk.StringVar(value="file")
        tk.Radiobutton(input_mode_frame, text="Load File", variable=self.input_mode, value="file", bg='#1a1a24', fg='#aaaaaa', selectcolor='#252533', command=self.toggle_input).pack(side='left', padx=10)
        tk.Radiobutton(input_mode_frame, text="Paste HitObjects", variable=self.input_mode, value="paste", bg='#1a1a24', fg='#aaaaaa', selectcolor='#252533', command=self.toggle_input).pack(side='left', padx=10)
        
        self.file_frame = tk.Frame(root, bg='#1a1a24')
        self.file_frame.pack(pady=5, padx=20, fill='x')
        
        tk.Label(self.file_frame, text="OSU File:", bg='#1a1a24', fg='#aaaaaa').pack(side='left')
        
        self.file_entry = tk.Entry(self.file_frame, textvariable=self.file_path, width=25, bg='#252533', fg='#ffffff', insertbackground='#ffffff')
        self.file_entry.pack(side='left', padx=5)
        
        tk.Button(self.file_frame, text="Browse", command=self.browse_file, bg='#3a3a5c', fg='#ffffff').pack(side='left')
        
        self.paste_frame = tk.Frame(root, bg='#1a1a24')
        
        tk.Label(self.paste_frame, text="Paste [HitObjects] content:", bg='#1a1a24', fg='#aaaaaa').pack(anchor='w')
        
        self.hitobjects_text = tk.Text(self.paste_frame, width=40, height=6, bg='#252533', fg='#ffffff', insertbackground='#ffffff')
        self.hitobjects_text.pack(pady=5)
        
        settings_frame = tk.LabelFrame(root, text="Settings", bg='#1a1a24', fg='#ffffff', font=("Arial", 12))
        settings_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(settings_frame, text="Number of Keys:", bg='#1a1a24', fg='#aaaaaa').grid(row=0, column=0, sticky='w', pady=5)
        self.keys_var = tk.StringVar(value="4")
        keys_spin = tk.Spinbox(settings_frame, from_=4, to=10, textvariable=self.keys_var, width=10, bg='#252533', fg='#ffffff')
        keys_spin.grid(row=0, column=1, sticky='w', pady=5)
        
        tk.Label(settings_frame, text="Spacing (px):", bg='#1a1a24', fg='#aaaaaa').grid(row=1, column=0, sticky='w', pady=5)
        self.spacing_px_var = tk.StringVar(value="100")
        spacing_px_entry = tk.Entry(settings_frame, textvariable=self.spacing_px_var, width=12, bg='#252533', fg='#ffffff', insertbackground='#ffffff')
        spacing_px_entry.grid(row=1, column=1, sticky='w', pady=5)
        
        tk.Label(settings_frame, text="Reference (ms):", bg='#1a1a24', fg='#aaaaaa').grid(row=2, column=0, sticky='w', pady=5)
        self.spacing_ms_var = tk.StringVar(value="50")
        spacing_ms_entry = tk.Entry(settings_frame, textvariable=self.spacing_ms_var, width=12, bg='#252533', fg='#ffffff', insertbackground='#ffffff')
        spacing_ms_entry.grid(row=2, column=1, sticky='w', pady=5)
        
        tk.Label(settings_frame, text="Column Gap (px):", bg='#1a1a24', fg='#aaaaaa').grid(row=3, column=0, sticky='w', pady=5)
        self.col_gap_var = tk.StringVar(value="20")
        col_gap_entry = tk.Entry(settings_frame, textvariable=self.col_gap_var, width=12, bg='#252533', fg='#ffffff', insertbackground='#ffffff')
        col_gap_entry.grid(row=3, column=1, sticky='w', pady=5)
        
        tk.Label(settings_frame, text="Canvas Height (px):", bg='#1a1a24', fg='#aaaaaa').grid(row=4, column=0, sticky='w', pady=5)
        self.canvas_height_var = tk.StringVar(value="2000")
        canvas_height_entry = tk.Entry(settings_frame, textvariable=self.canvas_height_var, width=12, bg='#252533', fg='#ffffff', insertbackground='#ffffff')
        canvas_height_entry.grid(row=4, column=1, sticky='w', pady=5)
        
        tk.Label(settings_frame, text="(50ms ≈ 1/4 note at 200BPM)", bg='#1a1a24', fg='#666666', font=("Arial", 9)).grid(row=5, column=0, columnspan=2, sticky='w', padx=5)
        
        self.generate_btn = tk.Button(root, text="Generate Preview", command=self.generate, bg='#2ed573', fg='#ffffff', font=("Arial", 14, "bold"), height=2)
        self.generate_btn.pack(pady=15, padx=20, fill='x')
        
        self.status_label = tk.Label(root, text="", bg='#1a1a24', fg='#aaaaaa')
        self.status_label.pack(pady=5)
    
    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("osu files", "*.osu")])
        if filename:
            self.file_path.set(filename)
    
    def toggle_input(self):
        if self.input_mode.get() == "file":
            self.file_frame.pack()
            self.paste_frame.pack_forget()
        else:
            self.file_frame.pack_forget()
            self.paste_frame.pack(pady=5, padx=20, fill='x')
    
    def set_preset(self, px, ms):
        self.spacing_px_var.set(str(px))
        self.spacing_ms_var.set(str(ms))
    
    def generate(self):
        if self.input_mode.get() == "file":
            filepath = self.file_path.get()
            if not filepath:
                messagebox.showerror("Error", "Please select an osu file")
                return
            
            if not os.path.exists(filepath):
                messagebox.showerror("Error", "File not found")
                return
            
            objects, cs = parse_osu_file(filepath)
        else:
            hitobjects_text = self.hitobjects_text.get("1.0", tk.END).strip()
            if not hitobjects_text:
                messagebox.showerror("Error", "Please paste HitObjects content")
                return
            
            objects = parse_hitobjects_text(hitobjects_text)
            if not objects:
                messagebox.showerror("Error", "Invalid HitObjects format")
                return
            
            cs = 4
        
        try:
            num_keys = int(self.keys_var.get())
            spacing_px = int(self.spacing_px_var.get())
            spacing_ms = int(self.spacing_ms_var.get())
            col_gap = int(self.col_gap_var.get())
            canvas_height = int(self.canvas_height_var.get())
            scale = 1
        except ValueError:
            messagebox.showerror("Error", "Invalid settings values")
            return
        
        self.status_label.config(text="Generating...")
        self.root.update()
        
        if cs > num_keys:
            num_keys = cs
        
        output_path = f"chart_preview_{num_keys}k.png"
        
        success = generate_chart_preview(objects, num_keys, output_path, scale, spacing_px, spacing_ms, col_gap, canvas_height)
        
        if success:
            self.status_label.config(text=f"Saved to: {output_path}")
            messagebox.showinfo("Success", f"Chart preview saved to:\n{output_path}")
            os.startfile(output_path) if os.name == 'nt' else None
        else:
            self.status_label.config(text="Error generating preview")
            messagebox.showerror("Error", "Failed to generate preview")

if __name__ == '__main__':
    root = tk.Tk()
    app = ChartPreviewApp(root)
    root.mainloop()