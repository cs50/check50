#include <cs50.h>
#include <stdio.h>

int main(void) {
    int cents;
    do {
        cents = get_int("Cents? ");
    }
    while (cents < 0);

    const int n_denominations = 4;
    int denominations[n_denominations] = {1, 5, 10, 25};

    int coins = 0;
    for (int i = n_denominations - 1; i >= 0; i--) {
        coins += cents / denominations[i];
        cents %= denominations[i];
    }

    printf("%i\n", coins);
}
