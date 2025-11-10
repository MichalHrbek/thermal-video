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
    return np.repeat((arr*255).astype(np.uint8), 3, axis=2)

def rgb_black_hot(arr: np.ndarray) -> np.ndarray:
    return np.repeat(((1-arr)*255).astype(np.uint8), 3, axis=2)

def rgb_colormap_cv(arr: np.ndarray, cmap=cv2.COLORMAP_INFERNO) -> np.ndarray:
    arr_uint8 = np.clip(arr * 255, 0, 255).astype(np.uint8)
    bgr = cv2.applyColorMap(arr_uint8, cmap)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb

COLOR_PALETTES = [
    ("White hot",           rgb_white_hot),
    ("Black hot",           rgb_black_hot),
    ("CV2_AUTUMN",          lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_AUTUMN)),
    ("CV2_BONE",            lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_BONE)),
    ("CV2_JET",             lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_JET)),
    ("CV2_WINTER",          lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_WINTER)),
    ("CV2_RAINBOW",         lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_RAINBOW)),
    ("CV2_OCEAN",           lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_OCEAN)),
    ("CV2_SUMMER",          lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_SUMMER)),
    ("CV2_SPRING",          lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_SPRING)),
    ("CV2_COOL",            lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_COOL)),
    ("CV2_HSV",             lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_HSV)),
    ("CV2_PINK",            lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_PINK)),
    ("CV2_HOT",             lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_HOT)),
    ("CV2_PARULA",          lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_PARULA)),
    ("CV2_MAGMA",           lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_MAGMA)),
    ("CV2_INFERNO",         lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_INFERNO)),
    ("CV2_PLASMA",          lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_PLASMA)),
    ("CV2_VIRIDIS",         lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_VIRIDIS)),
    ("CV2_CIVIDIS",         lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_CIVIDIS)),
    ("CV2_TWILIGHT",        lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_TWILIGHT)),
    ("CV2_TWILIGHT_SHIFTED",lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_TWILIGHT_SHIFTED)),
    ("CV2_TURBO",           lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_TURBO)),
    ("CV2_DEEPGREEN",       lambda arr: rgb_colormap_cv(arr, cv2.COLORMAP_DEEPGREEN)),
]

COLOR_SCALES = [
    ("Linear", lambda arr: normalize(arr)),
    ("sqrt", lambda arr: np.sqrt(normalize(arr))),
    ("x^2", lambda arr: np.square(normalize(arr))),
]