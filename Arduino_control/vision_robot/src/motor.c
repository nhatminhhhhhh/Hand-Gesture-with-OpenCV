#include <Arduino.h>
#include "motor.h"

int currentSpeed = 0;
void Motor_init() {
    // Initialize motor hardware
    pinMode(ENA_PIN, OUTPUT);
    pinMode(IN1_PIN, OUTPUT);
    pinMode(IN2_PIN, OUTPUT);
    pinMode(ENB_PIN, OUTPUT);
    pinMode(IN3_PIN, OUTPUT);
    pinMode(IN4_PIN, OUTPUT);
}

void Motor_setSpeed(int speed) {
    currentSpeed = speed;
}

void Motor_stop() {
    // Stop motor hardware
    analogWrite(ENA_PIN, 0);
    analogWrite(ENB_PIN, 0);
    pinMode(IN1_PIN, LOW);
    pinMode(IN2_PIN, LOW);
    pinMode(IN3_PIN, LOW);
    pinMode(IN4_PIN, LOW);
}
void Forward() {
    analogWrite(ENA_PIN, currentSpeed);
    analogWrite(ENB_PIN, currentSpeed);
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, HIGH);
    digitalWrite(IN3_PIN, LOW);
    digitalWrite(IN4_PIN, HIGH);
    
}
void Backward() {
    analogWrite(ENA_PIN, currentSpeed);
    analogWrite(ENB_PIN, currentSpeed);
    digitalWrite(IN1_PIN, HIGH);
    digitalWrite(IN2_PIN, LOW);
    digitalWrite(IN3_PIN, HIGH);
    digitalWrite(IN4_PIN, LOW);
}
void TurnLeft() {
    analogWrite(ENB_PIN, currentSpeed);
    digitalWrite(IN3_PIN, LOW);
    digitalWrite(IN4_PIN, HIGH);
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, LOW);
}
void TurnRight() {
    analogWrite(ENA_PIN, currentSpeed); 
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, HIGH);
    digitalWrite(IN3_PIN, LOW);
    digitalWrite(IN4_PIN, LOW);
}
void moveLeft() {
    analogWrite(ENA_PIN, currentSpeed);
    analogWrite(ENB_PIN, currentSpeed);
    digitalWrite(IN1_PIN, HIGH);
    digitalWrite(IN2_PIN, LOW);
    digitalWrite(IN3_PIN, LOW);
    digitalWrite(IN4_PIN, HIGH);
}
void moveRight() {
    analogWrite(ENA_PIN, currentSpeed);
    analogWrite(ENB_PIN, currentSpeed);
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, HIGH);
    digitalWrite(IN3_PIN, HIGH);
    digitalWrite(IN4_PIN, LOW);
}