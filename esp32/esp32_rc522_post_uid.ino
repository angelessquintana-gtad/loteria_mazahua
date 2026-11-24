/* ESP32 + RC522 por USB/Serial, 115200 baudios.
   Cargar en el puerto USB del ESP32 y cerrar el Monitor Serie antes de conectar el navegador.
   RC522: SDA=5, SCK=18, MOSI=23, MISO=19, RST=2, VCC=3.3V, GND=GND.
*/
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 5
#define RST_PIN 2
MFRC522 rfid(SS_PIN, RST_PIN);
String ultimoUID = "";
unsigned long ultimaLectura = 0;
unsigned long ultimoEstado = 0;
unsigned long ultimoReinicioRFID = 0;
// Sin un sensor adicional no se puede distinguir una avería de un tiempo sin
// tarjetas. Un reinicio breve y periódico del RC522 mantiene activa la lectura.
const unsigned long INTERVALO_RECUPERACION_RFID = 8000;

void setup() {
  Serial.begin(115200);
  delay(300);
  SPI.begin(18, 19, 23, SS_PIN);
  rfid.PCD_Init();
  delay(50);
  Serial.println("READY:RFID USB 115200");
  byte version = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (version == 0x00 || version == 0xFF) {
    Serial.println("ERROR:RC522 no responde. Revisar cableado y 3.3V.");
  }
}

void loop() {
  unsigned long ahora = millis();
  if (ahora - ultimaLectura >= INTERVALO_RECUPERACION_RFID &&
      ahora - ultimoReinicioRFID >= INTERVALO_RECUPERACION_RFID) {
    ultimoReinicioRFID = ahora;
    rfid.PCD_Init();
    delay(50);
    Serial.println("STATUS:RFID recuperacion preventiva");
  }
  // El navegador usa este estado para detectar una conexión congelada; estar
  // sin tarjetas cerca no se interpreta como una falla.
  if (millis() - ultimoEstado >= 5000) {
    ultimoEstado = millis();
    byte version = rfid.PCD_ReadRegister(MFRC522::VersionReg);
    if (version == 0x00 || version == 0xFF) {
      Serial.println("STATUS:RC522 sin respuesta; reiniciando lector");
      rfid.PCD_Init();
      delay(50);
    } else {
      Serial.println("STATUS:RFID OK");
    }
  }
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    delay(30);
    return;
  }
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) uid += " ";
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  if (uid != ultimoUID || millis() - ultimaLectura > 1500) {
    Serial.println("UID:" + uid);
    ultimoUID = uid;
    ultimaLectura = millis();
  }
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(100);
}
