from onnxruntime.quantization import quantize_dynamic, QuantType

# Конвертация модели в int8
quantize_dynamic(
    "resources\chess-o1\model.onnx",                
    "resources\chess-q2\model.onnx",      # Квантованная модель
    weight_type=QuantType.QInt4  # Тип квантования
)