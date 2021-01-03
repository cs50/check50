#include<math.h>

#include<stdio.h>

#include<cs50.h>

int main(void)


{   int quarter,penny,nichel,dimes,ncoins,sum,i,k,z,t;

quarter=25;
penny=1;
dimes=10;
nichel=5;




   float dollar = get_float(" change owed:\n");


     int cents=round(100*dollar);


  if (dollar>=0)

  {
     while(cents>=25)


    {   i=0;

         cents=cents-25;

          i++;

         ncoins=i;


    }


    while(cents>=10)

    {    z=0;
         cents=cents-10;

       z++;

        ncoins=ncoins+z;




    }

    while(cents>=5)


{
    cents=cents-5;
    t=0;
    t++;

    ncoins=ncoins+t;





}


    while(cents>=1)
{
    cents=cents-1;
    k=0;
    k++;
    ncoins=ncoins+k;


}


    printf("the number of coins are %i coins",ncoins);




}














}
