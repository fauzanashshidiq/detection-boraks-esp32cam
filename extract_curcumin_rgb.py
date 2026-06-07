from argparse import ArgumentParser
from csv import DictWriter
from pathlib import Path
from colorsys import rgb_to_hsv
from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_ppm(label):
    text = label.lower().replace("ppm", "")
    try:
        return int(text)
    except ValueError:
        return ""


def is_paper_pixel(red, green, blue):
    total = red + green + blue
    if total < 80:
        return False

    hue, saturation, value = rgb_to_hsv(red / 255, green / 255, blue / 255)
    hue_degrees = hue * 360

    # Curcumin paper is usually yellow, orange, or brown: saturated and low in blue.
    return 8 <= hue_degrees <= 70 and saturation >= 0.25 and value >= 0.12 and blue < 150


def is_yellow_base_pixel(red, green, blue):
    hue, saturation, value = rgb_to_hsv(red / 255, green / 255, blue / 255)
    hue_degrees = hue * 360

    # Unreacted curcumin paper tends to be bright yellow.
    return 42 <= hue_degrees <= 70 and saturation >= 0.35 and value >= 0.35


def is_reaction_pixel(red, green, blue):
    hue, saturation, value = rgb_to_hsv(red / 255, green / 255, blue / 255)
    hue_degrees = hue * 360

    # Borax reaction shifts curcumin toward orange/brown/red; ignore the yellow base.
    return 8 <= hue_degrees < 42 and saturation >= 0.28 and value >= 0.10 and red > green


def mean_rgb(pixels):
    if not pixels:
        return None

    count = len(pixels)
    red = sum(pixel[0] for pixel in pixels) / count
    green = sum(pixel[1] for pixel in pixels) / count
    blue = sum(pixel[2] for pixel in pixels) / count
    return round(red, 3), round(green, 3), round(blue, 3)


def normalized_rgb(target_rgb, reference_rgb):
    if not target_rgb or not reference_rgb:
        return "", "", ""

    red = target_rgb[0] / reference_rgb[0] if reference_rgb[0] else ""
    green = target_rgb[1] / reference_rgb[1] if reference_rgb[1] else ""
    blue = target_rgb[2] / reference_rgb[2] if reference_rgb[2] else ""
    return (
        round(red, 5) if red != "" else "",
        round(green, 5) if green != "" else "",
        round(blue, 5) if blue != "" else "",
    )


def make_mask_image(size, reaction_positions, yellow_positions, paper_positions):
    mask = Image.new("RGB", size, (0, 0, 0))
    pixels = mask.load()

    for x, y in paper_positions:
        pixels[x, y] = (70, 70, 70)
    for x, y in yellow_positions:
        pixels[x, y] = (255, 220, 0)
    for x, y in reaction_positions:
        pixels[x, y] = (255, 40, 40)

    return mask


def largest_inner_component(width, height, candidate_positions):
    candidates = set(candidate_positions)
    visited = set()
    best_component = set()
    best_inner_component = set()

    for start in list(candidates):
        if start in visited:
            continue

        stack = [start]
        component = set()
        touches_border = False
        visited.add(start)

        while stack:
            x, y = stack.pop()
            component.add((x, y))
            if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                touches_border = True

            neighbors = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
            for neighbor in neighbors:
                if neighbor in candidates and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        if len(component) > len(best_component):
            best_component = component
        if not touches_border and len(component) > len(best_inner_component):
            best_inner_component = component

    return best_inner_component or best_component


def extract_curcumin(path, debug_dir=None):
    with Image.open(path) as image:
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        pixel_data = rgb_image.load()

        paper_positions = []

        for y in range(height):
            for x in range(width):
                red, green, blue = pixel_data[x, y]
                if not is_paper_pixel(red, green, blue):
                    continue

                paper_positions.append((x, y))

        paper_positions = sorted(largest_inner_component(width, height, paper_positions))
        paper_pixels = []
        yellow_pixels = []
        reaction_pixels = []
        yellow_positions = []
        reaction_positions = []

        for x, y in paper_positions:
                red, green, blue = pixel_data[x, y]
                paper_pixels.append((red, green, blue))

                if is_yellow_base_pixel(red, green, blue):
                    yellow_pixels.append((red, green, blue))
                    yellow_positions.append((x, y))
                elif is_reaction_pixel(red, green, blue):
                    reaction_pixels.append((red, green, blue))
                    reaction_positions.append((x, y))

        target_pixels = reaction_pixels if len(reaction_pixels) >= 50 else paper_pixels
        target_name = "reaction" if len(reaction_pixels) >= 50 else "paper_fallback"
        target_rgb = mean_rgb(target_pixels) or ("", "", "")
        paper_rgb = mean_rgb(paper_pixels) or ("", "", "")
        yellow_rgb = mean_rgb(yellow_pixels) or ("", "", "")
        norm_red, norm_green, norm_blue = normalized_rgb(target_rgb, yellow_rgb)

        if debug_dir:
            debug_dir.mkdir(parents=True, exist_ok=True)
            mask = make_mask_image(rgb_image.size, reaction_positions, yellow_positions, paper_positions)
            mask.save(debug_dir / f"{path.stem}_mask.png")

        return {
            "width": width,
            "height": height,
            "target": target_name,
            "paper_pixels": len(paper_pixels),
            "yellow_pixels": len(yellow_pixels),
            "reaction_pixels": len(reaction_pixels),
            "red": target_rgb[0],
            "green": target_rgb[1],
            "blue": target_rgb[2],
            "paper_red": paper_rgb[0],
            "paper_green": paper_rgb[1],
            "paper_blue": paper_rgb[2],
            "yellow_red": yellow_rgb[0],
            "yellow_green": yellow_rgb[1],
            "yellow_blue": yellow_rgb[2],
            "norm_red": norm_red,
            "norm_green": norm_green,
            "norm_blue": norm_blue,
        }


def iter_images(dataset_dir):
    for path in sorted(dataset_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def main():
    parser = ArgumentParser(description="Ekstraksi RGB area reaksi kertas kurkumin.")
    parser.add_argument("--dataset", default="dataset", help="Folder dataset berisi subfolder label ppm.")
    parser.add_argument("--output", default="curcumin_rgb_features.csv", help="File CSV hasil ekstraksi.")
    parser.add_argument("--debug-masks", action="store_true", help="Simpan mask warna untuk cek segmentasi.")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset)
    output_path = Path(args.output)
    debug_dir = Path("curcumin_masks") if args.debug_masks else None

    rows = []
    for image_path in iter_images(dataset_dir):
        label = image_path.parent.name
        values = extract_curcumin(image_path, debug_dir)
        rows.append(
            {
                "filename": image_path.name,
                "path": image_path.as_posix(),
                "label": label,
                "ppm": parse_ppm(label),
                **values,
            }
        )

    fieldnames = [
        "filename",
        "path",
        "label",
        "ppm",
        "width",
        "height",
        "target",
        "paper_pixels",
        "yellow_pixels",
        "reaction_pixels",
        "red",
        "green",
        "blue",
        "paper_red",
        "paper_green",
        "paper_blue",
        "yellow_red",
        "yellow_green",
        "yellow_blue",
        "norm_red",
        "norm_green",
        "norm_blue",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Selesai ekstraksi {len(rows)} gambar ke {output_path}")
    if debug_dir:
        print(f"Mask segmentasi disimpan ke {debug_dir}")


if __name__ == "__main__":
    main()
