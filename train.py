import argparse
import os
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


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
IMG_SIZE = (128, 128)
RANDOM_STATE = 42


def center_crop(image_bgr, ratio=0.6):
    height, width = image_bgr.shape[:2]
    crop_w = int(width * ratio)
    crop_h = int(height * ratio)
    x1 = max((width - crop_w) // 2, 0)
    y1 = max((height - crop_h) // 2, 0)
    return image_bgr[y1 : y1 + crop_h, x1 : x1 + crop_w]


def segment_curcumin_paper(image_bgr, output_size=IMG_SIZE, return_mask=False, apply_mask=True):
    """Segment curcumin paper using HSV and crop to the largest contour."""
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
    bbox = None
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 100:
            x, y, w, h = cv2.boundingRect(largest)
            crop = image_bgr[y : y + h, x : x + w]
            crop_mask = mask[y : y + h, x : x + w]
            if apply_mask:
                neutral = np.full_like(crop, 255)
                crop = np.where(crop_mask[..., None] > 0, crop, neutral)
            bbox = (x, y, w, h)
        else:
            crop = center_crop(image_bgr)
    else:
        crop = center_crop(image_bgr)

    resized = cv2.resize(crop, output_size, interpolation=cv2.INTER_AREA)
    if return_mask:
        return resized, mask, bbox
    return resized


def iter_dataset_images(dataset_dir):
    dataset_dir = Path(dataset_dir)
    for class_index, class_name in enumerate(CLASS_NAMES):
        class_dir = dataset_dir / class_name
        if not class_dir.exists():
            print(f"Warning: class folder not found: {class_dir}")
            continue
        for path in sorted(class_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                yield path, class_index, class_name


def load_dataset(dataset_dir):
    images = []
    labels = []
    paths = []

    for image_path, class_index, _ in iter_dataset_images(dataset_dir):
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            print(f"Skip unreadable image: {image_path}")
            continue

        crop_bgr = segment_curcumin_paper(image_bgr)
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        images.append(crop_rgb.astype("float32") / 255.0)
        labels.append(class_index)
        paths.append(str(image_path))

    images = np.array(images, dtype=np.float32)
    labels = np.array(labels, dtype=np.int64)
    paths = np.array(paths)

    if len(images) == 0:
        raise RuntimeError(f"No images loaded from dataset: {dataset_dir}")
    return images, labels, paths


def show_segmentation_examples(dataset_dir, output_path="segmentation_examples.png", max_examples=8):
    examples = []
    for image_path, _, class_name in iter_dataset_images(dataset_dir):
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            continue
        crop_bgr, mask, bbox = segment_curcumin_paper(image_bgr, return_mask=True)
        original_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        examples.append((original_rgb, mask, crop_rgb, class_name, image_path.name, bbox))
        if len(examples) >= max_examples:
            break

    if not examples:
        return

    fig, axes = plt.subplots(len(examples), 3, figsize=(9, 3 * len(examples)))
    if len(examples) == 1:
        axes = np.expand_dims(axes, axis=0)

    for row, (original, mask, crop, class_name, filename, bbox) in enumerate(examples):
        axes[row, 0].imshow(original)
        axes[row, 0].set_title(f"{class_name} - original")
        if bbox:
            x, y, w, h = bbox
            rect = plt.Rectangle((x, y), w, h, fill=False, edgecolor="red", linewidth=2)
            axes[row, 0].add_patch(rect)

        axes[row, 1].imshow(mask, cmap="gray")
        axes[row, 1].set_title("HSV mask")
        axes[row, 2].imshow(crop)
        axes[row, 2].set_title("segmented 128x128")

        for col in range(3):
            axes[row, col].axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close(fig)
    print(f"Saved segmentation examples to {output_path}")


def build_mobilenetv2_model(num_classes):
    # Recommended for this small dataset: transfer learning with frozen ImageNet features.
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE[1], IMG_SIZE[0], 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomRotation(5 / 360),
            tf.keras.layers.RandomTranslation(0.1, 0.1),
            tf.keras.layers.RandomFlip("horizontal"),
        ],
        name="color_safe_augmentation",
    )

    inputs = tf.keras.Input(shape=(IMG_SIZE[1], IMG_SIZE[0], 3))
    x = augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x * 255.0)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="borax_mobilenetv2")


def build_light_cnn_model(num_classes):
    # Alternative for comparison only. Use MobileNetV2 first because the dataset is tiny.
    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomRotation(5 / 360),
            tf.keras.layers.RandomTranslation(0.1, 0.1),
            tf.keras.layers.RandomFlip("horizontal"),
        ],
        name="color_safe_augmentation",
    )

    model = tf.keras.Sequential(
        [
            tf.keras.Input(shape=(IMG_SIZE[1], IMG_SIZE[0], 3)),
            augmentation,
            tf.keras.layers.Conv2D(32, 3, activation="relu", padding="same"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation="relu", padding="same"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(128, 3, activation="relu", padding="same"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dense(num_classes, activation="softmax"),
        ],
        name="borax_light_cnn",
    )
    return model


def plot_history(history, output_path="training_curves.png"):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history["accuracy"], label="train")
    axes[0].plot(history.history["val_accuracy"], label="validation")
    axes[0].set_title("Accuracy")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()

    axes[1].plot(history.history["loss"], label="train")
    axes[1].plot(history.history["val_loss"], label="validation")
    axes[1].set_title("Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close(fig)
    print(f"Saved training curves to {output_path}")


def plot_confusion_matrix(y_true, y_pred, output_path="confusion_matrix.png"):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASS_NAMES))))
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Test Confusion Matrix")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    print(f"Saved confusion matrix to {output_path}")


def show_test_predictions(model, x_test, y_test, test_paths, output_path="test_predictions.png", count=5):
    count = min(count, len(x_test))
    probs = model.predict(x_test[:count], verbose=0)
    preds = np.argmax(probs, axis=1)

    fig, axes = plt.subplots(1, count, figsize=(3 * count, 3.5))
    if count == 1:
        axes = [axes]

    for i in range(count):
        confidence = probs[i, preds[i]]
        axes[i].imshow(x_test[i])
        axes[i].axis("off")
        axes[i].set_title(
            f"True: {CLASS_NAMES[y_test[i]]}\nPred: {CLASS_NAMES[preds[i]]}\nConf: {confidence:.2f}",
            fontsize=9,
        )
        print(
            f"Test sample {i + 1}: {Path(test_paths[i]).name} | "
            f"true={CLASS_NAMES[y_test[i]]} pred={CLASS_NAMES[preds[i]]} confidence={confidence:.4f}"
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close(fig)
    print(f"Saved test prediction examples to {output_path}")


def extract_rgb_features(dataset_dir, output_csv="rgb_features.csv"):
    rows = []
    for image_path, _, class_name in iter_dataset_images(dataset_dir):
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            continue
        crop_bgr, mask, bbox = segment_curcumin_paper(
            image_bgr, output_size=None, return_mask=True, apply_mask=False
        )
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        if bbox:
            x, y, w, h = bbox
            crop_mask = mask[y : y + h, x : x + w]
        else:
            crop_mask = None
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
    print(f"Saved RGB baseline features to {output_csv}")
    return df


def train_random_forest_baseline(rgb_df):
    x = rgb_df[["R_mean", "G_mean", "B_mean"]].values
    y = rgb_df["kelas"].map({name: index for index, name in enumerate(CLASS_NAMES)}).values

    x_train, x_temp, y_train, y_temp = train_test_split(
        x, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
    )

    model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE)
    model.fit(np.vstack([x_train, x_val]), np.concatenate([y_train, y_val]))
    preds = model.predict(x_test)
    accuracy = accuracy_score(y_test, preds)
    print(f"Random Forest RGB baseline test accuracy: {accuracy:.4f}")
    return accuracy


def main():
    parser = argparse.ArgumentParser(description="Train borax concentration classifier from ESP32-CAM images.")
    parser.add_argument("--dataset", default="dataset", help="Dataset folder with class subfolders")
    parser.add_argument("--model-output", default="borax_cnn_model.h5", help="Output .h5 model path")
    parser.add_argument("--architecture", choices=["mobilenetv2", "light_cnn"], default="mobilenetv2")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--skip-rf", action="store_true", help="Skip Random Forest RGB baseline")
    args = parser.parse_args()

    if not os.path.isdir(args.dataset):
        raise FileNotFoundError(f"Dataset folder not found: {args.dataset}")

    show_segmentation_examples(args.dataset)
    x, y, paths = load_dataset(args.dataset)
    print(f"Loaded dataset: {x.shape[0]} images, shape={x.shape[1:]}")

    x_train, x_temp, y_train, y_temp, paths_train, paths_temp = train_test_split(
        x, y, paths, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    x_val, x_test, y_val, y_test, paths_val, paths_test = train_test_split(
        x_temp, y_temp, paths_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
    )

    print(f"Split: train={len(x_train)}, validation={len(x_val)}, test={len(x_test)}")

    if args.architecture == "mobilenetv2":
        model = build_mobilenetv2_model(len(CLASS_NAMES))
    else:
        model = build_light_cnn_model(len(CLASS_NAMES))

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True, monitor="val_loss"),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5, monitor="val_loss"),
    ]

    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    plot_history(history)

    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
    print(f"Test loss: {test_loss:.4f}")
    print(f"Test accuracy: {test_acc:.4f}")

    probabilities = model.predict(x_test, verbose=0)
    y_pred = np.argmax(probabilities, axis=1)
    print("Classification report:")
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0))

    plot_confusion_matrix(y_test, y_pred)
    show_test_predictions(model, x_test, y_test, paths_test)

    rgb_df = extract_rgb_features(args.dataset, "rgb_features.csv")
    if not args.skip_rf:
        train_random_forest_baseline(rgb_df)

    model.save(args.model_output)
    print(f"Saved best model to {args.model_output}")


if __name__ == "__main__":
    main()
