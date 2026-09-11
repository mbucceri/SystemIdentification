#include <cstdlib>

int main()
{
    constexpr int expected = 4;
    constexpr int actual = 2 + 2;

    return actual == expected ? EXIT_SUCCESS : EXIT_FAILURE;
}
