// variazione sull'acquisizione dati da Arduino
//
// il programma ascolta (al momento mediante polling) un segnale. Quando viene triggerato
// invia i dati attraverso la seriale, implementando l'interfaccia dei sensori radar.
//
// in questo caso non possiamo sapere a priori quando la comunicazione sarà triggerata


#define TRIGGER_PIN 7
#define DEBOUNCE_TIME_MILLIS 300


enum class State {
	WAITING,
	READING
};


const char* name = "Arduino_trigger";
State state;
unsigned long last_measurement = 0;


void setup() {
	Serial.begin(9600);
	state = State::WAITING;

	pinMode(TRIGGER_PIN, INPUT);
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
			int trigger_state = digitalRead(TRIGGER_PIN);
			// questo trigger è un active LOW
			if (trigger_state == LOW) {
				const unsigned long now = millis();

				if (now - last_measurement > DEBOUNCE_TIME_MILLIS) {
						last_measurement = now;

						Serial.println("BEGIN");
						Serial.println(1);
						Serial.println("END");
				}
			}

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
