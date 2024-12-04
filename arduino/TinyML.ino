#include <Adafruit_AS7341.h>
#include <Wire.h>
#include "Adafruit_TLC59711.h"
#include "model_parameters.h" // Include the model parameters
#include <math.h>             // For exp() function

Adafruit_AS7341 as7341;
#define NUM_TLC59711 1
#define data 10
#define clock 8

// Customizable Variables
int pwmValue = 1000;  // PWM Value for LEDs
int atime = 50;       // AS7341 ATIME setting
int astep = 499;      // AS7341 ASTEP setting
int stabTime = 10;
int delayTime = 5;
int portNum = 115200;
int disconnectDelay = 1000;
as7341_gain_t gain = AS7341_GAIN_256X; // Gain setting for AS7341

// LED brightness for each LED (adjust as needed)
int ledBrightness[9] = {5000, 5000, 20000, 5000, 10000, 10000, 20000, 20000, 5000};

Adafruit_TLC59711 tlc = Adafruit_TLC59711(NUM_TLC59711, clock, data);
uint16_t readings[10] = {0};
unsigned long startTime = 0;

void setup() {
    Serial.begin(portNum);

    // AS7341 Setup
    if (!as7341.begin()) {
        Serial.println("Could not find AS7341");
        while (1) {
            delay(disconnectDelay);
        }
    }
    as7341.setATIME(atime);
    as7341.setASTEP(astep);
    as7341.setGain(gain);  // Set gain correctly

    tlc.begin();

    startTime = millis();

    // Print header for data columns
    Serial.println("Time(ms),590nm,630nm,680nm,NIR,Prediction");
}

// Activation functions
float relu(float x) { return x > 0 ? x : 0; }
float sigmoid(float x) { return 1.0 / (1.0 + exp(-x)); }

// Prediction function
float predict(float *input) {
    float hidden[4]; // Hidden layer outputs

    // Normalize inputs
    float norm_input[4];
    for (int i = 0; i < 4; i++) {
        norm_input[i] = (input[i] - mean[i]) / std_dev[i];
    }

    // Compute hidden layer activations
    for (int i = 0; i < 4; i++) {
        float sum = 0.0;
        for (int j = 0; j < 4; j++) {
            sum += norm_input[j] * fc1_weight[i][j];
        }
        sum += fc1_bias[i];
        hidden[i] = relu(sum);
    }

    // Compute output layer activation
    float output = 0.0;
    for (int i = 0; i < 4; i++) {
        output += hidden[i] * fc2_weight[i];
    }
    output += fc2_bias;

    // Apply Sigmoid to get probability
    float prediction = sigmoid(output);

    return prediction;
}

void loop() {
    float input[4] = {0}; // Initialize the input array for prediction

    // Ensure specific LEDs are activated one by one
    int ledIndices[] = {2, 1, 0, 8}; // LEDs for PD channels 590, 630, 680, NIR
    for (int i = 0; i < 4; ++i) {
        int ledIndex = ledIndices[i];
        tlc.setPWM(ledIndex, ledBrightness[ledIndex]);
        tlc.write();
        delay(stabTime); // Stabilize sensor after changing LED state

        // Read channels
        if (!as7341.readAllChannels()) {
            Serial.println("Error reading all channels!");
            return;
        }

        switch (ledIndex) {
            case 2: input[0] = (float)as7341.getChannel(AS7341_CHANNEL_590nm_F6); break;
            case 1: input[1] = (float)as7341.getChannel(AS7341_CHANNEL_630nm_F7); break;
            case 0: input[2] = (float)as7341.getChannel(AS7341_CHANNEL_680nm_F8); break;
            case 8: input[3] = (float)as7341.getChannel(AS7341_CHANNEL_NIR); break;
        }

        delay(delayTime); // Short delay between readings
    }

    // Reset all LEDs
    for (int i = 0; i < 9; ++i) {
        tlc.setPWM(i, 0);
    }
    tlc.write();

    // Perform prediction with the collected readings
    float prediction = predict(input);

    // Output the prediction and readings via Serial
    Serial.print("Time(ms): ");
    Serial.print(millis());
    Serial.print(", 590nm: ");
    Serial.print(input[0]);
    Serial.print(", 630nm: ");
    Serial.print(input[1]);
    Serial.print(", 680nm: ");
    Serial.print(input[2]);
    Serial.print(", NIR: ");
    Serial.print(input[3]);
    Serial.print(", Prediction: ");
    Serial.println(prediction);
}
