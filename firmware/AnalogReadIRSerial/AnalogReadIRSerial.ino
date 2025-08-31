// variazione sull programma esempio `AnalogReadSerial.ino`
//
// il programma legge con frequenza prefissata il valore di ir
// invia i dati attraverso la seriale, implementando l'interfaccia dei sensori radar.
//
// in questo caso non scegliamo esattamente la frequenza di campionamento, ma controlliamo
// il delay tra una acquisizione e l'altra
#include <Wire.h>
#include "MAX30105.h"

enum class State {
		WAITING,
		READING
};

const char* name = "Arduino_IR";
State state;
MAX30105 sensor;


void setup() {
		Wire.begin();

		if (not sensor.begin(Wire)) {
				name = "Arduino_IR (n/a)";
		}

		sensor.setup();
		sensor.setPulseAmplitudeIR(0x0A);
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
						const long ir = sensor.getIR();

						Serial.println("BEGIN");
						Serial.println(ir);
						Serial.println("END");

						if (Serial.available() > 0) {
								String res = Serial.readString();
								res.trim();

								if (res == "STOP") {
										state = State::WAITING;
								}
						}

						delay(100);
						break;
		}
}
