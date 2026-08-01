FROM golang:1.26.5-alpine AS builder

WORKDIR /agent_builder

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

RUN go install mvdan.cc/garble@latest

COPY . .
