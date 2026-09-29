# H0 — Agentic Harness Bootstrap

**Purpose:** Establish the smallest reliable Codex-driven development loop for the existing `SystemIdentification` monorepo using one repository-root VS Code Dev Container.

The immediate implementation target is `src/SystemIdECMaster`, but the development environment and agent workspace cover the complete monorepo.

---

## H0 Definition of Done

H0 is complete when all of the following are true:

- Docker is installed and usable by the normal user.
- VS Code and the Dev Containers extension are available.
- The existing `SystemIdentification` Git repository contains a version-controlled root `.devcontainer/`.
- The development container builds reproducibly.
- GCC/G++, CMake >= 3.30, Ninja, Git, Python, Node/npm and Codex CLI are available inside the container.
- The official Codex VS Code extension is usable from the Dev Container.
- Codex can inspect the complete monorepo.
- `src/SystemIdECMaster` contains a minimal C++ build.
- A deterministic host verification script returns success/failure through its exit status.
- repository-level and project-level `AGENTS.md` files define operating rules and scope.
- Codex can make a deliberately small change inside `SystemIdECMaster`.
- Codex runs the verification script after the change.
- A deliberately introduced defect is detected by verification and corrected by Codex.
- The final repository is committed in a clean state.

---

## Scope

H0 includes:

- one root Dev Container for the complete `SystemIdentification` monorepo;
- C++ and Python development baseline;
- Codex CLI and VS Code integration;
- repository-wide agent visibility;
- `SystemIdECMaster` project bootstrap;
- CMake/Ninja;
- minimal C++ target;
- minimal test target;
- shell-based verification;
- Git;
- Codex sandbox/approval policy;
- repository-level and project-level `AGENTS.md`.

H0 explicitly excludes:

- MATLAB inside the Dev Container;
- IgH installation;
- PREEMPT_RT;
- EtherCAT hardware;
- HIL;
- Conan;
- JFrog;
- CodeGraph;
- Graphify;
- Caveman;
- DS402;
- production architecture;
- MISRA compliance tooling.

---

## H0.1 — Monorepo layout

The existing repository remains authoritative.

Target structure:

```text
SystemIdentification/
├── .devcontainer/
│   ├── Dockerfile
│   └── devcontainer.json
│
├── AGENTS.md
│
├── data/
│   └── ...
│
├── docs/
│   ├── literature/
│   └── SystemIdECMaster/
│       ├── dissertation/
│       ├── architecture/
│       ├── decisions/
│       ├── exec-plans/
│       │   ├── active/
│       │   └── completed/
│       ├── experiments/
│       └── requirements/
│
└── src/
    ├── Identification_Luna_DB3.5/
    ├── Identification_VerticalJoint/
    ├── InputData/
    ├── utils/
    └── SystemIdECMaster/
        ├── AGENTS.md
        ├── CMakeLists.txt
        ├── README.md
        ├── include/
        ├── src/
        ├── tests/
        ├── tools/
        └── cmake/
```

There is one Git repository and one Dev Container.

Do not create a nested Git repository under `src/SystemIdECMaster`.

---

## H0.2 — Development environment policy

The Dev Container is the canonical development environment for the monorepo.

Its purpose is to provide one compatible toolchain baseline for current and future repository projects.

Initial common toolset:

- GCC/G++;
- CMake;
- Ninja;
- Git;
- Python 3;
- pip;
- Node.js/npm;
- Codex CLI;
- common shell/build utilities.

MATLAB is intentionally kept outside the container for now.

Project-specific dependencies remain owned by the project rather than being indiscriminately installed into the base image.

The container should make it possible to add Python dependencies later without requiring a second development environment.

---

## H0.3 — Repository visibility and temporary work scope

Codex may inspect the complete monorepo.

This is intentional because future tasks may need access to:

- robot descriptions;
- Python utilities;
- system-identification code;
- datasets;
- shared logic;
- future projects.

During the current phase, implementation changes should remain focused on:

```text
src/SystemIdECMaster/
docs/SystemIdECMaster/
```

unless an active execution plan explicitly requires modification elsewhere.

This is a temporary task-scope discipline, not a permanent repository-access restriction.

---

## H0.4 — Root Dev Container Dockerfile

Create:

```text
SystemIdentification/.devcontainer/Dockerfile
```

with:

```dockerfile
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
        gnupg \
        ninja-build \
        python3 \
        python3-pip \
        python3-venv \
        sudo \
        wget \
    && rm -rf /var/lib/apt/lists/*

# CMake from Kitware's Ubuntu Jammy repository.
RUN wget -qO- https://apt.kitware.com/keys/kitware-archive-latest.asc \
        | gpg --dearmor \
        > /usr/share/keyrings/kitware-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ jammy main" \
        > /etc/apt/sources.list.d/kitware.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        cmake \
        kitware-archive-keyring \
    && rm -rf /var/lib/apt/lists/*

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
```

Notes:

- Ubuntu 22.04 remains the container base.
- Python is intentionally included because existing monorepo projects use it.
- MATLAB is excluded.
- The image remains unprivileged.
- No host Docker socket is mounted.
- No EtherCAT NIC is exposed.
- No host home directory is mounted wholesale.

---

## H0.5 — Root Dev Container configuration

Create:

```text
SystemIdentification/.devcontainer/devcontainer.json
```

with:

```json
{
    "name": "SystemIdentification Development",

    "build": {
        "dockerfile": "Dockerfile",
        "context": "..",
        "args": {
            "USERNAME": "vscode",
            "USER_UID": "1000",
            "USER_GID": "1000"
        }
    },

    "remoteUser": "vscode",

    "workspaceFolder": "/workspace/SystemIdentification",

    "mounts": [
        "source=${localWorkspaceFolder},target=/workspace/SystemIdentification,type=bind,consistency=cached"
    ],

    // Codex uses Bubblewrap to create an inner workspace sandbox.
    // Docker's default seccomp and AppArmor policies prevent the nested
    // namespace/mount-propagation operations required by Bubblewrap.
    // Relax only those outer policies; the container remains non-privileged
    // and does not expose the Docker socket, host devices, or host home.
    "runArgs": [
        "--security-opt",
        "seccomp=unconfined",
        "--security-opt",
        "apparmor=unconfined"
    ],


    "customizations": {
        "vscode": {
            "extensions": [
                "ms-vscode.cpptools",
                "ms-vscode.cmake-tools",
                "ms-python.python"
            ],
            "settings": {
                "cmake.generator": "Ninja"
            }
        }
    },

    "containerEnv": {
        "CC": "gcc",
        "CXX": "g++"
    }
}
```

Install the official Codex extension through VS Code and record its actual extension identifier after installation.

Do not guess or hard-code an unverified extension identifier.

---

## H0.6 — Open the monorepo in the Dev Container

From the host:

```bash
cd /path/to/SystemIdentification
code .
```

Then in VS Code:

1. open the Command Palette;
2. run `Dev Containers: Reopen in Container`;
3. allow the image to build;
4. confirm that the whole `SystemIdentification` repository is visible inside the container.

The workspace root inside the container should be:

```text
/workspace/SystemIdentification
```

---

## H0.7 — Verify the container toolchain

Run inside the Dev Container:

```bash
echo "===== USER ====="
whoami

echo "===== OS ====="
cat /etc/os-release | grep PRETTY_NAME

echo "===== GCC ====="
gcc --version | head -n 1

echo "===== G++ ====="
g++ --version | head -n 1

echo "===== CMAKE ====="
cmake --version | head -n 1

echo "===== NINJA ====="
ninja --version

echo "===== GIT ====="
git --version

echo "===== PYTHON ====="
python3 --version

echo "===== PIP ====="
python3 -m pip --version

echo "===== NODE ====="
node --version

echo "===== NPM ====="
npm --version

echo "===== CODEX ====="
codex --version
```

Required properties:

- non-root user;
- Ubuntu 22.04;
- CMake >= 3.30;
- Python available;
- Node 22.x;
- Codex CLI available.

---

## H0.8 — Codex authentication

Inside the container:

```bash
codex
```

Authenticate with the intended ChatGPT account.

Authentication persistence should be tested after a Dev Container rebuild.

If persistence is needed, add a narrowly scoped mechanism for Codex state/credentials rather than mounting the complete host home directory.

---

## H0.9 — Codex security baseline

Initial intended Codex policy:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

Codex should be able to inspect the entire repository.

Do not enable unrestricted host access.

Do not mount during H0:

- `/var/run/docker.sock`;
- the complete host home directory;
- SSH private keys;
- EtherCAT NIC devices;
- real-time target credentials.

---


### Validated Linux sandbox prerequisites

Codex's `workspace-write` sandbox relies on Bubblewrap inside the Dev Container.

During H0 the following were verified:

```text
unshare --user --map-root-user true
    -> succeeds

Bubblewrap nested namespace/mount test
    -> succeeds
```

To make this work inside Docker, the Dev Container uses:

```jsonc
"runArgs": [
    "--security-opt",
    "seccomp=unconfined",
    "--security-opt",
    "apparmor=unconfined"
]
```

This relaxation applies to the outer Dev Container security profiles. The container remains non-privileged and does not expose the Docker socket, host devices, or the host home directory.

With this configuration, Codex can use its inner Bubblewrap-based `workspace-write` sandbox normally. Routine workspace commands such as `sed`, `rg`, `find`, `git status`, `diff`, CMake and test commands therefore do not require approval merely because of sandbox initialization failure.

Network access and genuine attempts to cross the configured sandbox boundary may still require approval, which is expected.

## H0.10 — Repository-level AGENTS.md

Create:

```text
SystemIdentification/AGENTS.md
```

with:

```markdown
# SystemIdentification Repository Agent Instructions

## Repository purpose

This is a multi-project robotics and system-identification monorepo.

The repository contains C++, Python, MATLAB scripts, robot descriptions,
experimental data and supporting utilities.

The canonical development environment is the repository Dev Container.

## Repository visibility

Agents may inspect any part of the repository when it is useful for
understanding a task.

Do not assume that neighboring projects are unrelated merely because
they use another language.

## Change scope

Modify only files required by the active task or execution plan.

For the current project phase, implementation work is focused on:

- src/SystemIdECMaster/
- docs/SystemIdECMaster/

Changes elsewhere require an explicit task reason.

## Engineering behavior

Do not invent missing requirements.

Prefer existing repository knowledge and utilities when appropriate,
but do not create dependencies on neighboring projects without
evaluating their architectural cost.

Do not perform broad refactoring as a side effect of a focused task.

## Verification

Use the verification procedure defined by the project being modified.

A task is not complete if required deterministic verification fails.
```

---

## H0.11 — SystemIdECMaster project skeleton

Create:

```bash
mkdir -p \
    src/SystemIdECMaster/include \
    src/SystemIdECMaster/src \
    src/SystemIdECMaster/tests \
    src/SystemIdECMaster/tools \
    src/SystemIdECMaster/cmake \
    docs/SystemIdECMaster/dissertation \
    docs/SystemIdECMaster/architecture \
    docs/SystemIdECMaster/decisions \
    docs/SystemIdECMaster/exec-plans/active \
    docs/SystemIdECMaster/exec-plans/completed \
    docs/SystemIdECMaster/experiments \
    docs/SystemIdECMaster/requirements
```

---

## H0.12 — SystemIdECMaster project AGENTS.md

Create:

```text
src/SystemIdECMaster/AGENTS.md
```

with:

```markdown
# SystemIdECMaster Agent Instructions

## Purpose

This project implements a C++ EtherCAT master application targeting
a Linux real-time environment.

Development and host-side verification run inside the repository
Dev Container.

## Authoritative documentation

Consult the relevant documents under:

../../docs/SystemIdECMaster/

including:

- requirements/
- architecture/
- decisions/
- exec-plans/
- experiments/

Do not invent missing requirements.

If required behavior is ambiguous, identify the ambiguity rather than
silently selecting an interpretation.

## Scope discipline

Keep implementation changes focused on SystemIdECMaster unless an
approved execution plan explicitly requires changes elsewhere.

The rest of the monorepo may be inspected and reused where justified.

## Build and verification

For host-side work, run:

    ./tools/verify-host.sh

from this project directory.

A task is not complete if required verification fails.

Do not remove, weaken or bypass a test merely to make verification pass.

## C++

Follow the language version and warning policy configured by CMake.

MISRA C++:2023 is the intended coding standard, but do not claim formal
compliance unless the configured compliance process verifies it.

## Real-time and hardware safety

The final application will communicate with EtherCAT devices and may
control physical actuators.

Do not infer safe physical-device behavior.

Do not perform hardware or motion tests unless an execution plan
explicitly authorizes them.

## Environment boundaries

The Dev Container is a development and host-verification environment.

Do not treat timing results obtained inside the Dev Container as
evidence of target real-time performance.

Do not request privileged container access or host-device access unless
an approved execution plan explicitly requires it.
```

---

## H0.13 — Minimal C++ program

Create:

```text
src/SystemIdECMaster/src/main.cpp
```

with:

```cpp
#include <iostream>

int main()
{
    std::cout << "SystemIdECMaster harness bootstrap\n";
    return 0;
}
```

---

## H0.14 — Dependency-free smoke test

Create:

```text
src/SystemIdECMaster/tests/bootstrap_test.cpp
```

with:

```cpp
#include <cstdlib>

int main()
{
    constexpr int expected = 4;
    constexpr int actual = 2 + 2;

    return actual == expected ? EXIT_SUCCESS : EXIT_FAILURE;
}
```

---

## H0.15 — Minimal CMake project

Create:

```text
src/SystemIdECMaster/CMakeLists.txt
```

with:

```cmake
cmake_minimum_required(VERSION 3.30)

project(
    SystemIdECMaster
    VERSION 0.1.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

function(project_warnings target)
    target_compile_options(${target} PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Werror
    )
endfunction()

add_executable(SystemIdECMaster
    src/main.cpp
)
project_warnings(SystemIdECMaster)

enable_testing()

add_executable(bootstrap-test
    tests/bootstrap_test.cpp
)
project_warnings(bootstrap-test)

add_test(
    NAME bootstrap-test
    COMMAND bootstrap-test
)
```

C++17 is the project language baseline.

---

## H0.16 — Canonical build-directory layout

All generated build artifacts live at the monorepo root, outside the source tree.

Canonical build directories are:

```text
SystemIdentification/
└── build/
    ├── linux-debug/
    ├── linux-release/
    ├── linux_rt-debug/
    └── linux_rt-release/
```

The naming convention is:

```text
build/<target>-<mode>
```

Supported target identifiers are `linux` and `linux_rt`; supported build modes are `debug` and `release`.

At H0, `linux_rt` reserves the target identity and directory convention only. PREEMPT_RT-specific build/runtime semantics will be defined later.

## H0.17 — Deterministic host verifier

Create `src/SystemIdECMaster/tools/verify-host.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/../.." && pwd)"

TARGET="${1:-linux}"
MODE="${2:-debug}"

case "${TARGET}" in
    linux|linux_rt) ;;
    *)
        echo "Unsupported target: ${TARGET}" >&2
        echo "Supported targets: linux, linux_rt" >&2
        exit 2
        ;;
esac

case "${MODE}" in
    debug) CMAKE_BUILD_TYPE="Debug" ;;
    release) CMAKE_BUILD_TYPE="Release" ;;
    *)
        echo "Unsupported build mode: ${MODE}" >&2
        echo "Supported modes: debug, release" >&2
        exit 2
        ;;
esac

BUILD_DIR="${REPO_ROOT}/build/${TARGET}-${MODE}"

cmake \
    -S "${PROJECT_DIR}" \
    -B "${BUILD_DIR}" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
    -DSYSTEMID_TARGET="${TARGET}"

cmake --build "${BUILD_DIR}"

ctest \
    --test-dir "${BUILD_DIR}" \
    --output-on-failure
```

Examples:

```bash
src/SystemIdECMaster/tools/verify-host.sh
# -> build/linux-debug/

src/SystemIdECMaster/tools/verify-host.sh linux release
# -> build/linux-release/

src/SystemIdECMaster/tools/verify-host.sh linux_rt debug
# -> build/linux_rt-debug/

src/SystemIdECMaster/tools/verify-host.sh linux_rt release
# -> build/linux_rt-release/
```

The build workflow must never create generated artifacts under `src/SystemIdECMaster/`.

## H0.18 — Root `.gitignore`

Add at the repository root as appropriate:

```text
/build/
*.swp
```

Do not ignore:

```text
.devcontainer/
```

because it is part of the repository's reproducible development environment.

---

## H0.19 — Baseline verification and commit

From the repository root:

```bash
cd src/SystemIdECMaster
./tools/verify-host.sh

cd ../..
git status
git add .
git commit -m "Bootstrap SystemIdECMaster agentic development harness"
```

The working tree should then be clean.

---

## H0.20 — First controlled Codex task

Run Codex from the repository workspace and give it:

```text
Read the repository AGENTS.md and src/SystemIdECMaster/AGENTS.md.

This is a harness-validation task, not a production feature.

Work only on src/SystemIdECMaster.

Add a function named project_name() that returns the application name
as a std::string_view.

Move the literal currently printed by main() behind that function.
Add a test for project_name().

Keep the change minimal.
Do not add dependencies.

Run:

    src/SystemIdECMaster/tools/verify-host.sh

before reporting completion.
```

Review the diff manually.

The goal is to verify that Codex:

- discovers repository-wide rules;
- discovers project-specific rules;
- can inspect the complete monorepo;
- respects the current task scope;
- changes source and tests;
- executes deterministic verification;
- reports failures accurately.

---

## H0.21 — Failure/recovery experiment

Introduce a controlled acceptance failure and observe:

```text
change
  ↓
verify
  ↓
failure
  ↓
inspect deterministic evidence
  ↓
correct implementation
  ↓
verify
  ↓
pass
```

The objective is to verify the development loop, not the sophistication of the sample feature.

Record the outcome in:

```text
docs/SystemIdECMaster/experiments/
```

and summarize the result in the living dissertation.

---

## H0 Evidence to Preserve

At completion record:

- host Docker version;
- host VS Code version;
- Dev Containers extension version;
- development image/base;
- GCC/G++ version in container;
- CMake version in container;
- Ninja version in container;
- Python/pip versions;
- Node/npm versions;
- Codex CLI version;
- Codex extension version;
- relevant Codex sandbox settings without secrets;
- Git commit hash;
- output of `src/SystemIdECMaster/tools/verify-host.sh`;
- notes from the first controlled Codex task;
- notes from the failure/recovery experiment.

---

## H0 Exit Criterion

H0 is complete when:

```bash
src/SystemIdECMaster/tools/verify-host.sh
```

provides a deterministic host-side acceptance gate inside the single
repository Dev Container, and Codex has demonstrated correct use of that
gate during both a successful implementation and a failed-then-corrected
implementation.
