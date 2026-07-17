FROM golang:1.26.5-alpine AS builder

WORKDIR /agent_builder

COPY go.mod go.sum ./

RUN go mod download

COPY . .
