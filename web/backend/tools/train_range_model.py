from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight


ROOT_DIR = Path(__file__).resolve().parents[3]
DATASET_DIR = ROOT_DIR / "dataset"
MODEL_OUTPUT = ROOT_DIR / "borax_range_model.keras"
BEST_MODEL_OUTPUT = ROOT_DIR / "best_borax_range_model.keras"
IMG_SIZE = (128, 128)
RANDOM_STATE = 42
BATCH_SIZE = 16
EPOCHS = 100

CLASS_NAMES = ["0ppm", "100-250ppm", "500-1000ppm", "1250-2000ppm"]
ORIGINAL_TO_RANGE = {
    "0ppm": "0ppm",
    "100ppm": "100-250ppm",
    "250ppm": "100-250ppm",
    "500ppm": "500-1000ppm",
    "750ppm": "500-1000ppm",
    "1000ppm": "500-1000ppm",
    "1250ppm": "1250-2000ppm",
    "1500ppm": "1250-2000ppm",
    "1750ppm": "1250-2000ppm",
    "2000ppm": "1250-2000ppm",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def center_crop(image_bgr, ratio=0.6):
    height, width = image_bgr.shape[:2]
    crop_width = int(width * ratio)
    crop_height = int(height * ratio)
    x1 = max((width - crop_width) // 2, 0)
    y1 = max((height - crop_height) // 2, 0)
    return image_bgr[y1 : y1 + crop_height, x1 : x1 + crop_width]


def segment_curcumin_paper(image_bgr, output_size=IMG_SIZE):
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    _, mask = cv2.threshold(saturation, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        crop = center_crop(image_bgr, ratio=0.7)
    else:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 500:
            crop = center_crop(image_bgr, ratio=0.7)
        else:
            x, y, width, height = cv2.boundingRect(largest)
            padding = int(0.05 * max(width, height))
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image_bgr.shape[1], x + width + padding)
            y2 = min(image_bgr.shape[0], y + height + padding)
            crop = image_bgr[y1:y2, x1:x2]

    return cv2.resize(crop, output_size, interpolation=cv2.INTER_AREA)


def iter_dataset_images():
    class_index_by_name = {class_name: index for index, class_name in enumerate(CLASS_NAMES)}
    for original_name, range_name in ORIGINAL_TO_RANGE.items():
        class_index = class_index_by_name[range_name]
        class_dir = DATASET_DIR / original_name
        if not class_dir.exists():
            raise FileNotFoundError(f"Class folder not found: {class_dir}")
        for image_path in sorted(class_dir.iterdir()):
            if image_path.suffix.lower() in IMAGE_EXTENSIONS:
                yield image_path, class_index


def load_dataset():
    images, labels = [], []
    for image_path, class_index in iter_dataset_images():
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            print(f"Skip unreadable image: {image_path}")
            continue
        crop_bgr = segment_curcumin_paper(image_bgr)
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        images.append(crop_rgb.astype("float32") / 255.0)
        labels.append(class_index)

    if not images:
        raise RuntimeError(f"No images loaded from {DATASET_DIR}")
    return np.array(images, dtype=np.float32), np.array(labels, dtype=np.int64)


def color_safe_augmentation():
    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.04),
            tf.keras.layers.RandomZoom(0.08),
            tf.keras.layers.RandomTranslation(0.05, 0.05),
            tf.keras.layers.RandomContrast(0.08),
        ],
        name="color_safe_augmentation",
    )


def build_model(num_classes):
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE[1], IMG_SIZE[0], 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=(IMG_SIZE[1], IMG_SIZE[0], 3))
    x = color_safe_augmentation()(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x * 255.0)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="borax_range_mobilenetv2")


def main():
    np.random.seed(RANDOM_STATE)
    tf.random.set_seed(RANDOM_STATE)

    print(f"Dataset: {DATASET_DIR}")
    print(f"Classes: {CLASS_NAMES}")
    x, y = load_dataset()

    x_train, x_temp, y_train, y_temp = train_test_split(
        x, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
    )

    weights = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(len(CLASS_NAMES)),
        y=y_train,
    )
    class_weight = {index: float(weight) for index, weight in enumerate(weights)}

    model = build_model(len(CLASS_NAMES))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            BEST_MODEL_OUTPUT,
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.EarlyStopping(
            patience=15,
            restore_best_weights=True,
            monitor="val_loss",
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            factor=0.5,
            patience=5,
            monitor="val_loss",
        ),
    ]

    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
        class_weight=class_weight,
    )

    test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=0)
    print(f"Test loss: {test_loss:.4f}")
    print(f"Test accuracy: {test_accuracy:.4f}")

    model.save(MODEL_OUTPUT)
    print(f"Saved model: {MODEL_OUTPUT}")
    print(f"Saved best checkpoint: {BEST_MODEL_OUTPUT}")


if __name__ == "__main__":
    main()
