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

def rgb_white_hot(arr: np.ndarray) -> np.ndarray:
    return np.repeat((normalize(arr)*255).astype(np.uint8), 3, axis=2)