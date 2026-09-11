FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bubblewrap \
        build-essential \
        ca-certificates \
        curl \
        git \
        ninja-build \
        python3 \
        python3-pip \
        python3-venv \
        sudo \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install CMake 3.30 as an official Kitware binary distribution.
ARG CMAKE_VERSION=3.30.9

RUN wget -q \
        "https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz" \
        -O /tmp/cmake.tar.gz \
    && mkdir -p /opt/cmake \
    && tar --strip-components=1 \
        -xzf /tmp/cmake.tar.gz \
        -C /opt/cmake \
    && ln -s /opt/cmake/bin/cmake /usr/local/bin/cmake \
    && ln -s /opt/cmake/bin/ctest /usr/local/bin/ctest \
    && ln -s /opt/cmake/bin/cpack /usr/local/bin/cpack \
    && rm /tmp/cmake.tar.gz

# Node.js 22 LTS.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Codex CLI.
RUN npm install -g @openai/codex@latest \
    && npm cache clean --force

# Non-root development user.
RUN groupadd --gid "${USER_GID}" "${USERNAME}" \
    && useradd \
        --uid "${USER_UID}" \
        --gid "${USER_GID}" \
        --create-home \
        --shell /bin/bash \
        "${USERNAME}" \
    && echo "${USERNAME} ALL=(root) NOPASSWD:ALL" \
        > "/etc/sudoers.d/${USERNAME}" \
    && chmod 0440 "/etc/sudoers.d/${USERNAME}"

USER ${USERNAME}
WORKDIR /workspace