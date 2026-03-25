import sys, os

def get_resource_path(relative_path):
    """Получить абсолютный путь к ресурсу с приоритетом внешних файлов"""
    full_path = os.path.join(os.path.abspath('.'), relative_path)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        external_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(external_path):
            return external_path
        
        full_path = os.path.join(sys._MEIPASS, relative_path)
    
    if os.path.exists(full_path):
        return full_path