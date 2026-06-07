import argparse
import os
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


CLASS_NAMES = [
    "0ppm",
    "100ppm",
    "250ppm",
    "500ppm",
    "750ppm",
    "1000ppm",
    "1250ppm",
    "1500ppm",
    "1750ppm",
    "2000ppm",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def segment_curcumin_paper(image_bgr, output_size=None, return_mask=False):
    """Find yellow/orange curcumin paper, crop to it, and fallback to center crop."""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # OpenCV hue scale is 0-179. This wider range covers yellow paper and
    # orange/red-brown borax reaction areas better than H 20-40 alone.
    lower = np.array([8, 35, 35], dtype=np.uint8)
    upper = np.array([70, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    crop_mask = None
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 100:
            x, y, w, h = cv2.boundingRect(largest)
            crop = image_bgr[y : y + h, x : x + w]
            crop_mask = mask[y : y + h, x : x + w]
        else:
            crop = center_crop(image_bgr)
    else:
        crop = center_crop(image_bgr)

    if output_size is not None:
        crop = cv2.resize(crop, output_size, interpolation=cv2.INTER_AREA)
        if crop_mask is not None:
            crop_mask = cv2.resize(crop_mask, output_size, interpolation=cv2.INTER_NEAREST)
    if return_mask:
        return crop, crop_mask
    return crop


def center_crop(image_bgr, ratio=0.6):
    height, width = image_bgr.shape[:2]
    crop_w = int(width * ratio)
    crop_h = int(height * ratio)
    x1 = max((width - crop_w) // 2, 0)
    y1 = max((height - crop_h) // 2, 0)
    return image_bgr[y1 : y1 + crop_h, x1 : x1 + crop_w]


def iter_dataset_images(dataset_dir):
    dataset_dir = Path(dataset_dir)
    for class_name in CLASS_NAMES:
        class_dir = dataset_dir / class_name
        if not class_dir.exists():
            continue
        for path in sorted(class_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                yield path, class_name


def extract_rgb_features(dataset_dir, output_csv):
    rows = []
    for image_path, class_name in iter_dataset_images(dataset_dir):
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            print(f"Skip unreadable image: {image_path}")
            continue

        crop_bgr, crop_mask = segment_curcumin_paper(image_bgr, return_mask=True)
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        if crop_mask is not None and np.count_nonzero(crop_mask) > 0:
            r_mean, g_mean, b_mean = crop_rgb[crop_mask > 0].mean(axis=0)
        else:
            r_mean, g_mean, b_mean = crop_rgb.reshape(-1, 3).mean(axis=0)

        rows.append(
            {
                "filename": image_path.name,
                "kelas": class_name,
                "R_mean": round(float(r_mean), 4),
                "G_mean": round(float(g_mean), 4),
                "B_mean": round(float(b_mean), 4),
            }
        )

    df = pd.DataFrame(rows, columns=["filename", "kelas", "R_mean", "G_mean", "B_mean"])
    df.to_csv(output_csv, index=False)
    print(f"Saved {len(df)} rows to {output_csv}")
    return df


def main():
    parser = argparse.ArgumentParser(description="Extract mean RGB from segmented curcumin paper.")
    parser.add_argument("--dataset", default="dataset", help="Dataset folder, e.g. dataset")
    parser.add_argument("--output", default="rgb_features.csv", help="Output CSV path")
    args = parser.parse_args()

    if not os.path.isdir(args.dataset):
        raise FileNotFoundError(f"Dataset folder not found: {args.dataset}")

    extract_rgb_features(args.dataset, args.output)


if __name__ == "__main__":
    main()
