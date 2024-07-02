//Könyvtár az SPI kommunikációhoz
#include <SPI.h>

//Könyvtár a CAN kommunikációhoz
#include <mcp_can.h>

//Pinek kiválasztása a távolságmérő szenzorok számára
#define TRIG_FRONT_RIGHT 2
#define TRIG_FRONT_LEFT 4
#define TRIG_BACK_LEFT 6
#define TRIG_BACK_RIGHT 8
#define ECHO_FRONT_RIGHT 3
#define ECHO_FRONT_LEFT 5
#define ECHO_BACK_LEFT 7
#define ECHO_BACK_RIGHT 9


//az Arduino digitális 10-es pin-jének használata az SPI (Serial Peripheral Interface) chip select (CS) jelzésére.
const int spiCSPin = 10;

float front_left_duration, f_front_left_distance,front_right_duration, f_front_right_distance, back_left_duration, f_back_left_distance,back_right_duration, f_back_right_distance; 
float rain_sensor_read = 0;
int i_front_left_distance = 0, i_front_right_distance = 0, i_back_left_distance = 0, i_back_right_distance = 0, rainIntensity = 0;

// MCP_CAN objektum létrehozása
MCP_CAN CAN(spiCSPin);

void setup(){
  Serial.begin(115200);

  //A CAN-busz inicializálása 500 kbps sebességre, 8 MHz-es órajellel
  while (CAN_OK != CAN.begin(CAN_500KBPS, MCP_8MHz))
  {
      Serial.println("CAN BUS init Failed");
      // 100 milliszekundumos várakozás az újrainicializálásig
      delay(100);
  }
  Serial.println("CAN BUS Shield Init OK!");

  //Pinek kimenetnek és bemenetnek állítása
  pinMode(TRIG_FRONT_RIGHT, OUTPUT);  
	pinMode(ECHO_FRONT_RIGHT, INPUT); 

  pinMode(TRIG_FRONT_LEFT, OUTPUT);  
	pinMode(ECHO_FRONT_LEFT, INPUT); 

  pinMode(TRIG_BACK_LEFT, OUTPUT);  
	pinMode(ECHO_BACK_LEFT, INPUT); 

  pinMode(TRIG_BACK_RIGHT, OUTPUT);  
	pinMode(ECHO_BACK_RIGHT, INPUT);  

  pinMode(A0,  INPUT);
}

//CAN üzenetek adatmezőjét jelölő tömbök deklarálása és inicializálása
unsigned char dataOfMessage2[4] = {0};
unsigned char dataOfMessage3[1] = {0};

void loop()
{    
    //Bal első távolságmérő szenzor trigger kiadása
    digitalWrite(TRIG_FRONT_LEFT, LOW);  
	  delayMicroseconds(2);  
	  digitalWrite(TRIG_FRONT_LEFT, HIGH);  
	  delayMicroseconds(10);  
	  digitalWrite(TRIG_FRONT_LEFT, LOW);

    //Bal első távolságmérő szenzor echo kiadása
    front_left_duration = pulseIn(ECHO_FRONT_LEFT, HIGH);

    //Bal első távolságmérő szenzor mért távolságának kiszámítása
    f_front_left_distance = (front_left_duration*.0343)/2;


    //Jobb első távolságmérő szenzor trigger kiadása
    digitalWrite(TRIG_FRONT_RIGHT, LOW);  
	  delayMicroseconds(2);  
	  digitalWrite(TRIG_FRONT_RIGHT, HIGH);  
	  delayMicroseconds(10);  
	  digitalWrite(TRIG_FRONT_RIGHT, LOW);

    //Jobb első távolságmérő szenzor echo kiadása
    front_right_duration = pulseIn(ECHO_FRONT_RIGHT, HIGH);

    //Jobb első távolságmérő szenzor mért távolságának kiszámítása
    f_front_right_distance = (front_right_duration*.0343)/2;

    //Bal hátsó távolságmérő szenzor trigger kiadása
    digitalWrite(TRIG_BACK_LEFT, LOW);  
	  delayMicroseconds(2);  
	  digitalWrite(TRIG_BACK_LEFT, HIGH);  
	  delayMicroseconds(10);  
	  digitalWrite(TRIG_BACK_LEFT, LOW);

    //Bal hátsó távolságmérő szenzor echo kiadása
    back_left_duration = pulseIn(ECHO_BACK_LEFT, HIGH);

    //Bal hátsó távolságmérő szenzor mért távolságának kiszámítása
    f_back_left_distance = (back_left_duration*.0343)/2;

    //Jobb hátsó távolságmérő szenzor trigger kiadása
    digitalWrite(TRIG_BACK_RIGHT, LOW);  
	  delayMicroseconds(2);  
	  digitalWrite(TRIG_BACK_RIGHT, HIGH);  
	  delayMicroseconds(10);  
	  digitalWrite(TRIG_BACK_RIGHT, LOW);

    //Jobb hátsó távolságmérő szenzor echo kiadása
    back_right_duration = pulseIn(ECHO_BACK_RIGHT, HIGH);

    //Jobb hátsó távolságmérő szenzor mért távolságának kiszámítása
    f_back_right_distance = (back_right_duration*.0343)/2;


    //Esőszenzor értékének beolvasása
    rain_sensor_read = analogRead(A0);
    //Az eső intenzitás értékeének 0-10-es intervallumra való redukálása
    rain_sensor_read = rain_sensor_read/100;

    //tipus konverzió
    i_front_left_distance = (int)f_front_left_distance;
    i_front_right_distance = (int)f_front_right_distance;
    i_back_left_distance = (int)f_back_left_distance;
    i_back_right_distance = (int)f_back_right_distance;
    rainIntensity = (int)rain_sensor_read;

    //A távolságértékeknek és az eső intenzitás értékének CAN üzenetek adatmezőjébe való elhelyezése
    dataOfMessage2[0] = i_front_left_distance;
    dataOfMessage2[1] = i_front_right_distance;
    dataOfMessage2[2] = i_back_left_distance;
    dataOfMessage2[3] = i_back_right_distance;
    dataOfMessage3[0] = rainIntensity;

    //A távolságértékeket tartalmazó CAN üzenet elküldése
    CAN.sendMsgBuf(0x02, 0, 4, dataOfMessage2);

    //Az eső intenzitását tartalmazó CAN üzenet elküldése
    CAN.sendMsgBuf(0x03, 0, 1, dataOfMessage3);
}
