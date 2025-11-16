#include <Arduino.h>
#include "motor.h"
#include <Servo.h>
Servo servo_x;
Servo servo_y;
#define Kpx 0.7
#define Kpy 0.5
#define Kix 0.5
#define Kiy 0.0
#define Kdx 0.0
#define Kdy 0.0
double currentTime, previousTime;
double setPointX =10.0; // Desired X position
double setPointY = 10.0;  // Desired Y position
double errorX, previousErrorX = 0.0;
double errorY, previousErrorY = 0.0;
double IntegralX = 0.0;
double IntegralY = 0.0;
double SamplingTime = 0.01; // Sampling time in milliseconds
int return_x, return_y;
int cmd = 0; 
void follow_hand(int error_x, int error_y) {

  currentTime = millis();
  float deltaTime = (currentTime - previousTime) / 1000.0; // Convert to seconds
  previousTime = currentTime;
  //if (deltaTime >= SamplingTime) {
    error_x = map(error_x,-170,170,-180,180);
    error_y = map(error_y,-130,130,-180,180);
    errorX = setPointX - error_x;
    errorY = setPointY - error_y;
    IntegralX += errorX * deltaTime;
    IntegralY += errorY * deltaTime;
    IntegralX = constrain(IntegralX, -100, 100); // Anti-windup
    IntegralY = constrain(IntegralY, -100, 100); // Anti-windup
    double DerivativeX = (errorX - previousErrorX) / deltaTime;
    double DerivativeY = (errorY - previousErrorY) / deltaTime;
    double outputX = Kpx * errorX + Kix * IntegralX + Kdx * DerivativeX;
    double outputY = Kpy * errorY + Kiy * IntegralY + Kdy * DerivativeY;
    int newPosX = constrain(servo_x.read() - outputX, 0, 180);
    int newPosY = constrain(servo_y.read() + outputY, 0, 180);
    servo_x.write(newPosX);
    // servo_y.write(newPosY);
    return_x = servo_x.read();
    return_y = servo_y.read();
    previousErrorX = errorX;
    previousErrorY = errorY;
  //}
}


void setup() {
  Serial.begin(9600);
  Motor_init();
  Motor_setSpeed(255);
  servo_x.attach(9, 500, 2400); // Attach servo to pin 9
  servo_y.attach(10, 500, 2400); // Attach servo to pin 10
  servo_x.write(150); // base position 150 degrees
  servo_y.write(50); // head position 50 degrees
  previousTime = millis();
}

void loop() {
  currentTime = millis();
  float deltaTime = (currentTime - previousTime) / 1000.0; // Convert to seconds
  //int cmd = 0;
  if (Serial.available() > 0 && deltaTime >= 0.01) {
    previousTime = currentTime;
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input == "S") {
      // Motor_stop();
      cmd = 0;
      // break;
    } else if (input == "N") {
      //Backward();
      cmd = 10;
      Serial.println("OK");
    } else if (input == "M") {
      //Forward();
      cmd = 1;
      //Serial.println("OK");
    } else if (input == "B"){
      //Backward();
      cmd = 3;
    } else if (input == "L"){
      //TurnLeft();
      cmd = 4;
    } else if (input == "R"){
      //TurnRight();
      cmd = 5;
    } else if (input.startsWith("F,")) {
      cmd = 2;
    }
  } else {
    switch (cmd)
    {
    case 0:
      Motor_stop();
      break;
    case 1:
      Forward();
      break;
    case 2:
      // follow_hand();
      break;
    case 3:
      Backward();
      break;
    case 4:
      TurnLeft();
      break;
    case 5:
      TurnRight();
      break;
    case 10:
      Motor_stop();
      servo_x.write(150); // base position
      servo_y.write(50);  // head position
      break;
    default:
      Motor_stop();
      servo_x.write(150); // base position
      servo_y.write(50);  // head position
      break;
    }
  }
}

