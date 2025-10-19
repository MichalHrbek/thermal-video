import cv2
import numpy as np

def normalize(arr: np.ndarray) -> np.ndarray:
    min_ = np.min(arr)
    max_ = np.max(arr)
    if max_ == min_:
        return np.zeros_like(arr)
    
    return (arr - min_) / (max_ - min_)

def normalize_on_range(arr: np.ndarray, min_: float, max_: float) -> np.ndarray:
    if max_ == min_:
        return np.zeros_like(arr)
    
    return (arr - min_) / (max_ - min_)

def bgr_white_hot(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor((img*255.0).astype(np.uint8), cv2.COLOR_GRAY2BGR)