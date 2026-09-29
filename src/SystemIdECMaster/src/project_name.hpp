#pragma once

#include <string>
#include <string_view>

#include "config.h"

inline std::string_view project_name()
{
    static const std::string name =
        std::string{"Hi Michele, today is a beatiful day and the application you just launched is: "}
        + APPLICATION_NAME;
    return name;
}
