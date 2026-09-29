#include <cstdlib>

#include "../src/config.h"
#include "../src/project_name.hpp"

int main()
{
    const auto name = project_name();
    if (name != "Hi Michele, today is a beatiful day and the application you just launched is: "
                  "SystemIdECMaster harness bootstrap") {
        return EXIT_FAILURE;
    }

    constexpr int expected = 4;
    constexpr int actual = 2 + 2;

    return actual == expected ? EXIT_SUCCESS : EXIT_FAILURE;
}
