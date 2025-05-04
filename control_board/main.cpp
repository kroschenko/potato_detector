#include <Arduino.h>

int relayPin = 7; // Пин, к которому подключено реле
int ledPin = 13;  // Пин, к которому подключен встроенный светодиод

unsigned long lastPulseTime = 0;
unsigned long pulseDuration = 0;
bool relayActive = false;

void setup()
{
    pinMode(relayPin, OUTPUT); // Устанавливаем пин на вывод для реле
    pinMode(ledPin, OUTPUT);   // Устанавливаем пин на вывод для светодиода

    digitalWrite(relayPin, HIGH); // Изначально выключаем реле
    digitalWrite(ledPin, LOW);    // Изначально выключаем светодиод

    // Мигаем светодиодом 3 раза при старте
    for (int i = 0; i < 3; i++)
    {
        digitalWrite(ledPin, HIGH); // Включаем светодиод
        delay(500);                 // Ждем полсекунды
        digitalWrite(ledPin, LOW);  // Выключаем светодиод
        delay(500);                 // Ждем полсекунды
    }

    Serial.begin(9600); // Инициализируем последовательную связь
    Serial.println("Board started");
}

void loop()
{
    if (Serial.available() > 0)
    {
        String input = Serial.readStringUntil('\n'); // Читаем строку до символа новой строки
        pulseDuration = input.toInt(); // Преобразуем строку в число

        if (pulseDuration > 0)
        {
            // Включаем реле и светодиод на указанное время
            digitalWrite(relayPin, LOW); // Включаем реле
            digitalWrite(ledPin, HIGH);  // Включаем светодиод

            Serial.print(millis());
            Serial.print(" - Relay ON for ");
            Serial.print(pulseDuration);
            Serial.println(" ms");

            lastPulseTime = millis(); // Запоминаем время включения
            relayActive = true;
        }
    }

    // Проверяем, истекло ли время импульса
    if (relayActive && (millis() - lastPulseTime >= pulseDuration))
    {
        // Выключаем реле и светодиод
        digitalWrite(relayPin, HIGH); // Выключаем реле
        digitalWrite(ledPin, LOW);    // Выключаем светодиод

        Serial.print(millis());
        Serial.println(" - Relay OFF");

        relayActive = false;
    }
}
