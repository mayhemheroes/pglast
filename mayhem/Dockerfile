# syntax=docker/dockerfile:1.7
#
# Commit-image Dockerfile (SMALL form) — builds ON TOP of the org base image
# (ghcr.io/mayhemheroes/base). The base provides debian + clang/llvm + gcc/make + libFuzzer +
# Python 3 + the identities + the build-contract ENV. pglast (lelit/pglast) is a thin Python
# wrapper around libpg_query, the PostgreSQL parser exported as a native CPython C extension
# (pglast.parser). This image installs the Atheris harness engine and pglast (which compiles
# libpg_query + the C extension) into the base's system Python as root, then (as the non-root
# `mayhem` user) compiles the ELF launcher shims and runs the KAT oracle via build.sh / test.sh.
#
# Build (from the repo root):
#   DOCKER_BUILDKIT=1 docker build -f mayhem/Dockerfile \
#       --build-arg COMMIT=$(git rev-parse HEAD) \
#       [--build-arg SOURCE_DATE_EPOCH=$(date +%s)] \
#       -t pglast-commit:test .

FROM ghcr.io/mayhemheroes/base:20260621

ARG COMMIT
ARG REPO_URL
# SOURCE_DATE_EPOCH stays an ARG (available to build.sh); never bake it as ENV — an empty value
# breaks clang. build.sh unsets it when empty.
ARG SOURCE_DATE_EPOCH
# Declared for parity with the build contract; the shims build.sh compiles are pure exec() wrappers.
ARG SANITIZER_FLAGS

# Atheris (the libFuzzer harness engine — builds a native module against the base's clang/libFuzzer)
# and pglast (which compiles the bundled libpg_query C library + the pglast.parser C extension from
# its PyPI sdist) go into the base's SYSTEM Python. PEP 668 marks that interpreter externally-managed,
# so --break-system-packages. This is the (networked) install step that builds the native parser; it
# is pinned to v7.14 (the upstream `v7` mirror's HEAD) for reproducibility. build.sh deliberately does
# NOT pip-install, so its offline PATCH-tier re-run stays air-gapped. The C extension built here is the
# code the Atheris harness actually fuzzes.
USER root
RUN pip install --no-cache-dir --break-system-packages \
        atheris==3.1.0 \
        pglast==7.14

# Source enters from the build CONTEXT (the CI checkout): the FULL repo (incl. .git history)
# is copied to /mayhem as `mayhem`; build.sh builds in place.
WORKDIR /mayhem
COPY --chown=2000:2000 . /mayhem

USER mayhem

# Compile the ELF launcher shims (Mayhem needs an ELF target, not a .py).
RUN bash mayhem/build.sh

# Run pglast's KAT behavioral suite at build time; a failing suite fails the build.
RUN if [ -f mayhem/test.sh ]; then bash mayhem/test.sh; else echo "no mayhem/test.sh"; fi

LABEL org.opencontainers.image.source="${REPO_URL}" \
      org.opencontainers.image.revision="${COMMIT}" \
      rlenv.tier="commit" \
      rlenv.source_date_epoch="${SOURCE_DATE_EPOCH}" \
      rlenv.user="mayhem"

USER mayhem
WORKDIR /mayhem
