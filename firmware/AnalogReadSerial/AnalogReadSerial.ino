// variazione sull programma esempio `AnalogReadSerial.ino`
//
// il programma legge con frequenza prefissata il valore di tensione sul pin A0
// invia i dati attraverso la seriale, implementando l'interfaccia dei sensori radar.
//
// in questo caso non scegliamo esattamente la frequenza di campionamento, ma controlliamo
// il delay tra una acquisizione e l'altra


#define ANALOG_PIN A0


enum class State {
	WAITING,
	READING
};


const char* name = "Arduino_analog";
State state;


void setup() {
	Serial.begin(9600);
	state = State::WAITING;
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
			int value = analogRead(ANALOG_PIN);

			Serial.println("BEGIN");
			Serial.println(value);
			Serial.println("END");
			delay(20);

			if (Serial.available() > 0) {
				String res = Serial.readString();
				res.trim();

				if (res == "STOP") {
					state = State::WAITING;
				}
			}

			break;
	}
}
