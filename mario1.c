#include <stdio.h>
#include <cs50.h>

int main(void)
{
    int x,i,y,z,t;


    x=get_int("enter the height from 1 to 8 \n");


    z=0;

  if(x>0 && x<9)
  
  {

    for(i=0;i<x;i++)

    {

        for(t=z;t<x;t++)
        {

            printf(" ");

        }





           for(y=x-z;y<=x;y=y+1)
           {



               printf("#");



           }

         z++;




          printf("\n");








}

  }


    }

