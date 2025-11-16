#ifndef MOTOR_H
#define MOTOR_H

#define ENA_PIN 5
#define IN1_PIN 2
#define IN2_PIN 3
#define ENB_PIN 6
#define IN3_PIN 4
#define IN4_PIN 7

#ifdef __cplusplus
extern "C" {
#endif

extern int currentSpeed;
void Motor_init();
void Motor_setSpeed(int speed);
void Motor_stop();
void Forward();
void Backward();
void TurnLeft();
void TurnRight();
void moveLeft();
void moveRight();

#ifdef __cplusplus
}
#endif

#endif // MOTOR_H
