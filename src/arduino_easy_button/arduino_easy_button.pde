// PhotoPops Easy Button
// v0.3
// 2011-10-22

int shutterPin = 2;
int focusPin = 3;
int buttonPin = 4;

int shutterLed = 8;
int focusLed = 9;
int serialLed = 10;

int inByte = 0;
int buttonState;
int buttonVal;
boolean ready = true;

int focusDur = 400;
int preShutterDur = 200;
int shutterDur = 500;

void photoCapture() {
  // Activate focus
  digitalWrite(focusPin, HIGH);
  digitalWrite(focusLed, HIGH);
  delay(focusDur);
  digitalWrite(focusPin, LOW);
  digitalWrite(focusLed, LOW);
  
  // Wait for focus to complete before triggering shutter
  delay(preShutterDur);
  
  // Trigger shutter
  digitalWrite(shutterPin, HIGH);
  digitalWrite(shutterLed, HIGH);
  delay(shutterDur);
  digitalWrite(shutterPin, LOW);
  digitalWrite(shutterLed, LOW);  
}

void setup() {
  Serial.begin(9600);
  pinMode(shutterPin, OUTPUT);
  pinMode(focusPin, OUTPUT);
  pinMode(buttonPin, INPUT);
  pinMode(shutterLed, OUTPUT);
  pinMode(focusLed, OUTPUT);
  pinMode(serialLed, OUTPUT);
}
  
void loop() {
  buttonVal = digitalRead(buttonPin);
  
  if (buttonVal != buttonState) {                  // buttonState has changed
    if ((buttonVal == LOW) && (ready == true)) {   // Button is pressed
      // Button is pressed. Write 'A' to signal button press.
      Serial.write(65);
      ready = false;                               // Don't accept another button press until the photo process is finished.
    }
  }
    
  buttonState = buttonVal;
  
  if (Serial.available() > 0) {
     inByte = Serial.read();
     
     if (inByte == 66) {
       // Received 'B' - Capture photo now
       digitalWrite(serialLed, HIGH);
       
       // Photo capture code
       photoCapture();
       
       // Write 'C' to signal photo capture done.
       Serial.write(67);
     }
     
     if (inByte == 68) {
       // Received 'D' - Photo process complete. Set to ready.
       ready = true;
     }
  }
  
  digitalWrite(serialLed, LOW);
}
