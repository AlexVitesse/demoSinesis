import yt_dlp
import os
from pathlib import Path
import threading
from functools import lru_cache
import json
import re

# Configuración inicial
downloads_lock = threading.Lock()
Path("temp_uploads").mkdir(exist_ok=True)

class YouTubeProcessor:
    def __init__(self):
        self.downloads_lock = downloads_lock
    
    def clean_subtitle_file(self, sub_file, txt_file):
        """Limpia archivos de subtítulos eliminando metadatos y marcas de tiempo"""
        if sub_file.endswith('.vtt') or sub_file.endswith('.srt'):
            with open(sub_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                    continue
                if line.isdigit():
                    continue
                if '-->' in line:
                    continue
                    
                line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}><c>', '', line)
                line = re.sub(r'</c>', '', line)
                line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', line)
                line = re.sub(r'<[^>]+>', '', line)
                
                if line.strip():
                    clean_lines.append(line.strip())
            
            final_lines = []
            previous_line = ""
            for line in clean_lines:
                if line != previous_line:
                    final_lines.append(line)
                    previous_line = line
            
            clean_content = '\n'.join(final_lines)
            clean_content = re.sub(r'\s+', ' ', clean_content)
            clean_content = re.sub(r'\n\s*\n', '\n', clean_content)
            
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(clean_content.strip())

    @lru_cache(maxsize=128)
    def get_video_info(self, url):
        """Obtiene información del video sin descargarlo"""
        ydl_opts = {'quiet': True, 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            raise Exception(f"Error al obtener información: {str(e)}")

    def download_subs(self, url, lang='es', format='txt'):
        """Descarga y procesa subtítulos del video"""
        try:
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': [lang],
                'skip_download': True,
                'outtmpl': 'temp_uploads/%(title)s',
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                base_name = ydl.prepare_filename(info)
                
                sub_file = None
                for ext in ['.vtt', '.srt', '.json', '.ttml']:
                    possible_file = f"{base_name}.{lang}{ext}"
                    if os.path.exists(possible_file):
                        sub_file = possible_file
                        break
                
                if not sub_file:
                    raise Exception("No se encontraron subtítulos para este video")
                    
                if format == 'txt':
                    txt_file = f"{base_name}.{lang}.txt"
                    
                    if sub_file.endswith('.vtt') or sub_file.endswith('.srt'):
                        self.clean_subtitle_file(sub_file, txt_file)
                    elif sub_file.endswith('.json'):
                        with open(sub_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        text = '\n'.join(segment['text'] for segment in data['segments'])
                        with open(txt_file, 'w', encoding='utf-8') as f:
                            f.write(text)
                    
                    os.remove(sub_file)
                    return txt_file
                
                return sub_file
                
        except Exception as e:
            raise Exception(f"Error al descargar subtítulos: {str(e)}")

    def format_duration(self, duration):
        """Formatea la duración en minutos:segundos"""
        if duration:
            return f"{duration//60}:{duration%60:02d}"
        return "N/A"

    def format_date(self, upload_date):
        """Formatea la fecha de subida"""
        if upload_date and len(upload_date) >= 8:
            return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        return "N/A"

    def format_views(self, view_count):
        """Formatea el número de vistas"""
        if view_count:
            if view_count >= 1000000:
                return f"{view_count/1000000:.1f}M"
            elif view_count >= 1000:
                return f"{view_count/1000:.1f}K"
            else:
                return str(view_count)
        return "N/A"