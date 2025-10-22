import numpy as np
import cv2

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

def rgb_white_hot(arr: np.ndarray) -> np.ndarray:
    return np.repeat((normalize(arr)*255).astype(np.uint8), 3, axis=2)

def rgb_black_hot(arr: np.ndarray) -> np.ndarray:
    return np.repeat(((1-normalize(arr))*255).astype(np.uint8), 3, axis=2)

def rgb_colormap_cv(arr: np.ndarray, cmap=cv2.COLORMAP_INFERNO) -> np.ndarray:
    arr_uint8 = np.clip(normalize(arr) * 255, 0, 255).astype(np.uint8)
    bgr = cv2.applyColorMap(arr_uint8, cmap)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb