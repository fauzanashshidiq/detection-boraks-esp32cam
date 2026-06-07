#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

const char *ssid = "tayo";
const char *password = "123456789";

WebServer server(80);

#define FLASH_GPIO_NUM 4
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

void lockCameraColorSettings() {
  sensor_t *sensor = esp_camera_sensor_get();
  if (!sensor) {
    return;
  }

  sensor->set_whitebal(sensor, 1);
  sensor->set_awb_gain(sensor, 1);
  sensor->set_wb_mode(sensor, 0);

  sensor->set_exposure_ctrl(sensor, 1);
  sensor->set_aec2(sensor, 1);
  sensor->set_ae_level(sensor, -1);

  sensor->set_gain_ctrl(sensor, 1);
  sensor->set_gainceiling(sensor, (gainceiling_t)GAINCEILING_2X);

  sensor->set_brightness(sensor, 0);
  sensor->set_contrast(sensor, 0);
  sensor->set_saturation(sensor, 0);
  sensor->set_bpc(sensor, 1);
  sensor->set_wpc(sensor, 1);
  sensor->set_lenc(sensor, 1);
}

void handleCapture() {
  digitalWrite(FLASH_GPIO_NUM, HIGH);
  delay(300);

  for (int i = 0; i < 8; i++) {
    camera_fb_t *oldFrame = esp_camera_fb_get();
    if (oldFrame) {
      esp_camera_fb_return(oldFrame);
    }
    delay(60);
  }

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    digitalWrite(FLASH_GPIO_NUM, LOW);
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  WiFiClient client = server.client();
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: image/jpeg");
  client.print("Content-Length: ");
  client.println(fb->len);
  client.println("Access-Control-Allow-Origin: *");
  client.println("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
  client.println("Pragma: no-cache");
  client.println("Connection: close");
  client.println();
  client.write(fb->buf, fb->len);
  client.flush();
  delay(20);

  esp_camera_fb_return(fb);
  digitalWrite(FLASH_GPIO_NUM, LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_XGA;
  config.jpeg_quality = 8;
  config.fb_count = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    return;
  }
  lockCameraColorSettings();

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan ke WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("ESP32-CAM DHCP IP: ");
  Serial.println(WiFi.localIP());

  server.on("/capture", HTTP_GET, handleCapture);
  server.begin();
}

void loop() {
  server.handleClient();
}
