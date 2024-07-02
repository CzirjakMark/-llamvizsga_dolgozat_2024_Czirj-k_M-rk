//Könyvtár az SPI kommunikációhoz
#include <SPI.h>

//Könyvtár a CAN kommunikációhoz
#include <mcp_can.h>

//Könyvtár a szervomotorok vezérléséhez
#include <Servo.h>

#define  FRONT_LEFT_SERVO 7
#define  FRONT_RIGHT_SERVO 8
#define  BACK_SERVO 9

//az Arduino digitális 10-es pin-jének használata az SPI (Serial Peripheral Interface) chip select (CS) jelzésére.
const int spiCSPin = 10;

//Szervomotorokhoz tartozó objektum létrehozása
Servo steering_wheel;
Servo front_left_servo;
Servo gas;

// Annak az időpontnak tárolására szolgáló változó, amikor a szervomotor állapota utoljára
// módosítva volt
unsigned long prevTime_back_wiper = 0;
unsigned long prevTime_front_wiper = 0;

//A szervomotorok állapotmódosításának gyakorisága milliszekundumban
const int interval_back_wiper = 50;
const int interval_front_wiper = 50;

//A szervomotorok vezérléséhez szükséges értékek változóinak deklarálása
int val_front_right_servo,val_front_left_servo,val_back_servo;

int back_servo_angle = 0;
bool flag_back_max_angle = false;
bool flag_left_button_off = false;
int left_button_pressed_counter = 0;

int front_servo_angle = 0;
int flag_front_max_angle = 0;
int flag_right_button_off = 0;
int right_button_pressed_counter = 0;

short gear = 0;

// MCP_CAN objektum létrehozása
MCP_CAN CAN(spiCSPin);

void setup() {

  Serial.begin(115200);

  //A CAN-busz inicializálása 500 kbps sebességre, 8 MHz-es órajellel
  while (CAN_OK != CAN.begin(CAN_500KBPS, MCP_8MHz))  // Corrected the constant name here
    {
        Serial.println("CAN BUS init Failed");
        // 100 milliszekundumos várakozás az újrainicializálásig
        delay(100);
    }
  Serial.println("CAN BUS Shield Init OK!");

  //SzervomotorOK csatlakoztatása pinhez
  front_left_servo.attach(FRONT_LEFT_SERVO);
  front_right_servo.attach(FRONT_RIGHT_SERVO);
  back_servo.attach(BACK_SERVO);
}

//A beérkező CAN üzenetek adatmezőjét hossza byte-okban
unsigned char length_of_data = 0;

//A beérkező CAN üzenetek adatmezőjében található adatok tárolására szolgáló tömb
unsigned char buf[8];

int rainIntensity = 0;


void update_back_servo() {
  //Tolatás és az eső intenzitásának figyelése,valamint a motor pozíciójának változtatása
  if(gear == 255 && rainIntensity < 8 && rainIntensity >= 5){
      if (flag_back_max_angle == false) {
            back_servo.write(back_servo_angle);
            back_servo_angle += 6;
            if (back_servo_angle >= 180) {
                flag_back_max_angle = true;
            }
        } else if (flag_back_max_angle == true) {
            back_servo_angle -= 6;
            back_servo.write(back_servo_angle);
            if (back_servo_angle <= 0) {
                flag_back_max_angle = false;
            }
        }
    }
    //Tolatás és az eső intenzitásának figyelése, valamint a motor pozíciójának intenzívebb változtatása
    if(gear == 255 && rainIntensity < 5){
      if (flag_back_max_angle == false) {
            //Szervomotor pozíciójának beállítása
            back_servo.write(back_servo_angle);
            back_servo_angle += 9;
            if (back_servo_angle >= 180) {
                flag_back_max_angle = true;
            }
        } else if (flag_back_max_angle == true) {
            //Szervomotor pozíciójának beállítása
            back_servo_angle -= 9;
            back_servo.write(back_servo_angle);
            if (back_servo_angle <= 0) {
                flag_back_max_angle = false;
            }
        }
    }
    //A bal gomb lenyomásának,a szervo aktuális szögének ellenőrzése,valamint a motor pozíciójának változtatása
    if (flag_back_max_angle == false && flag_left_button_off == false) {
            //Szervomotor pozíciójának beállítása
            back_servo.write(back_servo_angle);
            back_servo_angle += 6;
            if (back_servo_angle >= 180) {
              flag_back_max_angle = true;
            }
        } else if (flag_back_max_angle == true && flag_left_button_off == false) {
            //Szervomotor pozíciójának beállítása
            back_servo_angle -= 6;
            back_servo.write(back_servo_angle);
            if (back_servo_angle <= 0) {
                flag_back_max_angle = false;
            }
        }
}

void update_front_servo() {
    //Előre menet és az eső intenzitásának figyelése,valamint a motor pozíciójának változtatása
    if(gear < 255 && rainIntensity < 8 && rainIntensity >= 5){
      if (flag_front_max_angle == false) {
            //Szervomotorok pozíciójának beállítása
            front_right_servo.write(front_servo_angle);
            front_left_servo.write(front_servo_angle);
            front_servo_angle += 6;
            if (front_servo_angle >= 180) {
                flag_front_max_angle = true;
            }
        } else if (flag_front_max_angle == true) {
            //Szervomotorok pozíciójának beállítása
            front_servo_angle -= 6;
            front_right_servo.write(front_servo_angle);
            front_left_servo.write(front_servo_angle);
            if (front_servo_angle <= 0) {
                flag_front_max_angle = false;
            }
        }
    }
    //Előre menet és az eső intenzitásának figyelése,valamint a motor pozíciójának intenzívebb változtatása
    if(gear < 255 && rainIntensity <5){
      if (flag_front_max_angle == false) {
         if (front_servo_angle >= 180) {
                flag_front_max_angle = true;
            }
          //Szervomotorok pozíciójának beállítása
          front_right_servo.write(front_servo_angle);
          front_left_servo.write(front_servo_angle);
          front_servo_angle += 9;
          
        } else if (flag_front_max_angle == true) {
          if (front_servo_angle <= 0) {
                flag_front_max_angle = false;
            }
            //Szervomotorok pozíciójának beállítása
            front_servo_angle -= 9;
            front_right_servo.write(front_servo_angle);
            front_left_servo.write(front_servo_angle);
            
        }
    }
        //A jobb gomb lenyomásának,a szervo aktuális szögének ellenőrzése,valamint a motor pozíciójának változtatása
        if (flag_front_max_angle == false && flag_right_button_off == false) {
            //Szervomotorok pozíciójának beállítása
            front_right_servo.write(front_servo_angle);
            front_left_servo.write(front_servo_angle);
            front_servo_angle += 6;
            if (front_servo_angle >= 180) {
                flag_front_max_angle = true;
            }
        } else if (flag_front_max_angle == true && flag_right_button_off == false) {
            //Szervomotorok pozíciójának beállítása
            front_servo_angle -= 6;
            front_right_servo.write(front_servo_angle);
            front_left_servo.write(front_servo_angle);
            if (front_servo_angle <= 0) {
                flag_front_max_angle = false;
            }
        }
}

 unsigned long canId;

void loop() {

  //Lekérdezze az aktuális időnek milliszekundumokban az Arduino indulása óta
  unsigned long currentTime = millis();

  //Ellenőrzése annak, hogy érkezett-e üzenet
  if (CAN_MSGAVAIL == CAN.checkReceive())
    {
        //A bejövő CAN üzenet fogadása
        CAN.readMsgBuf(&length_of_data, buf);

        //A bejövő üzenet azonosítójának elmentése
        canId = CAN.getCanId();

        //A fogadni kívánt üzenet azonosítójának és a benne levő adatok számának ellenőrzése
        if (canId == 0x03 && length_of_data == 1)
        {
            rainIntensity = buf[0];
        }
        //A fogadni kívánt üzenet azonosítójának és a benne levő adatok számának ellenőrzése
        else if (canId == 0x04 && length_of_data == 3)
        {   
            //Az sebességváltó aktuális állásának elmentése
            gear = buf[2];

            //A bal gomb lenyomásának ellenőrzése
            if (buf[0] == 1) {
                left_button_pressed_counter++;
                flag_left_button_off = (left_button_pressed_counter % 2 == 0) ? true : false;
            }
            //A jobb gomb lenyomásának ellenőrzése
            if (buf[1] == 1) {
                right_button_pressed_counter++;
                flag_right_button_off = (right_button_pressed_counter % 2 == 0) ? true : false;
            }
        }
    }

    // Annak ellenőrzése, hogy a jelenlegi idő és az utolsó módosítás ideje
    // között eltelt-e a meghatározott mikroszekundum
    // Ha eltelt, akkor a szervomotor állapotmódosító függvénye meghívásra kerül
     if (currentTime - prevTime_back_wiper >= interval_back_wiper) {
        prevTime_back_wiper = currentTime;
        update_back_servo();
    }

    // Annak ellenőrzése, hogy a jelenlegi idő és az utolsó módosítás ideje
    // között eltelt-e a meghatározott mikroszekundum
    // Ha eltelt, akkor a szervomotor állapotmódosító függvénye meghívásra kerül
    if (currentTime - prevTime_front_wiper >= interval_front_wiper) {
        prevTime_front_wiper = currentTime;
        update_front_servo();
    }
  }
