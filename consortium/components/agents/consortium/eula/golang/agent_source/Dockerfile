FROM golang:1.26.5-alpine AS builder

WORKDIR /agent_builder

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

# Pinned rather than @latest so a payload built today is reproducible tomorrow. Garble
# patches the Go toolchain, so its releases track specific Go versions: v0.16.0 supports
# the Go version pinned above. Bump both together.
RUN go install mvdan.cc/garble@v0.16.0

COPY . .
