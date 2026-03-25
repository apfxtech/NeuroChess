import asyncio
import os, sys

def get_resource_path(relative_path: str, not_exist: bool = False) -> str:
    """Получить абсолютный путь к ресурсу с приоритетом внешних файлов"""
    # Нормализуем относительный путь (исправляем разделители)
    relative_path = os.path.normpath(relative_path)
    
    # Базовый путь для режима разработки
    full_path = os.path.normpath(os.path.join(os.path.abspath('.'), relative_path))
    
    # Проверяем режим исполнения (EXE или скрипт)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        external_path = os.path.normpath(os.path.join(exe_dir, relative_path))
        
        # Проверяем существование внешнего пути
        if os.path.exists(external_path):
            return external_path
        
        # Путь для запакованных ресурсов (PyInstaller)
        full_path = os.path.normpath(os.path.join(sys._MEIPASS, relative_path))
    
    # Возвращаем путь, даже если не существует (если указано not_exist=True)
    if os.path.exists(full_path) or not_exist:
        return full_path

class EventEngine:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EventEngine, cls).__new__(cls, *args, **kwargs)
            cls._instance.listeners = {}
        return cls._instance

    def on(self, event):
        if event not in self.listeners:
            self.listeners[event] = []

        def wrapper(func):
            if asyncio.iscoroutinefunction(func):
                self.listeners[event].append(func)
            else:
                raise TypeError(f"Handler for event '{event}' must be an async function")
            return func  # Возвращаем саму функцию, а не обёртку

        return wrapper

    async def trigger(self, event, *args, **kwargs):
        if event in self.listeners:
            handlers = [func(*args, **kwargs) for func in self.listeners[event]]
            await asyncio.gather(*handlers)
    
    def remove(self, event, func):
        if event in self.listeners:
            if func in self.listeners[event]:
                self.listeners[event].remove(func)
            else:
                print(f"Handler {func.__name__} not found in event {event}")
        else:
            print(f"Event {event} not found")

events_engine = EventEngine()
