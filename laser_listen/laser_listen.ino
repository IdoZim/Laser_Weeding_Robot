const int Laser = 8;
void setup() {
  // put your setup code here, to run once:
  pinMode(Laser, OUTPUT);
  //digitalWrite(Laser, HIGH);
  Serial.begin(9600);

}

void loop() {
  // put your main code here, to run repeatedly:
  
  if (Serial.available())
  {
    char command = Serial.read();
    if (command == '1')
    {
      digitalWrite(Laser, HIGH);
    }
    else
    {
      digitalWrite(Laser, LOW);
    }
    Serial.println(command);

  }
}
