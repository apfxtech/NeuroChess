import json
import os
import psutil
import numpy as np
import onnxruntime as rt
from scripts.engine import get_resource_path

class Model:
    _instances = {}
    def __new__(cls, path:str):
        if path not in cls._instances:
            instance = super(Model, cls).__new__(cls)
            cls._instances[path] = instance
        return cls._instances[path]

    def __init__(self, path:str):
        # Проверяем, инициализирован ли экземпляр ранее
        if hasattr(self, '_initialized'):
            return
        # Инициализация только для нового экземпляра
        self.path = path
        self.tokenizer = self.Tokenize(self)
        self.load()
        self._initialized = True

    def load(self):
        # Загружаем модель только если сессия ещё не создана
        if not hasattr(self, "session"):
            model_path = get_resource_path(self.path + "/model.onnx")
            self.session = rt.InferenceSession(model_path)
            self.input_name = self.session.get_inputs()[0].name

    def check(self, path):
        if hasattr(self._instances.get(path), "session"):
            return True
        
        model_path = get_resource_path(path + "/model.onnx")
        if not os.path.exists(model_path):
            return False
        
        memory = psutil.virtual_memory()
        size = os.path.getsize(model_path)
        return memory.available >= size * 2

    class Tokenize:
        def __init__(self, model):
            path = get_resource_path(model.path + "/tokenizer.json")
            with open(path, 'r') as t:
                self.jtokenizer = json.load(t)
                self.model = self.jtokenizer['model']['vocab']

        def ids(self, input_str):
            tokens = input_str.split()
            token_ids = [self.model.get(token, self.model["[UNK]"]) for token in tokens]
            return token_ids

        def str(self, input_ids):
            result = ""
            for token_id in input_ids:
                for key, value in self.model.items():
                    if value == token_id:
                        result += key + " "
                        break
            return result.strip()

    def generate(self, input_string):
        if not hasattr(self, "session"):
            self.load()

        token_ids = self.tokenizer.ids(input_string)
        input_array = np.array(token_ids, dtype=np.int64).reshape(1, -1)
        attention_mask = np.ones(input_array.shape, dtype=np.int64)
        position_ids = np.arange(input_array.shape[1]).reshape(1, -1)
        input_feed = {
            self.input_name: input_array,
            'attention_mask': attention_mask,
            'position_ids': position_ids
        }
        pred_onx = self.session.run(None, input_feed)[0]
        token_ids = np.argmax(pred_onx, axis=-1).flatten()
        decoded_text = self.tokenizer.str(token_ids)
        return decoded_text