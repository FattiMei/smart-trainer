// variazione sull programma esempio `AsyncReadSerial.ino`
//
// il programma legge con frequenza prefissata il valore ir (del modulo MAX30102)
// e lo elabora per identificare l'evento battito.
//
// implementa l'interfaccia dei sensori radar e invia un dato ogni volta che rileva un battito
// la frequenza di campionamento del sensore IR è impostata nel setup del sensore
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

enum class State {
		WAITING,
		READING
};

const char* name = "Arduino_heartbeat";
State state;
MAX30105 sensor;
int n = 0;
long lastBeat = 0;


void setup() {
		Wire.begin();

		if (not sensor.begin(Wire)) {
				name = "Arduino_hearbeat (n/a)";
		}

		// powerLevel, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange
		sensor.setup(0x1F, 4, 2, 100, 411, 4096); 
		sensor.setPulseAmplitudeIR(0x1F);
		sensor.setPulseAmplitudeRed(0x0A);

		Serial.begin(9600);
		state = State::WAITING;
		while(!Serial);
}


void loop() {
		switch (state) {
				case State::WAITING:
						if (Serial.available() > 0) {
								// lo so che usare l'oggetto String è estremamente
								// inefficiente, ma è un modo veloce di realizzare
								// la funzionalità
								String res = Serial.readString();
								res.trim();

								if (res == "INFO") {
										Serial.println(name);
								} else if (res == "START") {
										state = State::READING;
								}
						}

						break;

				case State::READING:
						long irValue = sensor.getIR();

						if (checkForBeat(irValue)) {
								const long now = millis();

								if (now - lastBeat > 1500) {
										// è passato troppo tempo dall'ultimo beat,
										// sicuramente c'è stato un problema di disconnessione
										// del dito
										n = 0;
								}

								lastBeat = now;

								Serial.println("BEGIN");
								Serial.println(n);
								Serial.println("END");
								n++;
						}
						if (Serial.available() > 0) {
								String res = Serial.readString();
								res.trim();

								if (res == "STOP") {
										state = State::WAITING;
								}
						}

						delay(20);
						break;
		}
}
