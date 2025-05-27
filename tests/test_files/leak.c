#include <stdlib.h>

void leak() {
    malloc(sizeof(int));
}

int main() {
    leak();
}
