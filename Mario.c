#include <stdio.h>
#include <cs50.h>

int main (void)
        // get an input from the user
{
        int height , row ,column ,space;
    {
    height = get_int("enter a height here :\n");
    }
// condition of loop
    while (height<1 || height>8);
// as long as -
    for(row = 0; row < height ; row++)
    {
        for (space = 0 ;space<height -row -1 ; space++)
        {
            printf(" ");
        }
        for(column =0; column<= row; column++) // because the column loop is nested in the row loop,
//everytime row is increased , column is initialized to 0
        {
            printf("#");
        }
        printf("\n");
    }
}
