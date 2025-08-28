// variazione sull programma esempio `AnalogReadSerial.ino`
//
// il programma legge con frequenza prefissata il valore ir e lo elabora per inviare attraverso 
// la seriale quando avviene l'evento battito, implementando l'interfaccia dei sensori radar.
//
// la frequenza di campionamento è impostata nel setup del sensore

#include <Wire.h>
#include "MAX30105.h"

#include "heartRate.h"

MAX30105 sensor;

const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;

float bpm;
int avgBPM;
int n = 0;

enum class State {
	WAITING,
	READING
};


const char* name = "Arduino_analog";
State state;


void setup() {
  Serial.begin(9600);
	state = State::WAITING;
	while(!Serial);

  Wire.begin();
  Serial.println("Init MAX30102...");

  if(!sensor.begin(Wire)) {
    Serial.println("MAX30102 not found. Check connections/power supply.");
    while(1) delay(1000);
		
  }else{
		Serial.println("...found.");
		Serial.println("Place your finger on the sensor with steady pressure.");
	}
  
	// powerLevel, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange
  sensor.setup(0x1F, 4, 2, 100, 411, 4096); 
	// sensor.setup();
  sensor.setPulseAmplitudeIR(0x1F);
  sensor.setPulseAmplitudeRed(0x0A);
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

      if (checkForBeat(irValue)) 
      {
        long now = millis();
        long delta = now - lastBeat;
        lastBeat = now;

        bpm = 60.0 / (delta / 1000.0);
        if (bpm > 20 && bpm < 255) 
        {
          rates[rateSpot++] = (byte)bpm;
          rateSpot %= RATE_SIZE;
          for (byte i = 0 ; i < RATE_SIZE ; i++) avgBPM += rates[i];
          avgBPM /= RATE_SIZE;

					n++;

          Serial.println("BEGIN");
			    Serial.println(n);
			    Serial.println("END");

        }else{
					n = 0;
				}
      }
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
