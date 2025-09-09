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

int last_trigger_state;
unsigned long last_trigger_time;


void setup() {
	Serial.begin(9600);
	state = State::WAITING;

	pinMode(TRIGGER_PIN, INPUT_PULLUP);
	last_trigger_state = HIGH;
	last_trigger_time = 0;
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
			const int trigger_state = digitalRead(TRIGGER_PIN);

			// questo particolare sensore viene triggerato sul fronte di discesa
			if (trigger_state == LOW and last_trigger_state == HIGH) {
				const auto now = millis();

				if ((now - last_trigger_time) > DEBOUNCE_TIME_MILLIS) {
					last_trigger_time = now;
				
					Serial.println("BEGIN");
					Serial.println(1);
					Serial.println("END");
				}
			}

			last_trigger_state = trigger_state;

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
