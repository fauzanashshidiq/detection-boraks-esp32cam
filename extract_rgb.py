from argparse import ArgumentParser
from csv import DictWriter
from pathlib import Path
from PIL import Image, ImageStat


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_ppm(label):
    text = label.lower().replace("ppm", "")
    try:
        return int(text)
    except ValueError:
        return ""


def center_crop(image, ratio):
    if ratio >= 1:
        return image

    width, height = image.size
    crop_width = int(width * ratio)
    crop_height = int(height * ratio)
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    return image.crop((left, top, left + crop_width, top + crop_height))


def extract_image_rgb(path, crop_ratio):
    with Image.open(path) as image:
        rgb_image = image.convert("RGB")
        roi = center_crop(rgb_image, crop_ratio)
        stat = ImageStat.Stat(roi)
        red, green, blue = stat.mean
        return {
            "width": image.width,
            "height": image.height,
            "red": round(red, 3),
            "green": round(green, 3),
            "blue": round(blue, 3),
        }


def iter_images(dataset_dir):
    for path in sorted(dataset_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def main():
    parser = ArgumentParser(description="Ekstraksi rata-rata RGB dari gambar dataset.")
    parser.add_argument("--dataset", default="dataset", help="Folder dataset berisi subfolder label ppm.")
    parser.add_argument("--output", default="rgb_features.csv", help="File CSV hasil ekstraksi.")
    parser.add_argument(
        "--crop",
        type=float,
        default=1.0,
        help="Rasio crop tengah 0.1 sampai 1.0. Pakai 1.0 untuk seluruh gambar.",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset)
    output_path = Path(args.output)
    crop_ratio = max(0.1, min(1.0, args.crop))

    rows = []
    for image_path in iter_images(dataset_dir):
        label = image_path.parent.name
        values = extract_image_rgb(image_path, crop_ratio)
        rows.append(
            {
                "filename": image_path.name,
                "path": image_path.as_posix(),
                "label": label,
                "ppm": parse_ppm(label),
                "width": values["width"],
                "height": values["height"],
                "crop_ratio": crop_ratio,
                "red": values["red"],
                "green": values["green"],
                "blue": values["blue"],
            }
        )

    fieldnames = ["filename", "path", "label", "ppm", "width", "height", "crop_ratio", "red", "green", "blue"]
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Selesai ekstraksi {len(rows)} gambar ke {output_path}")


if __name__ == "__main__":
    main()
