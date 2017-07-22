#include <stdio.h>

#define DIM_MAX 9
extern int board[DIM_MAX][DIM_MAX];
extern int d;

/**
 * Output board in a manner easily checked by check50. Adjacent numbers are
 * seperated by '-' and rows are seperated by '|'. Any tile which is outside
 * the range allowed by the given board size is assumed to represent the blank
 * tile and is printed as 0
 */
void simple_draw(void)
{
    int max = d * d;
    for (int row = 0; row < d; row++)
    {
        for (int col = 0; col < d; col++) 
        {
            int tile = board[row][col];
            printf("%d", tile > 0 && tile < max ? tile : 0);
            if (col < d - 1) printf("-");
        }
        printf("%c", row < d - 1 ? '|' : '\n');
    }
}
