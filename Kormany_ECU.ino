//Könyvtár az SPI kommunikációhoz
#include <SPI.h>

//Könyvtár a CAN kommunikációhoz
#include <mcp_can.h> 

//Pinek kiválasztása a motorvezérlő számára
#define DIRECTION   7
#define EN    9

//A sebességváltó max min értékei
#define MAX_GEAR 6
#define MIN_GEAR -1

//Pinek kiválasztása a kormány és váltókar gombjainak számára
#define  LEFT_BUTTON 5
#define  RIGHT_BUTTON 3
#define  SHIFT_FORWARD 4
#define  SHIFT_BACKWARD 6

//az Arduino digitális 10-es pin-jének használata az SPI (Serial Peripheral Interface) chip select (CS) jelzésére.
const int spiCSPin = 10;

int motorSpeed = 0;
bool direction = LOW;

bool shift_forward_offflag = true; 

bool shift_backward_offflag = true;

short gear_state = 0;

//A kormányszög és a pedálok állását tároló változók
int val_steering_wheel,val_gas,val_brake;

// MCP_CAN objektum létrehozása
MCP_CAN CAN(spiCSPin);

void setup() {
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
  pinMode(LEFT_BUTTON,INPUT);

  pinMode(RIGHT_BUTTON,INPUT);

  pinMode(SHIFT_FORWARD,INPUT);

  pinMode(SHIFT_BACKWARD,INPUT);

  pinMode(DIRECTION, OUTPUT);
  digitalWrite(DIRECTION, LOW);

  pinMode(EN, OUTPUT);
  digitalWrite(EN, LOW);
}
//CAN üzenetek adatmezőjét jelölő tömbök deklarálása és inicializálása
unsigned char dataOfMessage4[3] = {0};
unsigned char dataOfMessage5[3] = {0};

//A beérkező CAN üzenetek adatmezőjét hossza byte-okban
unsigned char length_of_data = 0;

//A beérkező CAN üzenetek adatmezőjében található adatok tárolására szolgáló tömb
unsigned char buf[8];

unsigned long canId = 0;

void loop() {

  //Ellenőrzése annak, hogy érkezett-e üzenet
  if (CAN_MSGAVAIL == CAN.checkReceive())
    {
        //A bejövő CAN üzenet fogadása
        CAN.readMsgBuf(&length_of_data, buf);

        //A bejövő üzenet azonosítójának elmentése
        canId = CAN.getCanId();

        //A fogadni kívánt üzenet azonosítójának és a benne levő adatok számának ellenőrzése
        if (canId == 0x06 && length_of_data == 1)
        {
            //Az aktuális sebesség érték elmentése
            motorSpeed = buf[0];
        }
    }
  //Kormányszög, gáz- és fékpedálok értékének beolvasása
  val_steering_wheel = analogRead(1);
  val_gas = analogRead(2);
  val_brake = analogRead(3);

  //A potenciométerektől érkező 0-1023-as analóg érték átméretezése a 0-180 tartományba
  val_steering_wheel = map(val_steering_wheel,0,1023,0,180);
  val_gas = map(val_gas,0,1023,0,180);
  val_brake = map(val_brake,0,1023,0,180);

  //A kormányszögnek és az pedálok értékének CAN üzenet adatmezőjébe való elhelyezése
  dataOfMessage5[0] = val_steering_wheel;
  dataOfMessage5[1] = val_gas;
  dataOfMessage5[2] = val_brake;

  //Vizsgálata annak, hogy a bal gomb le van-e nyomva
  if(digitalRead(LEFT_BUTTON) == HIGH){
    //Gombállás elhelyezése a CAN üzenet adatmezőjébe
    dataOfMessage4[0] = 1;
  }
  else{
    //Gombállás elhelyezése a CAN üzenet adatmezőjébe
    dataOfMessage4[0] = 0;    
  }

  //Vizsgálata annak, hogy a jobb gomb le van-e nyomva
  if(digitalRead(RIGHT_BUTTON) == HIGH){
    //Gombállás elhelyezése a CAN üzenet adatmezőjébe
    dataOfMessage4[1] =1;
  }
  else{
    //Gombállás elhelyezése a CAN üzenet adatmezőjébe
    dataOfMessage4[1] = 0;
 
  }

  //Váltókar előre mozdításának figyelése
  if((digitalRead(SHIFT_FORWARD) == HIGH) && shift_forward_offflag == true){
    shift_forward_offflag = false;
    //Vizsgálata annak, hogy elértük-e a maximális állását a sebességváltónak
    if(gear_state < MAX_GEAR){
      gear_state++;
    }
    //Váltókar állás elhelyezése a CAN üzenet adatmezőjébe
    dataOfMessage4[2] = gear_state;
  }
  else if(digitalRead(SHIFT_FORWARD) == LOW){
    shift_forward_offflag = true;
  }

  //Váltókar hátra mozdításának figyelése
  if((digitalRead(SHIFT_BACKWARD) == HIGH) && shift_backward_offflag == true){
    shift_backward_offflag = false;
    //Vizsgálata annak, hogy elértük-e a minimális állását a sebességváltónak
    if(gear_state >  MIN_GEAR){
      gear_state--;
    }
    //Váltókar állás elhelyezése a CAN üzenet adatmezőjébe
    dataOfMessage4[2] = gear_state;
  }
  else if(digitalRead(SHIFT_BACKWARD) == LOW){
    shift_backward_offflag = true;
  }

  //A motor forgási irányának és sebességének meghatározása a sebességváltó 
  //aktuális állása és a műszerfal által kiszámított sebesség által
  if(dataOfMessage4[2] == 255){
    digitalWrite(DIRECTION, !direction);  //set direction
    analogWrite(EN, motorSpeed);  //set speed (with pwm)
  }
  else{
    digitalWrite(DIRECTION, direction);  //set direction
    analogWrite(EN, motorSpeed);  //set speed (with pwm)
  }

  //A komány és váltókar gombjainak állásást tartalmazó CAN üzenet elküldése
  CAN.sendMsgBuf(0x04, 0, 3, dataOfMessage4);

  //A kormányszöget, gáz- és fékpedál állásokat tartalmazó CAN üzenet elküldése
  CAN.sendMsgBuf(0x05, 0, 3, dataOfMessage5);
}

